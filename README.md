# AWS Client VPN Management Suite

Complete solution for AWS Client VPN deployment and management using existing infrastructure.

## 🚀 Quick Start

**Deploy VPN in 5 minutes:**
```bash
# Install dependencies
pip install -r requirements.txt

# Get your VPC/Subnet IDs (us-east-2)
aws ec2 describe-vpcs --region us-east-2 --query 'Vpcs[*].[VpcId,CidrBlock]' --output table

# Deploy VPN with certificate authentication
python deploy_vpn_cert.py --domain "fozdigitalz.com" --vpc-id "vpc-09a94e086232207f4" --subnet-id "subnet-0459cd356e8cda83d"

# Add new VPN users (creates certificate + .ovpn file)
python cert_manager.py add-user --vpn-endpoint [ENDPOINT-ID] --client-name john.doe
```

## 📁 Files Overview

**Core Scripts:**
- **`deploy_vpn_cert.py`** - Main VPN deployment script (certificate auth + split tunneling)
- **`cert_manager.py`** - Certificate management utility with CRL-based revocation

**Documentation:**
- **`README.md`** - This quick start guide
- **`DEPLOYMENT_GUIDE.md`** - Complete deployment guide
- **`VPN-ADMIN.md`** - Administration and user management guide
- **`CLIENT_VPN_CONNECTION_GUIDE.md`** - User connection instructions

**Configuration:**
- **`aws-permissions-policy.json`** - Required IAM permissions
- **`requirements.txt`** - Python dependencies

**Generated Files:**
- **`certs/`** - Certificate directory (auto-created)
- **`vpn_user_config/`** - User VPN configuration files (auto-created)
- **`certs/crl.pem`** - Certificate Revocation List
- **`vpn_user_config/[username]-vpn.ovpn`** - Individual user configurations
- **S3 Bucket:** `vpn-cert-revocation-list` - CRL storage (auto-created)

## Setup

### Git Clone Setup

If you cloned this project from Git:

```bash
# Clone the repository
git clone <repository-url>
cd aws-vpn-project

# Run setup script to create necessary directories
python setup.py

# Install dependencies
pip install -r requirements.txt

# Configure AWS credentials
aws configure
```

### Prerequisites
- AWS credentials configured
- Python 3.7+ installed
- OpenSSL installed and in PATH
- Existing VPC and Subnet
- Domain name for server certificate
- Required IAM permissions (see `aws-permissions-policy.json`)

### Installation
```bash
# Install Python dependencies
pip install -r requirements.txt

# Setup IAM permissions
aws iam create-policy --policy-name AWSClientVPNManagement --policy-document file://aws-permissions-policy.json
aws iam attach-user-policy --user-name YOUR-USERNAME --policy-arn arn:aws:iam::ACCOUNT:policy/AWSClientVPNManagement

# Verify AWS access
aws sts get-caller-identity

# Verify OpenSSL installation
openssl version
```

## Usage

### 🎯 Automated Deployment

```bash
# Deploy with split tunneling (default - recommended)
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

### 👥 User Management

```bash
# Add new VPN user (creates certificate + .ovpn file)
python cert_manager.py add-user --vpn-endpoint cvpn-endpoint-xxx --client-name john.doe

# Ban user (revoke certificate + force disconnect)
python cert_manager.py ban-user --vpn-endpoint cvpn-endpoint-xxx --client-name john.doe

# Remove local files (cleanup only)
python cert_manager.py remove-user --client-name john.doe

# List certificates
python cert_manager.py list
```

### 🔐 Certificate Management

```bash
# Create server certificate
python cert_manager.py create-server --domain "fozdigitalz.com"

# Create client certificate
python cert_manager.py create-client --client-name username

# List certificates
python cert_manager.py list

# Delete certificate
python cert_manager.py delete --cert-arn "arn:aws:acm:..."
```

## 📖 Documentation

- **Complete Setup**: See `DEPLOYMENT_GUIDE.md`
- **User Instructions**: See `CLIENT_VPN_CONNECTION_GUIDE.md`

## 🔧 Common Tasks

### Certificate Operations
```bash
# Create certificates for multiple users
python cert_manager.py create-client --client-name user1
python cert_manager.py create-client --client-name user2

# Generate individual .ovpn files
python cert_manager.py generate-ovpn --vpn-endpoint cvpn-endpoint-xxx --client-name user1
```

### Certificate Revocation (CRL)
```bash
# Ban user (revoke + force disconnect - immediate effect)
python cert_manager.py ban-user --vpn-endpoint cvpn-endpoint-xxx --client-name compromised.user

# Check CRL status
aws s3 ls s3://vpn-cert-revocation-list/

# View revoked certificates
openssl crl -in certs/crl.pem -text -noout
```



### Find Your Infrastructure
```bash
# List VPCs (us-east-2)
aws ec2 describe-vpcs --region us-east-2 --query 'Vpcs[*].[VpcId,CidrBlock,Tags[?Key==`Name`].Value|[0]]' --output table

# List Subnets (us-east-2)
aws ec2 describe-subnets --region us-east-2 --query 'Subnets[*].[SubnetId,VpcId,CidrBlock]' --output table
```

### Monitor VPN
```bash
# Check VPN status
aws ec2 describe-client-vpn-endpoints --region us-east-2

# View connection logs
aws logs describe-log-streams --log-group-name vpn-logs --region us-east-2
```

### Bulk User Operations
```bash
# Add multiple VPN users
for user in john jane bob; do
  python cert_manager.py add-user --vpn-endpoint cvpn-endpoint-xxx --client-name $user
done

# Ban multiple users
for user in john jane bob; do
  python cert_manager.py ban-user --vpn-endpoint cvpn-endpoint-xxx --client-name $user
done
```

## 🆘 Support

**Need Help?**
- Check `DEPLOYMENT_GUIDE.md` for complete setup instructions
- Review troubleshooting sections in documentation
- Verify AWS credentials and permissions

**Common Issues:**
- Certificate validation: Use Route 53 or manual DNS validation
- OpenSSL errors: Ensure OpenSSL is installed and in PATH
- Connection problems: Check security groups and routes
- Client certificate issues: Regenerate client certificates