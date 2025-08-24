# Security Guidelines

## 🔒 Sensitive Files Protection

This project handles sensitive cryptographic materials and AWS infrastructure details. The following files are automatically excluded from Git via `.gitignore`:

### Never Commit These Files:
- **`certs/`** - Contains CA certificates, client certificates, and private keys
- **`vpn_user_config/`** - Contains user .ovpn files with embedded certificates  
- **`vpn_deployment_info.json`** - Contains VPC IDs, endpoint IDs, and ARNs
- **`*.key`, `*.crt`, `*.pem`** - Any certificate or private key files
- **`*.ovpn`** - VPN configuration files with embedded certificates

### Safe to Commit:
- **`vpn_deployment_info.template.json`** - Template showing structure without real values
- **`aws-permissions-policy.json`** - IAM policy template (no secrets)
- **`requirements.txt`** - Python dependencies
- **`*.py`** - Source code files
- **`*.md`** - Documentation files

## 🛡️ Security Best Practices

### Before Committing:
1. **Review staged files**: `git status` and `git diff --cached`
2. **Check for secrets**: Scan for AWS account IDs, certificate content, private keys
3. **Verify .gitignore**: Ensure sensitive directories are excluded

### If You Accidentally Commit Secrets:
1. **Immediately rotate** any exposed credentials
2. **Remove from Git history**: Use `git filter-branch` or BFG Repo-Cleaner
3. **Force push** to overwrite remote history
4. **Notify team** about the security incident

### Certificate Management:
- **Rotate certificates** if exposed
- **Use strong passphrases** for private keys (if applicable)
- **Limit certificate validity** periods
- **Monitor certificate usage** via AWS CloudTrail

### AWS Security:
- **Use IAM roles** instead of access keys when possible
- **Enable CloudTrail** logging for VPN operations
- **Monitor VPN connections** regularly
- **Implement least privilege** access policies

## 🚨 Emergency Response

If sensitive data is accidentally exposed:

1. **Immediate Actions:**
   ```bash
   # Revoke compromised certificates
   python cert_manager.py ban-user --client-name compromised-user --vpn-endpoint ENDPOINT-ID
   
   # Rotate AWS credentials if exposed
   aws iam create-access-key --user-name USERNAME
   aws iam delete-access-key --access-key-id OLD-KEY --user-name USERNAME
   ```

2. **Clean Git History:**
   ```bash
   # Remove file from all commits (use carefully!)
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch SENSITIVE-FILE' \
     --prune-empty --tag-name-filter cat -- --all
   
   # Force push to remote
   git push origin --force --all
   ```

3. **Verify Cleanup:**
   ```bash
   # Check that sensitive files are gone
   git log --all --full-history -- SENSITIVE-FILE
   ```

## 📋 Security Checklist

Before pushing to GitHub:

- [ ] Run `git status` to check staged files
- [ ] Verify no files in `certs/` or `vpn_user_config/` are staged
- [ ] Check that `vpn_deployment_info.json` is not staged
- [ ] Scan commit diff for AWS account IDs, ARNs, or certificate content
- [ ] Ensure `.gitignore` is up to date
- [ ] Test that sensitive operations still work after excluding files

## 🔍 Monitoring

Set up monitoring for:
- **Unauthorized VPN connections**
- **Certificate usage patterns**
- **Failed authentication attempts**
- **Unusual network traffic patterns**

Use AWS CloudWatch and CloudTrail to track VPN-related activities.