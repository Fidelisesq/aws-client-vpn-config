# AWS Permissions Required for VPN Management Suite

This document explains the AWS IAM permissions required to execute the AWS Client VPN Management Suite project.

## 📋 Policy File: `aws-permissions-policy.json`

**Purpose:** Contains all AWS IAM permissions needed to deploy and manage AWS Client VPN infrastructure.

## 🔐 Permission Groups Explained

### 1. Client VPN Management (`ClientVPNManagement_CreateModifyDeleteVPNEndpoints`)
**Purpose:** Core VPN endpoint operations

| Permission | Used By | Purpose |
|------------|---------|---------|
| `ec2:CreateClientVpnEndpoint` | `deploy_vpn_cert.py` | Create new VPN endpoints |
| `ec2:DeleteClientVpnEndpoint` | Manual cleanup | Delete VPN endpoints |
| `ec2:ModifyClientVpnEndpoint` | `deploy_vpn_cert.py` | Update VPN endpoint settings |
| `ec2:DescribeClientVpnEndpoints` | Both scripts | Check VPN endpoint status |
| `ec2:DescribeClientVpnConnections` | `cert_manager.py` | View active user connections |
| `ec2:DescribeClientVpnAuthorizationRules` | `deploy_vpn_cert.py` | Check access rules |
| `ec2:DescribeClientVpnRoutes` | `deploy_vpn_cert.py` | Check routing configuration |
| `ec2:DescribeClientVpnTargetNetworks` | `deploy_vpn_cert.py` | Check network associations |
| `ec2:AssociateClientVpnTargetNetwork` | `deploy_vpn_cert.py` | Connect VPN to subnets |
| `ec2:DisassociateClientVpnTargetNetwork` | Manual cleanup | Disconnect VPN from subnets |
| `ec2:AuthorizeClientVpnIngress` | `deploy_vpn_cert.py` | Allow VPN access to networks |
| `ec2:RevokeClientVpnIngress` | Emergency procedures | Revoke VPN access |
| `ec2:CreateClientVpnRoute` | `deploy_vpn_cert.py` | Create VPN routes |
| `ec2:DeleteClientVpnRoute` | Manual cleanup | Delete VPN routes |
| `ec2:ExportClientVpnClientConfiguration` | `cert_manager.py` | Generate .ovpn files |
| `ec2:TerminateClientVpnConnections` | `cert_manager.py` | Force disconnect users |
| `ec2:ImportClientVpnClientCertificateRevocationList` | `cert_manager.py` | Update certificate revocation list |

### 2. VPC and Network Access (`VPCAndNetworkAccess_ReadVPCSubnetInfo`)
**Purpose:** Read existing VPC and subnet information

| Permission | Used By | Purpose |
|------------|---------|---------|
| `ec2:DescribeVpcs` | `deploy_vpn_cert.py` | Get VPC CIDR blocks |
| `ec2:DescribeVpcAttribute` | `deploy_vpn_cert.py` | Get VPC attributes |
| `ec2:DescribeSubnets` | `deploy_vpn_cert.py` | Validate subnet IDs |

### 3. Certificate Management (`CertificateManagement_ACMOperations`)
**Purpose:** Manage SSL/TLS certificates via AWS Certificate Manager

| Permission | Used By | Purpose |
|------------|---------|---------|
| `acm:RequestCertificate` | `cert_manager.py` | Request new SSL certificates |
| `acm:ImportCertificate` | `deploy_vpn_cert.py` | Upload CA certificates |
| `acm:DeleteCertificate` | `cert_manager.py` | Delete certificates |
| `acm:DescribeCertificate` | Both scripts | Check certificate status |
| `acm:ListCertificates` | `cert_manager.py` | List all certificates |
| `acm:GetCertificate` | Both scripts | Download certificate content |

### 4. Route 53 Certificate Validation (`Route53CertificateValidation_DNSRecords`)
**Purpose:** Automatically validate SSL certificates via DNS

| Permission | Used By | Purpose |
|------------|---------|---------|
| `route53:GetChange` | ACM validation | Check DNS record status |
| `route53:ChangeResourceRecordSets` | ACM validation | Create validation DNS records |
| `route53:ListHostedZones` | ACM validation | Find correct DNS zone |
| `route53:ListResourceRecordSets` | ACM validation | Check existing DNS records |

**Note:** Only needed if using Route 53 for domain validation. Can be removed if using manual DNS validation.

### 5. S3 CRL Management (`S3CRLManagement_CertificateRevocationList`)
**Purpose:** Store and manage Certificate Revocation Lists

| Permission | Used By | Purpose |
|------------|---------|---------|
| `s3:CreateBucket` | `cert_manager.py` | Create CRL storage bucket |
| `s3:HeadBucket` | `cert_manager.py` | Check if bucket exists |
| `s3:PutObject` | `cert_manager.py` | Upload CRL files |
| `s3:PutObjectAcl` | `cert_manager.py` | Set CRL file permissions |
| `s3:GetObject` | `cert_manager.py` | Download CRL files |
| `s3:DeleteObject` | Manual cleanup | Delete old CRL files |
| `s3:ListBucket` | `cert_manager.py` | List CRL files |

**Bucket:** `vpn-cert-revocation-list` (auto-created)

### 6. STS Access (`STSAccess_GetAccountInfo`)
**Purpose:** Get AWS account information

| Permission | Used By | Purpose |
|------------|---------|---------|
| `sts:GetCallerIdentity` | `deploy_vpn_cert.py` | Get AWS account ID for ARNs |

## 🚀 How to Apply These Permissions

### Option 1: Create IAM Policy (Recommended)
```bash
# Create the policy
aws iam create-policy \
    --policy-name AWSClientVPNManagement \
    --policy-document file://aws-permissions-policy.json

# Attach to your user
aws iam attach-user-policy \
    --user-name YOUR-USERNAME \
    --policy-arn arn:aws:iam::ACCOUNT:policy/AWSClientVPNManagement
```

### Option 2: Attach to IAM Role
```bash
# Attach to an existing role
aws iam attach-role-policy \
    --role-name YOUR-ROLE-NAME \
    --policy-arn arn:aws:iam::ACCOUNT:policy/AWSClientVPNManagement
```

## 🔒 Security Considerations

### Least Privilege Principle
- These permissions are scoped to the minimum required for the project
- S3 permissions are limited to the specific CRL bucket
- No permissions for other AWS services not used by the project

### Resource Restrictions
- S3 permissions are restricted to `vpn-cert-revocation-list` bucket only
- All other permissions use `"Resource": "*"` as required by AWS services

### Optional Permissions
- **Route 53 permissions** can be removed if not using automatic DNS validation
- **Delete permissions** can be removed if you don't plan to clean up resources

## ⚠️ Troubleshooting Permission Issues

### Common Error Messages:
- **"AccessDenied"** → Missing required permission
- **"InvalidClientVpnEndpointId.NotFound"** → Need `ec2:DescribeClientVpnEndpoints`
- **"UnauthorizedOperation"** → Check the specific permission mentioned in error

### Testing Permissions:
```bash
# Test basic access
aws sts get-caller-identity

# Test VPN permissions
aws ec2 describe-client-vpn-endpoints --region us-east-2

# Test ACM permissions
aws acm list-certificates --region us-east-2
```

## 📚 Related Documentation
- [AWS Client VPN API Reference](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/OperationList-query-clientvpn.html)
- [AWS Certificate Manager API Reference](https://docs.aws.amazon.com/acm/latest/APIReference/)
- [IAM Policy Examples](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_examples.html)