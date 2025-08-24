#!/usr/bin/env python3
"""
Certificate Management for AWS Client VPN
Manages server and client certificates
"""

import boto3
import subprocess
import os
import argparse
import json
import ipaddress
from botocore.exceptions import ClientError

class CertificateManager:
    def __init__(self, region='us-east-2'):
        self.region = region
        self.acm = boto3.client('acm', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.ec2 = boto3.client('ec2', region_name=region)
        self.bucket_name = 'vpn-cert-revocation-list'
    
    def create_client_certificates(self, common_name='client'):
        """Create client certificates using OpenSSL"""
        try:
            print(f"Creating client certificates for: {common_name}")
            
            # Create certificates directory
            os.makedirs('certs', exist_ok=True)
            
            # Ensure CA certificate exists (should be created by deploy_vpn_cert.py)
            if not os.path.exists('certs/ca.crt') or not os.path.exists('certs/ca.key'):
                print("Error: CA certificate not found. Run deploy_vpn_cert.py first.")
                return False
            
            # Generate client private key
            client_key_file = f'certs/{common_name}.key'
            subprocess.run([
                'openssl', 'genrsa', '-out', client_key_file, '2048'
            ], check=True)
            
            # Generate client certificate request
            client_csr_file = f'certs/{common_name}.csr'
            subprocess.run([
                'openssl', 'req', '-new', '-key', client_key_file,
                '-out', client_csr_file, '-subj', f'/C=US/ST=VA/L=Arlington/O=VPN/CN={common_name}'
            ], check=True)
            
            # Sign client certificate with CA
            client_crt_file = f'certs/{common_name}.crt'
            subprocess.run([
                'openssl', 'x509', '-req', '-days', '3650', '-in', client_csr_file,
                '-CA', 'certs/ca.crt', '-CAkey', 'certs/ca.key', '-CAcreateserial',
                '-out', client_crt_file
            ], check=True)
            
            # Clean up CSR file
            os.remove(client_csr_file)
            
            print(f"Client certificate created: {client_crt_file}")
            return True
            
        except Exception as e:
            print(f"Error creating client certificates: {e}")
            return False
    
    def list_certificates(self):
        """List certificates in ACM"""
        try:
            response = self.acm.list_certificates()
            
            if not response['CertificateSummaryList']:
                print("No certificates found in ACM")
                return
            
            print("Certificates in ACM:")
            print("-" * 80)
            for cert in response['CertificateSummaryList']:
                print(f"Domain: {cert['DomainName']}")
                print(f"ARN: {cert['CertificateArn']}")
                print(f"Status: {cert['Status']}")
                print("-" * 80)
                
        except ClientError as e:
            print(f"Error listing certificates: {e}")
    
    def delete_certificate(self, cert_arn):
        """Delete certificate from ACM"""
        try:
            self.acm.delete_certificate(CertificateArn=cert_arn)
            print(f"Certificate deleted: {cert_arn}")
            return True
            
        except ClientError as e:
            print(f"Error deleting certificate: {e}")
            return False
    
    def create_server_certificate(self, domain):
        """Request server certificate via ACM"""
        try:
            response = self.acm.request_certificate(
                DomainName=domain,
                ValidationMethod='DNS'
            )
            
            cert_arn = response['CertificateArn']
            print(f"Server certificate requested: {cert_arn}")
            print(f"Validate certificate in ACM console")
            return cert_arn
            
        except ClientError as e:
            print(f"Error creating server certificate: {e}")
            return None
    
    def generate_ovpn_config(self, vpn_endpoint_id, client_name='client'):
        """Generate .ovpn file with embedded certificates"""
        try:
            # Create vpn_user_config directory
            os.makedirs('vpn_user_config', exist_ok=True)
            
            # Export base configuration
            response = self.ec2.export_client_vpn_client_configuration(
                ClientVpnEndpointId=vpn_endpoint_id
            )
            
            config_content = response['ClientConfiguration']
            
            # Read client certificate and key
            client_crt_file = f'certs/{client_name}.crt'
            client_key_file = f'certs/{client_name}.key'
            
            with open(client_crt_file, 'r') as f:
                client_cert = f.read()
            
            with open(client_key_file, 'r') as f:
                client_key = f.read()
            
            # Get VPC CIDR and calculate DNS resolver
            vpc_cidr = self._get_vpc_cidr()
            vpc_dns = self._calculate_vpc_dns(vpc_cidr)
            network = ipaddress.IPv4Network(vpc_cidr, strict=False)
            
            # Add split tunneling configuration
            config_content += "\n\n# Split tunneling - only VPC traffic through VPN\n"
            config_content += "route-nopull\n"
            config_content += f"route {network.network_address} {network.netmask}\n"
            config_content += f"\ndhcp-option DNS {vpc_dns}\n"
            
            # Embed certificates in config
            config_content += f"\n# Client certificate for {client_name}\n"
            config_content += "<cert>\n"
            config_content += client_cert
            config_content += "</cert>\n\n"
            config_content += "<key>\n"
            config_content += client_key
            config_content += "</key>\n"
            
            # Write to vpn_user_config directory
            ovpn_file = f'vpn_user_config/{client_name}-vpn.ovpn'
            with open(ovpn_file, 'w') as f:
                f.write(config_content)
            
            print(f"Client configuration generated: {ovpn_file}")
            return ovpn_file
            
        except Exception as e:
            print(f"Error generating client config: {e}")
            return None
    
    def remove_user(self, client_name):
        """Remove user certificates and configuration files"""
        try:
            files_to_remove = [
                f'certs/{client_name}.crt',
                f'certs/{client_name}.key',
                f'vpn_user_config/{client_name}-vpn.ovpn'
            ]
            
            removed_files = []
            for file_path in files_to_remove:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    removed_files.append(file_path)
            
            if removed_files:
                print(f"User {client_name} removed successfully!")
                print("Removed files:")
                for file_path in removed_files:
                    print(f"  - {file_path}")
            else:
                print(f"No files found for user: {client_name}")
            
            return True
            
        except Exception as e:
            print(f"Error removing user {client_name}: {e}")
            return False
    
    def ban_user(self, client_name, vpn_endpoint_id):
        """Ban user: revoke certificate + force disconnect active sessions"""
        try:
            print(f"Banning user: {client_name}")
            
            # Step 1: Revoke certificate
            if not self.revoke_user_certificate(client_name, vpn_endpoint_id):
                return False
            
            # Step 2: Force disconnect active sessions
            self._force_disconnect_user(client_name, vpn_endpoint_id)
            
            print(f"User {client_name} banned successfully!")
            return True
            
        except Exception as e:
            print(f"Error banning user {client_name}: {e}")
            return False
    
    def _force_disconnect_user(self, client_name, vpn_endpoint_id):
        """Force disconnect all active sessions for a user"""
        try:
            # Get active connections for this user
            response = self.ec2.describe_client_vpn_connections(
                ClientVpnEndpointId=vpn_endpoint_id
            )
            
            # Filter for active connections with matching common name
            active_connections = [
                conn for conn in response.get('Connections', [])
                if conn.get('Status', {}).get('Code') == 'active' and 
                   conn.get('CommonName') == client_name
            ]
            
            if not active_connections:
                print(f"No active connections found for user: {client_name}")
                return
            
            # Terminate all active connections
            for conn in active_connections:
                connection_id = conn['ConnectionId']
                self.ec2.terminate_client_vpn_connections(
                    ClientVpnEndpointId=vpn_endpoint_id,
                    ConnectionId=connection_id
                )
                print(f"Terminated connection: {connection_id}")
            
            print(f"Disconnected {len(active_connections)} active session(s) for {client_name}")
            
        except Exception as e:
            print(f"Error force disconnecting user {client_name}: {e}")
    
    def revoke_user_certificate(self, client_name, vpn_endpoint_id=None):
        """Revoke user certificate using CRL"""
        try:
            client_crt_file = f'certs/{client_name}.crt'
            
            if not os.path.exists(client_crt_file):
                print(f"Certificate file not found: {client_crt_file}")
                return False
            
            # Create CA database if it doesn't exist
            self._setup_ca_database()
            
            # Revoke the certificate
            subprocess.run([
                'openssl', 'ca', '-revoke', client_crt_file,
                '-keyfile', 'certs/ca.key', '-cert', 'certs/ca.crt',
                '-config', 'certs/openssl.conf'
            ], check=True)
            
            print(f"Certificate revoked: {client_name}")
            
            # Generate and upload CRL
            if self._generate_and_upload_crl():
                # Update VPN endpoint with CRL
                if vpn_endpoint_id:
                    self._update_vpn_endpoint_crl(vpn_endpoint_id)
                
                print(f"User {client_name} access revoked successfully!")
                return True
            
            return False
            
        except Exception as e:
            print(f"Error revoking certificate: {e}")
            return False
    
    def _setup_ca_database(self):
        """Setup OpenSSL CA database for CRL"""
        ca_dir = 'certs'
        
        # Create index.txt if it doesn't exist
        index_file = f'{ca_dir}/index.txt'
        if not os.path.exists(index_file):
            open(index_file, 'w').close()
        
        # Create serial file if it doesn't exist
        serial_file = f'{ca_dir}/serial'
        if not os.path.exists(serial_file):
            with open(serial_file, 'w') as f:
                f.write('01\n')
        
        # Create crlnumber file if it doesn't exist
        crlnumber_file = f'{ca_dir}/crlnumber'
        if not os.path.exists(crlnumber_file):
            with open(crlnumber_file, 'w') as f:
                f.write('01\n')
        
        # Create OpenSSL config file
        config_content = f"""[ ca ]
default_ca = CA_default

[ CA_default ]
dir = {ca_dir}
certs = $dir
crl_dir = $dir
database = $dir/index.txt
new_certs_dir = $dir
certificate = $dir/ca.crt
serial = $dir/serial
crlnumber = $dir/crlnumber
crl = $dir/crl.pem
private_key = $dir/ca.key
default_days = 3650
default_crl_days = 30
default_md = sha256
preserve = no
policy = policy_anything

[ policy_anything ]
countryName = optional
stateOrProvinceName = optional
localityName = optional
organizationName = optional
organizationalUnitName = optional
commonName = supplied
emailAddress = optional
"""
        
        with open(f'{ca_dir}/openssl.conf', 'w') as f:
            f.write(config_content)
    
    def _generate_and_upload_crl(self):
        """Generate CRL and upload to S3"""
        try:
            # Generate CRL
            subprocess.run([
                'openssl', 'ca', '-gencrl',
                '-keyfile', 'certs/ca.key', '-cert', 'certs/ca.crt',
                '-out', 'certs/crl.pem',
                '-config', 'certs/openssl.conf'
            ], check=True)
            
            print("CRL generated successfully")
            
            # Create S3 bucket if it doesn't exist
            self._create_s3_bucket()
            
            # Upload CRL to S3
            self.s3.upload_file(
                'certs/crl.pem',
                self.bucket_name,
                'vpn-crl.pem'
            )
            
            print(f"CRL uploaded to S3: s3://{self.bucket_name}/vpn-crl.pem")
            return True
            
        except Exception as e:
            print(f"Error generating/uploading CRL: {e}")
            return False
    
    def _create_s3_bucket(self):
        """Create S3 bucket for CRL if it doesn't exist"""
        try:
            # Check if bucket exists
            self.s3.head_bucket(Bucket=self.bucket_name)
        except:
            # Create bucket
            if self.region == 'us-east-1':
                self.s3.create_bucket(Bucket=self.bucket_name)
            else:
                self.s3.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            print(f"S3 bucket created: {self.bucket_name}")
    
    def _update_vpn_endpoint_crl(self, vpn_endpoint_id):
        """Update VPN endpoint with CRL content"""
        try:
            # Read CRL content
            with open('certs/crl.pem', 'r') as f:
                crl_content = f.read()
            
            # Import CRL to VPN endpoint
            self.ec2.import_client_vpn_client_certificate_revocation_list(
                ClientVpnEndpointId=vpn_endpoint_id,
                CertificateRevocationList=crl_content
            )
            
            print(f"VPN endpoint updated with CRL content")
            
        except Exception as e:
            print(f"Error updating VPN endpoint with CRL: {e}")
    

    def _get_vpc_cidr(self):
        """Read VPC CIDR from deployment info"""
        try:
            with open('vpn_deployment_info.json', 'r') as f:
                info = json.load(f)
                return info['vpc_cidr']
        except Exception:
            return '10.0.0.0/16'  # fallback
    
    def _calculate_vpc_dns(self, vpc_cidr):
        """Calculate VPC DNS resolver (base + 2)"""
        network = ipaddress.IPv4Network(vpc_cidr, strict=False)
        dns_ip = network.network_address + 2
        return str(dns_ip)

def main():
    parser = argparse.ArgumentParser(description='Certificate Management for AWS Client VPN')
    parser.add_argument('action', choices=['create-client', 'create-server', 'list', 'delete', 'generate-ovpn', 'add-user', 'remove-user', 'revoke-user', 'ban-user'])
    parser.add_argument('--domain', help='Domain for server certificate')
    parser.add_argument('--client-name', default='client', help='Client certificate name')
    parser.add_argument('--cert-arn', help='Certificate ARN to delete')
    parser.add_argument('--vpn-endpoint', help='VPN endpoint ID for config generation')
    parser.add_argument('--region', default='us-east-2', help='AWS region')
    
    args = parser.parse_args()
    
    cert_manager = CertificateManager(region=args.region)
    
    if args.action == 'create-client':
        cert_manager.create_client_certificates(args.client_name)
    elif args.action == 'create-server':
        if not args.domain:
            print("--domain required for server certificate")
            return
        cert_manager.create_server_certificate(args.domain)
    elif args.action == 'list':
        cert_manager.list_certificates()
    elif args.action == 'delete':
        if not args.cert_arn:
            print("--cert-arn required for delete")
            return
        cert_manager.delete_certificate(args.cert_arn)
    elif args.action == 'generate-ovpn':
        if not args.vpn_endpoint:
            print("--vpn-endpoint required for config generation")
            return
        cert_manager.generate_ovpn_config(args.vpn_endpoint, args.client_name)
    elif args.action == 'add-user':
        if not args.vpn_endpoint or not args.client_name:
            print("--vpn-endpoint and --client-name required for add-user")
            return
        print(f"Adding new VPN user: {args.client_name}")
        if cert_manager.create_client_certificates(args.client_name):
            if cert_manager.generate_ovpn_config(args.vpn_endpoint, args.client_name):
                print(f"User {args.client_name} added successfully!")
                print(f"Configuration file: vpn_user_config/{args.client_name}-vpn.ovpn")
            else:
                print(f"Failed to generate config for user {args.client_name}")
        else:
            print(f"Failed to add user {args.client_name}")
    elif args.action == 'remove-user':
        if not args.client_name:
            print("--client-name required for remove-user")
            return
        cert_manager.remove_user(args.client_name)
    elif args.action == 'revoke-user':
        if not args.client_name:
            print("--client-name required for revoke-user")
            return
        cert_manager.revoke_user_certificate(args.client_name, args.vpn_endpoint)
    elif args.action == 'ban-user':
        if not args.client_name or not args.vpn_endpoint:
            print("--client-name and --vpn-endpoint required for ban-user")
            return
        cert_manager.ban_user(args.client_name, args.vpn_endpoint)

if __name__ == '__main__':
    main()