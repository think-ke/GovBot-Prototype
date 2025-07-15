# GovStack Audit Trail System

## Overview

The GovStack audit trail system provides comprehensive tracking of all user actions across the platform. It records who performed what action, when, and includes contextual information about the operation.

## Features

### 🔍 **Complete Action Tracking**
- Document uploads and deletions
- Website crawl operations
- Collection management (create, update, delete)
- API access with user identification
- IP address and user agent tracking

### 📊 **Detailed Audit Logs**
- User identification via API key names
- Action types (upload, delete, crawl_start, crawl_complete, etc.)
- Resource types (document, webpage, collection)
- Timestamps with timezone information
- Additional context in JSON details field

### 🛡️ **Security & Compliance**
- Immutable audit records
- User attribution for all operations
- Full audit trail for compliance requirements
- Indexed queries for performance

## Database Schema

### Audit Log Table
```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,           -- API key name or user identifier
    action VARCHAR(100) NOT NULL,            -- Action performed
    resource_type VARCHAR(50) NOT NULL,      -- Type of resource
    resource_id VARCHAR(100),                -- ID of affected resource
    details JSONB,                           -- Additional context
    ip_address VARCHAR(45),                  -- User's IP address
    user_agent TEXT,                         -- User agent string
    api_key_name VARCHAR(100) NOT NULL,      -- API key used
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_audit_user_timestamp ON audit_logs(user_id, timestamp);
CREATE INDEX idx_audit_action_resource ON audit_logs(action, resource_type);
CREATE INDEX idx_audit_resource_lookup ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_api_key_timestamp ON audit_logs(api_key_name, timestamp);
```

### Enhanced Resource Tables
Documents and webpages now include audit trail fields:

```sql
-- Documents table additions
ALTER TABLE documents ADD COLUMN created_by VARCHAR(100);
ALTER TABLE documents ADD COLUMN updated_by VARCHAR(100);
ALTER TABLE documents ADD COLUMN api_key_name VARCHAR(100);

-- Webpages table additions  
ALTER TABLE webpages ADD COLUMN created_by VARCHAR(100);
ALTER TABLE webpages ADD COLUMN updated_by VARCHAR(100);
ALTER TABLE webpages ADD COLUMN api_key_name VARCHAR(100);
```

## API Endpoints

### Audit Log Endpoints
All audit endpoints require admin permissions (`X-API-Key` with admin rights).

#### `GET /admin/audit-logs`
List audit logs with filtering and pagination.

**Query Parameters:**
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Max records to return (default: 50, max: 1000)
- `user_id` (string): Filter by user ID
- `action` (string): Filter by action type
- `resource_type` (string): Filter by resource type
- `resource_id` (string): Filter by specific resource ID
- `hours_ago` (int): Filter by hours ago (max: 8760 = 1 year)

**Example:**
```bash
curl -H "X-API-Key: gs-dev-admin-key-67890" \
  "http://localhost:5000/admin/audit-logs?action=upload&hours_ago=24&limit=10"
```

#### `GET /admin/audit-logs/summary`
Get audit summary statistics.

**Query Parameters:**
- `hours_ago` (int): Time period in hours (default: 24, max: 8760)

**Response:**
```json
{
  "total_actions": 45,
  "unique_users": 3,
  "action_counts": {
    "upload": 15,
    "crawl_start": 8,
    "crawl_complete": 8,
    "delete": 2
  },
  "resource_type_counts": {
    "document": 17,
    "webpage": 25,
    "collection": 3
  },
  "recent_activity": [...]
}
```

#### `GET /admin/audit-logs/user/{user_id}`
Get audit logs for a specific user.

#### `GET /admin/audit-logs/resource/{resource_type}/{resource_id}`
Get audit logs for a specific resource.

## Action Types

### Document Actions
- `upload` - Document uploaded to MinIO
- `delete` - Document deleted
- `access` - Document accessed (if enabled)

### Webpage Actions  
- `crawl_start` - Website crawl initiated
- `crawl_complete` - Website crawl completed successfully
- `crawl_failed` - Website crawl failed

### Collection Actions
- `create` - Collection created
- `update` - Collection updated
- `delete` - Collection deleted

## User Identification

Users are identified by their API key names:
- `master` - Master API key (full access)
- `admin` - Admin API key (no delete permission)
- Custom API keys can be configured

## Setup & Migration

### 1. Run Migration Script
```bash
cd /home/ubuntu/govstack
python scripts/add_audit_trail.py
```

### 2. Verify Installation
```bash
python scripts/test_audit_trail.py
```

## Usage Examples

### View Recent Activity
```bash
# Get last 24 hours of activity
curl -H "X-API-Key: gs-dev-admin-key-67890" \
  "http://localhost:5000/admin/audit-logs/summary?hours_ago=24"
```

### Track User Actions
```bash
# Get all actions by a specific user
curl -H "X-API-Key: gs-dev-admin-key-67890" \
  "http://localhost:5000/admin/audit-logs/user/master"
```

### Monitor Document Operations
```bash
# Get all document-related actions
curl -H "X-API-Key: gs-dev-admin-key-67890" \
  "http://localhost:5000/admin/audit-logs?resource_type=document"
```

### Resource History
```bash
# Get history for a specific document
curl -H "X-API-Key: gs-dev-admin-key-67890" \
  "http://localhost:5000/admin/audit-logs/resource/document/123"
```

## Security Considerations

### Access Control
- Audit log endpoints require admin permissions
- Resource-specific logs require read permissions
- Audit logging cannot be disabled by API users

### Data Retention
- Audit logs are permanent by default
- Consider implementing archival/cleanup policies for large deployments
- Logs include IP addresses for security analysis

### Privacy
- User agent strings are logged for security
- IP addresses are tracked for access monitoring
- Sensitive data should not be included in details field

## Integration with Analytics

The audit trail data can be integrated with the analytics dashboard for:
- User activity monitoring
- System usage patterns
- Compliance reporting
- Security analysis

## Troubleshooting

### Common Issues

1. **Missing audit logs**
   - Verify migration was run successfully
   - Check database connection
   - Ensure audit logging isn't failing silently

2. **Performance issues**
   - Audit table indexes are created automatically
   - Consider partitioning for very large datasets
   - Monitor query performance

3. **Permission errors**
   - Audit endpoints require admin permissions
   - Verify API key has correct permissions

### Log Analysis
```bash
# Check application logs for audit failures
grep -i "audit" /var/log/govstack/app.log

# Monitor database for audit table size
psql -c "SELECT COUNT(*) FROM audit_logs;"
```

## Future Enhancements

Potential improvements to the audit trail system:
- Real-time audit log streaming
- Audit log retention policies
- Enhanced search and filtering
- Integration with SIEM systems
- Automated compliance reporting
- Audit log encryption
- Anonymous user tracking options

## Compliance

This audit trail system helps meet various compliance requirements:
- **SOC 2 Type II** - Access logging and monitoring
- **GDPR** - Data access and modification tracking  
- **HIPAA** - Audit trail requirements (if handling health data)
- **ISO 27001** - Information security management

The system provides a complete audit trail of all data access and modifications, supporting compliance audits and security investigations.
