#!/usr/bin/env python3
"""
AWS Client VPN Deployment with Certificate Authentication
Creates server cert via ACM and client cert via OpenSSL
"""

import boto3
import json
import time
import argparse
import subprocess
import os
import sys
from botocore.exceptions import ClientError

class VPNCertDeployer:
    def __init__(self, region='us-east-2'):
        self.region = region
        self.ec2 = boto3.client('ec2', region_name=region)
        self.acm = boto3.client('acm', region_name=region)
        self.sts = boto3.client('sts')
        
    def get_account_id(self):
        """Get AWS account ID"""
        return self.sts.get_caller_identity()['Account']
    
    def create_server_certificate(self, domain):
        """Create server certificate via ACM"""
        try:
            # Check if certificate already exists
            existing_certs = self.acm.list_certificates()
            for cert in existing_certs['CertificateSummaryList']:
                if cert['DomainName'] == domain and cert['Status'] in ['ISSUED', 'PENDING_VALIDATION']:
                    print(f"✅ Using existing server certificate: {cert['CertificateArn']}")
                    return cert['CertificateArn']
            
            # Create new certificate
            response = self.acm.request_certificate(
                DomainName=domain,
                ValidationMethod='DNS'
            )
            cert_arn = response['CertificateArn']
            print(f"✅ Server certificate requested: {cert_arn}")
            print(f"⚠️  Validate certificate in ACM console before proceeding")
            return cert_arn
            
        except ClientError as e:
            print(f"❌ Error creating server certificate: {e}")
            return None
    
    def create_ca_certificate(self):
        """Create CA certificate only (client certs handled by cert_manager.py)"""
        try:
            os.makedirs('certs', exist_ok=True)
            
            if os.path.exists('certs/ca.crt') and os.path.exists('certs/ca.key'):
                print("✅ Using existing CA certificate")
                return True
            
            # Generate CA private key and certificate
            subprocess.run(['openssl', 'genrsa', '-out', 'certs/ca.key', '2048'], check=True)
            subprocess.run([
                'openssl', 'req', '-new', '-x509', '-days', '3650', '-key', 'certs/ca.key',
                '-out', 'certs/ca.crt', '-subj', '/C=US/ST=VA/L=Arlington/O=VPN/CN=VPN-CA'
            ], check=True)
            print("✅ CA certificate created")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error creating CA certificate: {e}")
            return False
    
    def upload_client_ca_to_acm(self):
        """Upload client CA certificate to ACM"""
        try:
            # Read CA certificate
            with open('certs/ca.crt', 'r') as f:
                ca_cert = f.read()
            
            # Check if CA certificate already exists in ACM
            existing_certs = self.acm.list_certificates()
            for cert in existing_certs['CertificateSummaryList']:
                if cert['DomainName'] == 'VPN-CA':
                    print(f"✅ Using existing client CA certificate: {cert['CertificateArn']}")
                    return cert['CertificateArn']
            
            # Upload new CA certificate to ACM
            with open('certs/ca.key', 'r') as f:
                ca_key = f.read()
            
            response = self.acm.import_certificate(
                Certificate=ca_cert,
                PrivateKey=ca_key
            )
            
            ca_cert_arn = response['CertificateArn']
            print(f"✅ Client CA certificate uploaded: {ca_cert_arn}")
            return ca_cert_arn
            
        except Exception as e:
            print(f"❌ Error uploading client CA: {e}")
            return None
    
    def create_vpn_endpoint(self, server_cert_arn, client_ca_arn, vpc_id, subnet_id, split_tunnel=True):
        """Create Client VPN endpoint"""
        try:
            # Get VPC CIDR
            vpc_response = self.ec2.describe_vpcs(VpcIds=[vpc_id])
            vpc_cidr = vpc_response['Vpcs'][0]['CidrBlock']
            
            # Check if VPN endpoint already exists
            existing_endpoints = self.ec2.describe_client_vpn_endpoints()
            for endpoint in existing_endpoints['ClientVpnEndpoints']:
                if endpoint['ServerCertificateArn'] == server_cert_arn:
                    vpn_endpoint_id = endpoint['ClientVpnEndpointId']
                    print(f"✅ Using existing VPN endpoint: {vpn_endpoint_id}")
                    
                    print("✅ Target network already associated")
                    
                    return vpn_endpoint_id, vpc_cidr
            
            # Create new VPN endpoint
            response = self.ec2.create_client_vpn_endpoint(
                ClientCidrBlock='192.168.0.0/16',
                ServerCertificateArn=server_cert_arn,
                AuthenticationOptions=[{
                    'Type': 'certificate-authentication',
                    'MutualAuthentication': {
                        'ClientRootCertificateChainArn': client_ca_arn
                    }
                }],
                ConnectionLogOptions={'Enabled': False},
                DnsServers=['8.8.8.8', '8.8.4.4']
            )
            
            vpn_endpoint_id = response['ClientVpnEndpointId']
            print(f"✅ VPN endpoint created: {vpn_endpoint_id}")
            
            # Associate target network
            self.ec2.associate_client_vpn_target_network(
                ClientVpnEndpointId=vpn_endpoint_id,
                SubnetId=subnet_id
            )
            print("✅ Target network associated")
            
            # Configure authorization rules and routes (idempotent)
            self._configure_vpn_access(vpn_endpoint_id, vpc_cidr, subnet_id, split_tunnel)
            
            return vpn_endpoint_id, vpc_cidr
            
        except ClientError as e:
            print(f"❌ Error creating VPN endpoint: {e}")
            return None, None
    
    def _configure_vpn_access(self, vpn_endpoint_id, vpc_cidr, subnet_id, split_tunnel):
        """Configure authorization rules and routes (idempotent)"""
        try:
            # Get existing authorization rules
            existing_auth_rules = self.ec2.describe_client_vpn_authorization_rules(
                ClientVpnEndpointId=vpn_endpoint_id
            )
            
            # Get existing routes
            existing_routes = self.ec2.describe_client_vpn_routes(
                ClientVpnEndpointId=vpn_endpoint_id
            )
            
            if split_tunnel:
                # Split tunneling: VPC traffic only
                
                # Check if VPC authorization rule exists
                vpc_auth_exists = any(
                    rule['DestinationCidr'] == vpc_cidr and rule['Status']['Code'] in ['active', 'authorizing']
                    for rule in existing_auth_rules['AuthorizationRules']
                )
                
                if not vpc_auth_exists:
                    self.ec2.authorize_client_vpn_ingress(
                        ClientVpnEndpointId=vpn_endpoint_id,
                        TargetNetworkCidr=vpc_cidr,
                        AuthorizeAllGroups=True
                    )
                    print("✅ VPC access authorized")
                else:
                    print("✅ VPC access already authorized")
                
                # Check if VPC route exists
                vpc_route_exists = any(
                    route['DestinationCidr'] == vpc_cidr and route['Status']['Code'] in ['active', 'creating']
                    for route in existing_routes['Routes']
                )
                
                if not vpc_route_exists:
                    self.ec2.create_client_vpn_route(
                        ClientVpnEndpointId=vpn_endpoint_id,
                        DestinationCidrBlock=vpc_cidr,
                        TargetVpcSubnetId=subnet_id
                    )
                    print("✅ VPC route added (split tunneling enabled)")
                else:
                    print("✅ VPC route already exists")
                
                print("ℹ️  Internet traffic goes direct, only VPC traffic through VPN")
                
            else:
                # Full tunneling: All traffic through VPN
                
                # Check if internet authorization rule exists
                internet_auth_exists = any(
                    rule['DestinationCidr'] == '0.0.0.0/0' and rule['Status']['Code'] in ['active', 'authorizing']
                    for rule in existing_auth_rules['AuthorizationRules']
                )
                
                if not internet_auth_exists:
                    self.ec2.authorize_client_vpn_ingress(
                        ClientVpnEndpointId=vpn_endpoint_id,
                        TargetNetworkCidr='0.0.0.0/0',
                        AuthorizeAllGroups=True
                    )
                    print("✅ Internet access authorized")
                else:
                    print("✅ Internet access already authorized")
                
                # Check if VPC authorization rule exists
                vpc_auth_exists = any(
                    rule['DestinationCidr'] == vpc_cidr and rule['Status']['Code'] in ['active', 'authorizing']
                    for rule in existing_auth_rules['AuthorizationRules']
                )
                
                if not vpc_auth_exists:
                    self.ec2.authorize_client_vpn_ingress(
                        ClientVpnEndpointId=vpn_endpoint_id,
                        TargetNetworkCidr=vpc_cidr,
                        AuthorizeAllGroups=True
                    )
                    print("✅ VPC access authorized")
                else:
                    print("✅ VPC access already authorized")
                
                # Check if internet route exists
                internet_route_exists = any(
                    route['DestinationCidr'] == '0.0.0.0/0' and route['Status']['Code'] in ['active', 'creating']
                    for route in existing_routes['Routes']
                )
                
                if not internet_route_exists:
                    self.ec2.create_client_vpn_route(
                        ClientVpnEndpointId=vpn_endpoint_id,
                        DestinationCidrBlock='0.0.0.0/0',
                        TargetVpcSubnetId=subnet_id
                    )
                    print("✅ Internet route added")
                else:
                    print("✅ Internet route already exists")
                
                # Check if VPC route exists
                vpc_route_exists = any(
                    route['DestinationCidr'] == vpc_cidr and route['Status']['Code'] in ['active', 'creating']
                    for route in existing_routes['Routes']
                )
                
                if not vpc_route_exists:
                    self.ec2.create_client_vpn_route(
                        ClientVpnEndpointId=vpn_endpoint_id,
                        DestinationCidrBlock=vpc_cidr,
                        TargetVpcSubnetId=subnet_id
                    )
                    print("✅ VPC route added (full tunneling enabled)")
                else:
                    print("✅ VPC route already exists")
                
                print("ℹ️  All traffic goes through VPN")
                
        except ClientError as e:
            if 'InvalidClientVpnDuplicateAuthorizationRule' in str(e) or 'InvalidClientVpnDuplicateRoute' in str(e):
                print("✅ Rules/routes already configured")
            else:
                print(f"❌ Error configuring VPN access: {e}")
    

    
    def deploy(self, domain, vpc_id, subnet_id, split_tunnel=True):
        """Complete VPN deployment"""
        print("🚀 Deploying AWS Client VPN with certificate authentication...")
        print(f"Domain: {domain}")
        print(f"VPC: {vpc_id}")
        print(f"Subnet: {subnet_id}")
        print(f"Split Tunneling: {'Enabled' if split_tunnel else 'Disabled'}")
        print("-" * 50)
        
        # Step 1: Create server certificate
        print("\n1. Creating server certificate...")
        server_cert_arn = self.create_server_certificate(domain)
        if not server_cert_arn:
            return False
        
        # Step 2: Create CA certificate
        print("\n2. Creating CA certificate...")
        if not self.create_ca_certificate():
            return False
        
        # Step 3: Upload client CA to ACM
        print("\n3. Uploading client CA certificate...")
        client_ca_arn = self.upload_client_ca_to_acm()
        if not client_ca_arn:
            return False
        
        # Step 4: Create VPN endpoint
        print("\n4. Creating VPN endpoint...")
        vpn_endpoint_id, vpc_cidr = self.create_vpn_endpoint(
            server_cert_arn, client_ca_arn, vpc_id, subnet_id, split_tunnel
        )
        if not vpn_endpoint_id:
            return False
        
        # Step 5: Save deployment info
        deployment_info = {
            'vpc_id': vpc_id,
            'subnet_id': subnet_id,
            'vpc_cidr': vpc_cidr,
            'vpn_endpoint_id': vpn_endpoint_id,
            'server_certificate_arn': server_cert_arn,
            'client_ca_certificate_arn': client_ca_arn,
            'region': self.region,
            'auth_type': 'certificate'
        }
        
        with open('vpn_deployment_info.json', 'w') as f:
            json.dump(deployment_info, f, indent=2)
        
        print("\n" + "="*50)
        print("🎉 VPN DEPLOYMENT COMPLETED!")
        print("="*50)
        print(f"VPN Endpoint ID: {vpn_endpoint_id}")
        print(f"CA Certificate: certs/ca.crt")
        print(f"Deployment Info: vpn_deployment_info.json")
        print("\n📋 Next Steps:")
        print("1. Validate server certificate in ACM console")
        print("2. Create users: python cert_manager.py add-user --vpn-endpoint {vpn_endpoint_id} --client-name username")
        print("3. Distribute .ovpn files from vpn_user_config/ to users")
        
        return True

def main():
    parser = argparse.ArgumentParser(description='Deploy AWS Client VPN with Certificate Authentication')
    parser.add_argument('--domain', required=True, help='Domain for server certificate')
    parser.add_argument('--vpc-id', required=True, help='VPC ID')
    parser.add_argument('--subnet-id', required=True, help='Subnet ID')
    parser.add_argument('--region', default='us-east-2', help='AWS region')
    parser.add_argument('--full-tunnel', action='store_true', help='Enable full tunneling (all traffic through VPN)')
    
    args = parser.parse_args()
    
    # Split tunneling is default, full tunneling is optional
    split_tunnel = not args.full_tunnel
    
    deployer = VPNCertDeployer(region=args.region)
    success = deployer.deploy(args.domain, args.vpc_id, args.subnet_id, split_tunnel)
    
    if not success:
        sys.exit(1)

if __name__ == '__main__':
    main()