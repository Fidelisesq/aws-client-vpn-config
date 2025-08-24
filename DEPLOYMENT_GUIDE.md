# AWS Client VPN - Deployment Guide

Complete deployment guide for AWS Client VPN with certificate authentication.

## Prerequisites

- AWS credentials configured
- Python 3.7+ installed
- OpenSSL installed and in PATH
- Domain name for server certificate
- Existing VPC and Subnet IDs
- Required IAM permissions (see `aws-permissions-policy.json`)

## Quick Deployment (5 Minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Verify OpenSSL installation
openssl version

# 3. Find your VPC and Subnet IDs
aws ec2 describe-vpcs --region us-east-2 --query 'Vpcs[*].[VpcId,CidrBlock,Tags[?Key==`Name`].Value|[0]]' --output table
aws ec2 describe-subnets --region us-east-2 --query 'Subnets[*].[SubnetId,VpcId,CidrBlock,AvailabilityZone]' --output table

# 4. Deploy VPN with split tunneling (recommended)
python deploy_vpn_cert.py \
    --domain "fozdigitalz.com" \
    --vpc-id "vpc-09a94e086232207f4" \
    --subnet-id "subnet-0459cd356e8cda83d"

# 5. Add new VPN users
python cert_manager.py add-user --vpn-endpoint [ENDPOINT-ID] --client-name john.doe

# 6. Distribute individual .ovpn files to users
```

## Manual Deployment (Step-by-Step)

### Step 1: Setup Environment

#### 1.1 Install Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# Verify AWS credentials
aws sts get-caller-identity

# Verify OpenSSL installation
openssl version
```

#### 1.2 Setup IAM Permissions
```bash
# Create IAM policy
aws iam create-policy --policy-name AWSClientVPNManagement --policy-document file://aws-permissions-policy.json

# Attach to your user
aws iam attach-user-policy --user-name YOUR-USERNAME --policy-arn arn:aws:iam::ACCOUNT:policy/AWSClientVPNManagement
```

#### 1.3 Get Existing Infrastructure IDs
```bash
# List your VPCs
aws ec2 describe-vpcs --region us-east-2 --query 'Vpcs[*].[VpcId,CidrBlock,Tags[?Key==`Name`].Value|[0]]' --output table

# List your subnets
aws ec2 describe-subnets --region us-east-2 --query 'Subnets[*].[SubnetId,VpcId,CidrBlock,AvailabilityZone]' --output table

# Note your VPC ID and Subnet ID for use below
```

### Step 2: Deploy VPN Infrastructure

#### 2.1 Automated Deployment (Recommended)
```bash
# Deploy with split tunneling (saves costs)
python deploy_vpn_cert.py \
    --domain "fozdigitalz.com" \
    --vpc-id "vpc-09a94e086232207f4" \
    --subnet-id "subnet-0459cd356e8cda83d"

# Deploy with full tunneling (all traffic through VPN)
python deploy_vpn_cert.py \
    --domain "fozdigitalz.com" \
    --vpc-id "vpc-09a94e086232207f4" \
    --subnet-id "subnet-0459cd356e8cda83d" \
    --full-tunnel
```

This script automatically:
- Creates server certificate via ACM
- Creates client CA certificate with OpenSSL
- Uploads client CA to ACM
- Creates VPN endpoint with certificate authentication
- Configures split tunneling (VPC traffic only)
- Generates client configuration with embedded certificates

#### 2.2 Certificate Validation
1. Go to AWS Certificate Manager console
2. Find your certificate for the domain
3. Click "Create records in Route 53" (if using Route 53)
4. Wait for validation to complete (Status: Issued)

### Step 3: User Management

#### 3.1 Add VPN Users
```bash
# Add single user (creates certificate + .ovpn file)
python cert_manager.py add-user --vpn-endpoint cvpn-endpoint-xxx --client-name john.doe

# Add multiple users
python cert_manager.py add-user --vpn-endpoint cvpn-endpoint-xxx --client-name jane.smith
python cert_manager.py add-user --vpn-endpoint cvpn-endpoint-xxx --client-name bob.wilson
```

#### 3.2 Remove VPN Users
```bash
# Ban user (revoke certificate + force disconnect)
python cert_manager.py ban-user --vpn-endpoint cvpn-endpoint-xxx --client-name john.doe

# Clean up local files (optional)
python cert_manager.py remove-user --client-name john.doe
```

#### 3.3 Certificate Management
```bash
# List all certificates in ACM
python cert_manager.py list

# Create server certificate (if needed)
python cert_manager.py create-server --domain "fozdigitalz.com"

# Delete certificate
python cert_manager.py delete --cert-arn "arn:aws:acm:..."
```

### Step 4: Testing and Monitoring

#### 4.1 Test VPN Connection
```bash
# Check VPN endpoint status
aws ec2 describe-client-vpn-endpoints --region us-east-2

# Test user connection
# 1. Distribute .ovpn file to user
# 2. User imports into OpenVPN client
# 3. User connects and tests access
```

#### 4.2 Monitor VPN Usage
```bash
# View active connections
aws ec2 describe-client-vpn-connections --region us-east-2

# Check VPN routes
aws ec2 describe-client-vpn-routes --client-vpn-endpoint-id cvpn-endpoint-xxx --region us-east-2

# List authorization rules
aws ec2 describe-client-vpn-authorization-rules --client-vpn-endpoint-id cvpn-endpoint-xxx --region us-east-2
```

## Important Values to Save

Create a file with these values for future reference:

```
VPC ID: vpc-09a94e086232207f4
Subnet ID: subnet-0459cd356e8cda83d
VPC CIDR: 10.0.0.0/16
VPN Endpoint ID: cvpn-endpoint-xxxxxxxxx
Server Certificate ARN: arn:aws:acm:us-east-2:ACCOUNT:certificate/CERT-ID
Client CA Certificate ARN: arn:aws:acm:us-east-2:ACCOUNT:certificate/CLIENT-CA-ID
Region: us-east-2
Authentication Type: certificate
Split Tunneling: enabled (default)
```

## Post-Deployment

Once deployment is complete, refer to:
- **VPN-ADMIN.md** - For ongoing administration and user management
- **CLIENT_VPN_CONNECTION_GUIDE.md** - For user connection instructions

## Security Checklist

- [ ] Certificate validated and issued
- [ ] VPN endpoint created successfully
- [ ] Authorization rules configured
- [ ] Users synced from IAM
- [ ] Client configuration distributed
- [ ] Connection logging enabled
- [ ] Test connection successful