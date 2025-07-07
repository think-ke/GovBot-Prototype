# GovStack API Security Guide

## Overview

GovStack API implements a comprehensive security model based on API key authentication with role-based access control. This document outlines security features, best practices, and configuration guidelines.

## Authentication System

### API Key Authentication

All API endpoints (except public health checks) require authentication via the `X-API-Key` header:

```http
X-API-Key: your-secure-api-key-here
```

### API Key Types

The system supports multiple API key types with different permission levels:

#### Master API Key
- **Environment Variable**: `GOVSTACK_API_KEY`
- **Permissions**: read, write, delete (full access)
- **Use Case**: Administrative operations, full system access
- **Default**: Configured in `.env` files

#### Admin API Key  
- **Environment Variable**: `GOVSTACK_ADMIN_API_KEY`
- **Permissions**: read, write (no delete)
- **Use Case**: Application operations, content management
- **Default**: Configured in `.env` files

#### Custom API Keys
Additional API keys can be configured programmatically with specific permissions.

## Permission Levels

### Read Permission
- **Endpoints**: All GET endpoints
- **Operations**: 
  - View documents and metadata
  - Access chat history
  - Retrieve webpage data
  - Get collection statistics
  - Check crawl status

### Write Permission
- **Endpoints**: POST endpoints
- **Operations**:
  - Upload documents
  - Create chat messages
  - Start web crawls
  - Extract text content
  - Fetch webpages

### Delete Permission
- **Endpoints**: DELETE endpoints
- **Operations**:
  - Remove documents
  - Delete chat sessions
  - Clean up resources

## Security Configuration

### Environment Variables

#### Required Security Variables
```bash
# Master API key with full permissions
GOVSTACK_API_KEY="your-secure-master-key-here"

# Admin API key with read/write permissions  
GOVSTACK_ADMIN_API_KEY="your-secure-admin-key-here"
```

#### Database Security
```bash
# Strong database password
POSTGRES_PASSWORD="your-strong-db-password"

# Secure database connection string
DATABASE_URL="postgresql+asyncpg://postgres:password@host:5432/db"
```

#### ChromaDB Security
```bash
# ChromaDB authentication
CHROMA_USERNAME="your-chroma-username"
CHROMA_PASSWORD="your-secure-chroma-password"
CHROMA_CLIENT_AUTHN_CREDENTIALS="username:password"
```

#### MinIO Security
```bash
# MinIO access credentials
MINIO_ACCESS_KEY="your-minio-access-key"  
MINIO_SECRET_KEY="your-minio-secret-key"
```

### API Key Best Practices

#### Key Generation
- Use cryptographically secure random generators
- Minimum 32 characters length
- Include alphanumeric and special characters
- Avoid predictable patterns

Example secure key format:
```bash
GOVSTACK_API_KEY="gs-prod-$(openssl rand -hex 32)"
```

#### Key Management
1. **Rotation**: Rotate API keys regularly (every 90 days recommended)
2. **Storage**: Store keys in secure environment variables or secret management systems
3. **Scope**: Use minimal required permissions for each key
4. **Monitoring**: Log and monitor API key usage
5. **Revocation**: Have a process to quickly revoke compromised keys

#### Key Distribution
- Never commit API keys to version control
- Use secure channels for key distribution
- Implement key provisioning workflows
- Document key ownership and purpose

## Production Security Checklist

### Environment Setup
- [ ] Use strong, unique API keys
- [ ] Configure HTTPS/TLS encryption
- [ ] Set secure database passwords
- [ ] Enable access logging
- [ ] Configure CORS properly
- [ ] Disable debug mode (`DEV_MODE=false`)
- [ ] Set appropriate log levels

### Infrastructure Security
- [ ] Use private networks for database access
- [ ] Implement firewall rules
- [ ] Regular security updates
- [ ] Monitor system resources
- [ ] Backup encryption
- [ ] Network segmentation

### API Security
- [ ] Rate limiting implementation
- [ ] Request size limits
- [ ] Input validation
- [ ] Output sanitization
- [ ] Error message sanitization
- [ ] Security headers

### Monitoring and Auditing
- [ ] API access logging
- [ ] Failed authentication monitoring
- [ ] Unusual usage pattern detection
- [ ] Security event alerting
- [ ] Regular security audits

## Common Security Configurations

### Development Environment
```bash
# Development - Less restrictive but still secure
GOVSTACK_API_KEY="gs-dev-master-key-12345"
GOVSTACK_ADMIN_API_KEY="gs-dev-admin-key-67890"
DEV_MODE=true
LOG_LEVEL=DEBUG
```

### Production Environment
```bash
# Production - Maximum security
GOVSTACK_API_KEY="gs-prod-$(openssl rand -hex 32)"
GOVSTACK_ADMIN_API_KEY="gs-prod-admin-$(openssl rand -hex 32)"
DEV_MODE=false
LOG_LEVEL=INFO
```

### Staging Environment
```bash
# Staging - Production-like security
GOVSTACK_API_KEY="gs-staging-$(openssl rand -hex 24)"
GOVSTACK_ADMIN_API_KEY="gs-staging-admin-$(openssl rand -hex 24)"
DEV_MODE=false
LOG_LEVEL=INFO
```

## Error Handling

### Authentication Errors

The API returns specific error codes for authentication issues:

#### Missing API Key
```json
{
  "detail": "Missing API key",
  "status_code": 401
}
```

#### Invalid API Key
```json
{
  "detail": "Invalid API key", 
  "status_code": 401
}
```

#### Insufficient Permissions
```json
{
  "detail": "Insufficient permissions for this operation",
  "status_code": 403
}
```

### Security Headers

Recommended security headers for production:

```http
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
```

## Incident Response

### Compromised API Key
1. **Immediate**: Rotate the compromised key
2. **Investigate**: Check access logs for unauthorized usage
3. **Update**: Update all systems using the old key
4. **Monitor**: Watch for continued unauthorized access attempts
5. **Document**: Record the incident and response actions

### Suspected Breach
1. **Isolate**: Restrict access to affected systems
2. **Assess**: Determine scope and impact
3. **Contain**: Prevent further unauthorized access
4. **Recover**: Restore systems from secure backups if needed
5. **Learn**: Update security measures based on lessons learned

## Compliance Considerations

### Data Protection
- Encrypt data in transit and at rest
- Implement data retention policies
- Provide data access and deletion capabilities
- Maintain audit trails

### Access Control
- Implement principle of least privilege
- Regular access reviews
- Automated access provisioning/deprovisioning
- Multi-factor authentication for administrative access

### Monitoring and Logging
- Comprehensive audit logging
- Real-time security monitoring
- Incident response procedures
- Regular security assessments

## Contact and Reporting

For security issues:
1. Review this documentation first
2. Check application logs
3. Verify API key configuration
4. Test with appropriate permissions

Remember: Security is a shared responsibility between the API provider and consumers. Follow these guidelines to ensure secure operations.
