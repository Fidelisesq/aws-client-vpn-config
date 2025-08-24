# AWS Client VPN - Administration Guide

Complete administration and management guide for ongoing VPN operations with certificate authentication.

## Certificate Manager Commands Reference

### User Certificate Management

#### Add New VPN User (One Command)
```bash
python cert_manager.py add-user --vpn-endpoint cvpn-endpoint-xxx --client-name john.doe
# Creates certificate AND .ovpn file in one step
```


#### Ban VPN User (Revoke + Force Disconnect)
```bash
python cert_manager.py ban-user --client-name john.doe --vpn-endpoint cvpn-endpoint-098fc14f568a1a989
# Revokes certificate AND force disconnects active sessions - immediate effect
```

#### Remove Local Files Only (No VPN Access Change)
```bash
python cert_manager.py remove-user --client-name john.doe
# ⚠️  WARNING: Only removes local files - user can still connect to VPN!
# Use ban-user first to actually revoke VPN access
```

#### Manual Steps (if needed)
```bash
# Create client certificate only (requires CA certificate from deployment)
python cert_manager.py create-client --client-name john.doe

# Generate .ovpn file only
python cert_manager.py generate-ovpn --vpn-endpoint cvpn-endpoint-xxx --client-name john.doe
```

#### Create Multiple Users
```bash
# Bulk user creation (simplified)
for user in john.doe jane.smith bob.wilson; do
  python cert_manager.py add-user --vpn-endpoint cvpn-endpoint-xxx --client-name $user
done
```

### Server Certificate Management

#### Create Server Certificate
```bash
python cert_manager.py create-server --domain "fozdigitalz.com"
# Requests new SSL certificate for VPN server via ACM
```

#### List All Certificates in ACM
```bash
python cert_manager.py list
# Shows all ACM certificates with domain, ARN, and status
```

#### Delete Certificate
```bash
python cert_manager.py delete --cert-arn "arn:aws:acm:us-east-2:account:certificate/cert-id"
# Permanently deletes specified certificate
```

### Certificate Files Management

#### View Certificate Files
```bash
# List certificate files
ls -la certs/

# View CA certificate
cat certs/ca.crt

# View user certificate
cat certs/john.doe.crt

# View Certificate Revocation List
cat certs/crl.pem

# Check CRL in S3
aws s3 ls s3://vpn-cert-revocation-list/
```

### Certificate Revocation List (CRL) Management

#### Manual CRL Operations
```bash
# View current CRL status
aws ec2 describe-client-vpn-endpoints \
    --client-vpn-endpoint-ids cvpn-endpoint-0e142c7c94634e649 \
    --region us-east-2 \
    --query 'ClientVpnEndpoints[0].ClientCertificateRevocationListUrl'

# Check S3 CRL bucket
aws s3 ls s3://vpn-cert-revocation-list/ --region us-east-2

# Download current CRL
aws s3 cp s3://vpn-cert-revocation-list/vpn-crl.pem ./current-crl.pem --region us-east-2

# View revoked certificates
openssl crl -in current-crl.pem -text -noout
```

## Ongoing Administration & Maintenance

### Daily Operations

#### Add New Employee
```bash
# Single command to create certificate and .ovpn file
python cert_manager.py add-user --vpn-endpoint cvpn-endpoint-xxx --client-name new.employee

# Send vpn_user_config/new.employee-vpn.ovpn file to employee
```

#### Remove Employee
```bash
# Ban user (revoke + force disconnect)
python cert_manager.py ban-user --client-name old.employee --vpn-endpoint cvpn-endpoint-0e142c7c94634e649

# Optional: Clean up local files
python cert_manager.py remove-user --client-name old.employee
```

#### Bulk User Management
```bash
# Create certificates and .ovpn files for multiple users
for user in user1 user2 user3; do
  python cert_manager.py add-user --vpn-endpoint cvpn-endpoint-xxx --client-name $user
done

# List all certificate files
ls -la certs/*.crt
ls -la *.ovpn
```

### Weekly Tasks

#### Monitor VPN Usage
```bash
# Check VPN status
aws ec2 describe-client-vpn-endpoints --region us-east-2

# View active connections
aws ec2 describe-client-vpn-connections --client-vpn-endpoint-id cvpn-endpoint-0e142c7c94634e649 --region us-east-2

# Check authorization rules
aws ec2 describe-client-vpn-authorization-rules --client-vpn-endpoint-id cvpn-endpoint-0e142c7c94634e649 --region us-east-2
```

#### Security Review
```bash
# Review certificate files
ls -la certs/

# Check certificate expiration
openssl x509 -in certs/ca.crt -text -noout | grep "Not After"

# List distributed .ovpn files
ls -la vpn_user_config/*.ovpn
```

### Monthly Tasks

#### Certificate Management
```bash
# Check certificate expiration
python cert_manager.py list

# Renew certificate (if needed)
python cert_manager.py create-server --domain "fozdigitalz.com"
```

#### Cost Monitoring
```bash
# Monitor VPN costs in AWS Cost Explorer
# Review connection hours and data transfer
# Optimize based on usage patterns
```

### Quarterly Tasks

#### Access Review
- Review all VPN users for continued business need
- Remove access for inactive employees
- Update user groups based on organizational changes

#### Security Audit
- Review VPN logs for suspicious activity
- Verify certificate rotation schedule
- Test disaster recovery procedures
- Update documentation

### Annual Tasks

#### Certificate Renewal
- Plan certificate renewal 30 days before expiration
- Test certificate deployment in non-production
- Schedule maintenance window for certificate update
- Communicate changes to users

#### Infrastructure Review
- Review VPN capacity and performance
- Evaluate cost optimization opportunities
- Update security policies and procedures
- Plan for infrastructure upgrades

## Emergency Procedures

### Immediate VPN Access Revocation
```bash
# NUCLEAR OPTION: Revoke ALL VPC access (immediate effect)
aws ec2 revoke-client-vpn-ingress \
    --client-vpn-endpoint-id cvpn-endpoint-0e142c7c94634e649 \
    --target-network-cidr "10.0.0.0/16" \
    --revoke-all-groups \
    --region us-east-2

# Check active connections (will be terminated)
aws ec2 describe-client-vpn-connections \
    --client-vpn-endpoint-id cvpn-endpoint-0e142c7c94634e649 \
    --region us-east-2
```

### Restore VPN Access
```bash
# Re-enable VPC access for all users
aws ec2 authorize-client-vpn-ingress \
    --client-vpn-endpoint-id cvpn-endpoint-0e142c7c94634e649 \
    --target-network-cidr "10.0.0.0/16" \
    --authorize-all-groups \
    --region us-east-2

# Verify access restored
aws ec2 describe-client-vpn-authorization-rules \
    --client-vpn-endpoint-id cvpn-endpoint-0e142c7c94634e649 \
    --region us-east-2
```

### Complete VPN Endpoint Management
```bash
# Disable VPN endpoint (prevents new connections)
aws ec2 modify-client-vpn-endpoint \
    --client-vpn-endpoint-id cvpn-endpoint-0e142c7c94634e649 \
    --connection-log-options Enabled=false \
    --region us-east-2

# PERMANENT: Delete VPN endpoint entirely (3-step process)
# Step 1: Get association ID
aws ec2 describe-client-vpn-target-networks \
    --client-vpn-endpoint-id cvpn-endpoint-0e142c7c94634e649 \
    --region us-east-2 \
    --query 'ClientVpnTargetNetworks[*].AssociationId' \
    --output text

# Step 2: Disassociate target network (use association ID from above)
aws ec2 disassociate-client-vpn-target-network \
    --client-vpn-endpoint-id cvpn-endpoint-0e142c7c94634e649 \
    --association-id cvpn-assoc-0460c257eb8be2745 \
    --region us-east-2

# Step 3: Delete VPN endpoint (after disassociation completes)
aws ec2 delete-client-vpn-endpoint \
    --client-vpn-endpoint-id cvpn-endpoint-0e142c7c94634e649 \
    --region us-east-2

# WARNING: Deletion is irreversible - you'll need to redeploy
# All users will lose access and need new .ovpn files
```

### Automated VPN Endpoint Deletion
```bash
# One-liner to delete VPN endpoint (handles disassociation automatically)
ASSOC_ID=$(aws ec2 describe-client-vpn-target-networks --client-vpn-endpoint-id cvpn-endpoint-0e142c7c94634e649 --region us-east-2 --query 'ClientVpnTargetNetworks[0].AssociationId' --output text) && \
aws ec2 disassociate-client-vpn-target-network --client-vpn-endpoint-id cvpn-endpoint-0e142c7c94634e649 --association-id $ASSOC_ID --region us-east-2 && \
echo "Waiting for disassociation..." && sleep 30 && \
aws ec2 delete-client-vpn-endpoint --client-vpn-endpoint-id cvpn-endpoint-0e142c7c94634e649 --region us-east-2
```

### Monitor VPN Status
```bash
# Check VPN endpoint status
aws ec2 describe-client-vpn-endpoints \
    --client-vpn-endpoint-ids cvpn-endpoint-0e142c7c94634e649 \
    --region us-east-2

# View all active connections
aws ec2 describe-client-vpn-connections \
    --client-vpn-endpoint-id cvpn-endpoint-0e142c7c94634e649 \
    --region us-east-2

# Check authorization rules
aws ec2 describe-client-vpn-authorization-rules \
    --client-vpn-endpoint-id cvpn-endpoint-0e142c7c94634e649 \
    --region us-east-2
```

## Monitoring & Alerts

### Set Up CloudWatch Alarms
```bash
# Monitor connection failures
aws cloudwatch put-metric-alarm \
    --alarm-name "VPN-Connection-Failures" \
    --alarm-description "Alert on VPN connection failures" \
    --metric-name "ConnectionAttempts" \
    --namespace "AWS/ClientVPN" \
    --statistic Sum \
    --period 300 \
    --threshold 10 \
    --comparison-operator GreaterThanThreshold \
    --region us-east-2
```reshold 10 \
    --comparison-operator GreaterThanThreshold \
    --region us-east-2
```

### Regular Health Checks
- Monitor certificate expiration dates
- Check VPN endpoint status
- Verify user access permissions
- Review security group configurations
- Test connectivity from different locations


```bash
# Check VPN status
aws ec2 describe-client-vpn-endpoints --region us-east-2

# View connection logs
aws logs describe-log-streams --log-group-name vpn-logs --region us-east-2

# Test user access
python cert_manager.py list
```

## Security Checklist

- [ ] Certificate validated and issued
- [ ] VPN endpoint created successfully
- [ ] Authorization rules configured
- [ ] Users synced from IAM
- [ ] Client configuration distributed
- [ ] Connection logging enabled
- [ ] Test connection successful

## Important Values Reference

Keep these values handy for administration:

```
VPC ID: vpc-09a94e086232207f4
Subnet ID: subnet-0459cd356e8cda83d
VPC CIDR: 10.0.0.0/16
VPN Endpoint ID: cvpn-endpoint-0e142c7c94634e649
Server Certificate ARN: arn:aws:acm:us-east-2:ACCOUNT:certificate/CERT-ID
Client CA Certificate ARN: arn:aws:acm:us-east-2:ACCOUNT:certificate/CLIENT-CA-ID
Region: us-east-2
Authentication: Certificate-based
Split Tunneling: Enabled
```