# GovStack Admin Dashboard - Technical Specification

## Executive Summary

This document outlines the technical specification for a comprehensive admin dashboard that enables administrators to manage documents, websites, and content collections within the GovStack AI-powered eCitizen Services platform. The dashboard will provide full CRUD operations for file management, website crawling, content versioning, and system monitoring.

## System Overview

### Purpose
The admin dashboard serves as a centralized interface for:
- Document upload, management, and versioning
- Website crawling configuration and monitoring
- Content collection organization
- File and webpage metadata management
- System health monitoring and analytics

### Architecture
- **Frontend**: Next.js 15 with TypeScript and Tailwind CSS (extending existing analytics-dashboard)
- **Backend**: FastAPI with existing endpoints in `/app/api/fast_api_app.py`
- **Database**: PostgreSQL (existing models: Document, Webpage, WebpageLink)
- **Storage**: MinIO for file storage
- **Authentication**: API Key-based authentication with role-based permissions

## API Integration

### Existing API Endpoints to Utilize

#### Document Management
- `POST /documents/` - Upload documents
- `GET /documents/` - List documents with pagination
- `GET /documents/{document_id}` - Get document details
- `DELETE /documents/{document_id}` - Delete documents

#### Website & Webpage Management
- `POST /crawl/` - Start website crawling
- `GET /crawl/{task_id}` - Get crawl status
- `POST /webpages/fetch-webpage/` - Fetch single webpage
- `GET /webpages/` - List webpages with pagination
- `GET /webpages/{webpage_id}` - Get webpage details
- `GET /webpages/collection/{collection_id}` - Get webpages by collection
- `GET /webpages/by-url/` - Get webpage by URL

#### Collection Management
- `GET /collections/{collection_id}/extract-texts` - Extract text from collection
- `GET /collections/{collection_id}/stats` - Get collection statistics
- `GET /collections/all-stats` - Get all collection statistics

### Required New API Endpoints

#### Document Versioning
```typescript
POST /documents/{document_id}/versions
PUT /documents/{document_id}
GET /documents/{document_id}/versions
POST /documents/{document_id}/versions/{version_id}/restore
```

#### Webpage Management
```typescript
PUT /webpages/{webpage_id}
DELETE /webpages/{webpage_id}
POST /webpages/{webpage_id}/recrawl
```

#### Collection Management
```typescript
POST /collections/
PUT /collections/{collection_id}
DELETE /collections/{collection_id}
POST /collections/{collection_id}/documents
DELETE /collections/{collection_id}/documents/{document_id}
```

## Data Models

### Document Model (Existing)
```typescript
interface Document {
  id: number;
  filename: string;
  object_name: string;
  content_type: string;
  size: number;
  upload_date: string;
  last_accessed?: string;
  description?: string;
  is_public: boolean;
  metadata?: Record<string, any>;
  collection_id?: string;
}
```

### Webpage Model (Existing)
```typescript
interface Webpage {
  id: number;
  url: string;
  title?: string;
  content_hash?: string;
  last_crawled: string;
  first_crawled: string;
  crawl_depth: number;
  status_code?: number;
  error?: string;
  metadata?: Record<string, any>;
  is_seed: boolean;
  content_type?: string;
  collection_id?: string;
  is_indexed: boolean;
  indexed_at?: string;
}
```

### New Models Required

#### Document Version Model
```typescript
interface DocumentVersion {
  id: number;
  document_id: number;
  version_number: number;
  object_name: string;
  size: number;
  created_at: string;
  created_by: string;
  changelog?: string;
  is_current: boolean;
}
```

#### Collection Model
```typescript
interface Collection {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  created_by: string;
  type: 'documents' | 'webpages' | 'mixed';
  metadata?: Record<string, any>;
  document_count: number;
  webpage_count: number;
  total_size: number;
}
```

## User Interface Specification

### Layout Structure
```
┌─────────────────────────────────────────────────────────────┐
│ Header (Logo, Search, User Menu, Notifications)            │
├───────────────┬─────────────────────────────────────────────┤
│ Sidebar       │ Main Content Area                           │
│ - Dashboard   │                                             │
│ - Documents   │                                             │
│ - Websites    │                                             │
│ - Collections │                                             │
│ - Analytics   │                                             │
│ - Settings    │                                             │
└───────────────┴─────────────────────────────────────────────┘
```

### Key Pages and Components

#### 1. Dashboard Overview
**Route**: `/admin`
**Components**:
- System health metrics
- Recent activity feed
- Quick stats (total documents, webpages, collections)
- Active crawl jobs status
- Storage usage metrics

#### 2. Document Management
**Route**: `/admin/documents`
**Features**:
- File upload with drag-and-drop
- Bulk upload support
- Document listing with advanced filtering
- Document preview and download
- Metadata editing
- Version history management
- Collection assignment

**Components**:
- `DocumentUpload` - File upload interface
- `DocumentTable` - Data table with sorting/filtering
- `DocumentPreview` - File preview modal
- `DocumentMetadataEditor` - Form for editing metadata
- `VersionHistory` - Version management interface

#### 3. Website Management
**Route**: `/admin/websites`
**Features**:
- Website crawl configuration
- Crawl job monitoring
- Webpage listing and management
- Content preview
- Re-crawl functionality
- Crawl depth and strategy configuration

**Components**:
- `CrawlJobCreator` - Form for configuring new crawls
- `CrawlMonitor` - Real-time crawl status dashboard
- `WebpageTable` - Paginated webpage listing
- `WebpagePreview` - Content preview modal
- `CrawlSettings` - Configuration interface

#### 4. Collection Management
**Route**: `/admin/collections`
**Features**:
- Collection creation and organization
- Content assignment to collections
- Collection analytics
- Bulk operations
- Search and filtering

**Components**:
- `CollectionCreator` - Collection creation form
- `CollectionBrowser` - Tree view of collections
- `CollectionDetails` - Detailed collection view
- `ContentAssigner` - Interface for assigning content to collections

#### 5. File Browser
**Route**: `/admin/files`
**Features**:
- Hierarchical file browser
- Search across all content
- Advanced filtering options
- Bulk selection and operations
- File organization tools

### Component Specifications

#### DocumentUpload Component
```typescript
interface DocumentUploadProps {
  onUploadSuccess: (documents: Document[]) => void;
  onUploadError: (error: string) => void;
  acceptedTypes?: string[];
  maxFileSize?: number;
  collectionId?: string;
  multiple?: boolean;
}

const DocumentUpload: React.FC<DocumentUploadProps> = ({
  onUploadSuccess,
  onUploadError,
  acceptedTypes = ['.pdf', '.docx', '.txt', '.md'],
  maxFileSize = 50 * 1024 * 1024, // 50MB
  collectionId,
  multiple = true
}) => {
  // Implementation with react-dropzone
  // Progress tracking
  // Error handling
  // Metadata input
};
```

#### CrawlJobCreator Component
```typescript
interface CrawlJobCreatorProps {
  onCrawlStart: (taskId: string) => void;
  onError: (error: string) => void;
}

interface CrawlConfig {
  url: string;
  depth: number;
  concurrent_requests: number;
  follow_external: boolean;
  strategy: 'breadth_first' | 'depth_first';
  collection_id?: string;
}

const CrawlJobCreator: React.FC<CrawlJobCreatorProps> = ({
  onCrawlStart,
  onError
}) => {
  // URL validation
  // Advanced configuration options
  // Preview of crawl scope
  // Collection selection
};
```

#### DataTable Component (Reusable)
```typescript
interface DataTableProps<T> {
  data: T[];
  columns: ColumnDef<T>[];
  pagination: PaginationState;
  sorting: SortingState;
  filtering: FilteringState;
  onPaginationChange: (pagination: PaginationState) => void;
  onSortingChange: (sorting: SortingState) => void;
  onFilteringChange: (filtering: FilteringState) => void;
  loading?: boolean;
  error?: string;
  actions?: ActionDef<T>[];
}
```

## Technical Implementation

### State Management
- **React Query/TanStack Query** for server state management
- **Zustand** for client-side state management
- **React Hook Form** for form state management

### Key Libraries and Dependencies
```json
{
  "dependencies": {
    "@tanstack/react-query": "^5.0.0",
    "@tanstack/react-table": "^8.0.0",
    "react-hook-form": "^7.45.0",
    "react-dropzone": "^14.2.0",
    "recharts": "^2.8.0",
    "date-fns": "^2.30.0",
    "react-hot-toast": "^2.4.0",
    "cmdk": "^0.2.0",
    "zustand": "^4.4.0"
  }
}
```

### API Client Structure
```typescript
// lib/api-client.ts
class ApiClient {
  private baseUrl: string;
  private apiKey: string;

  constructor(baseUrl: string, apiKey: string) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  // Document methods
  async uploadDocument(file: File, metadata: DocumentMetadata): Promise<Document>
  async getDocuments(params: ListParams): Promise<PaginatedResponse<Document>>
  async getDocument(id: number): Promise<Document>
  async deleteDocument(id: number): Promise<void>
  async updateDocument(id: number, updates: Partial<Document>): Promise<Document>

  // Webpage methods
  async startCrawl(config: CrawlConfig): Promise<CrawlTask>
  async getCrawlStatus(taskId: string): Promise<CrawlStatus>
  async getWebpages(params: ListParams): Promise<PaginatedResponse<Webpage>>
  async deleteWebpage(id: number): Promise<void>
  async recrawlWebpage(id: number): Promise<CrawlTask>

  // Collection methods
  async getCollections(): Promise<Collection[]>
  async createCollection(collection: CreateCollectionRequest): Promise<Collection>
  async updateCollection(id: string, updates: Partial<Collection>): Promise<Collection>
  async deleteCollection(id: string): Promise<void>
  async getCollectionStats(id: string): Promise<CollectionStats>
}
```

### File Structure
```
analytics-dashboard/
├── app/
│   ├── admin/
│   │   ├── layout.tsx
│   │   ├── page.tsx                    # Dashboard overview
│   │   ├── documents/
│   │   │   ├── page.tsx               # Document listing
│   │   │   ├── upload/page.tsx        # Upload interface
│   │   │   └── [id]/
│   │   │       ├── page.tsx           # Document details
│   │   │       └── versions/page.tsx  # Version history
│   │   ├── websites/
│   │   │   ├── page.tsx               # Website management
│   │   │   ├── crawl/page.tsx         # Crawl configuration
│   │   │   └── [id]/page.tsx          # Webpage details
│   │   ├── collections/
│   │   │   ├── page.tsx               # Collection listing
│   │   │   ├── create/page.tsx        # Collection creation
│   │   │   └── [id]/page.tsx          # Collection details
│   │   └── files/
│   │       └── page.tsx               # File browser
├── components/
│   ├── admin/
│   │   ├── document/
│   │   │   ├── DocumentUpload.tsx
│   │   │   ├── DocumentTable.tsx
│   │   │   ├── DocumentPreview.tsx
│   │   │   ├── DocumentMetadataEditor.tsx
│   │   │   └── VersionHistory.tsx
│   │   ├── website/
│   │   │   ├── CrawlJobCreator.tsx
│   │   │   ├── CrawlMonitor.tsx
│   │   │   ├── WebpageTable.tsx
│   │   │   └── WebpagePreview.tsx
│   │   ├── collection/
│   │   │   ├── CollectionCreator.tsx
│   │   │   ├── CollectionBrowser.tsx
│   │   │   ├── CollectionDetails.tsx
│   │   │   └── ContentAssigner.tsx
│   │   ├── common/
│   │   │   ├── DataTable.tsx
│   │   │   ├── FileUpload.tsx
│   │   │   ├── SearchBar.tsx
│   │   │   └── BulkActions.tsx
│   │   └── layout/
│   │       ├── AdminSidebar.tsx
│   │       ├── AdminHeader.tsx
│   │       └── Breadcrumbs.tsx
├── lib/
│   ├── api-client.ts
│   ├── auth.ts
│   ├── types.ts
│   └── utils.ts
└── hooks/
    ├── useDocuments.ts
    ├── useWebpages.ts
    ├── useCollections.ts
    └── useCrawlJobs.ts
```

## Security and Permissions

### Authentication
- API key-based authentication for all admin operations
- Session management for UI persistence
- Secure token storage

### Authorization Levels
- **Read**: View documents, webpages, and collections
- **Write**: Upload documents, start crawls, create collections
- **Delete**: Remove documents, webpages, and collections
- **Admin**: Full system access including user management

### Data Protection
- Secure file upload validation
- Content sanitization for webpage content
- Audit logging for all admin actions
- Rate limiting for API calls

## Performance Considerations

### Optimization Strategies
- Lazy loading for large file lists
- Pagination for all data tables
- Caching for frequently accessed data
- Image optimization for previews
- Background processing for large operations

### Scalability
- Efficient database queries with proper indexing
- CDN integration for static assets
- Compression for file downloads
- Stream processing for large file uploads

## Monitoring and Analytics

### System Metrics
- Upload/download rates
- Crawl job performance
- Storage usage trends
- API response times
- Error rates and types

### User Analytics
- Admin action tracking
- Feature usage statistics
- Performance bottlenecks
- Common workflows

## Development Timeline

### Phase 1: Core Infrastructure (Week 1-2)
- Set up admin routing structure
- Implement basic layout and navigation
- Create API client and authentication
- Develop reusable DataTable component

### Phase 2: Document Management (Week 3-4)
- Document upload interface
- Document listing and filtering
- Metadata editing capabilities
- Basic file preview functionality

### Phase 3: Website Management (Week 5-6)
- Crawl job creation interface
- Crawl monitoring dashboard
- Webpage listing and management
- Content preview functionality

### Phase 4: Collection Management (Week 7-8)
- Collection creation and organization
- Content assignment workflows
- Collection analytics dashboard
- Search and filtering improvements

### Phase 5: Advanced Features (Week 9-10)
- Version management system
- Bulk operations
- Advanced search capabilities
- Performance optimizations

### Phase 6: Testing and Polish (Week 11-12)
- Comprehensive testing
- UI/UX refinements
- Documentation completion
- Deployment preparation

## Testing Strategy

### Unit Testing
- Component testing with React Testing Library
- API client testing with Mock Service Worker
- Hook testing with React Hooks Testing Library

### Integration Testing
- End-to-end testing with Playwright
- API integration testing
- File upload/download testing

### Performance Testing
- Load testing for file operations
- Stress testing for crawl jobs
- Memory usage optimization

## Deployment Considerations

### Environment Configuration
- Environment-specific API endpoints
- Feature flags for gradual rollout
- Configuration management

### CI/CD Pipeline
- Automated testing on pull requests
- Staging environment deployment
- Production deployment with rollback capability

### Monitoring and Logging
- Error tracking with Sentry
- Performance monitoring
- User action logging for audit trails

## Future Enhancements

### Planned Features
- Real-time notifications for crawl completion
- Advanced content search with elasticsearch
- Automated content categorization
- Content scheduling and publication workflows
- Multi-tenant support for different government agencies

### Integration Opportunities
- Integration with external document management systems
- API integration with other government platforms
- Advanced analytics and reporting capabilities
- Machine learning-powered content recommendations

---

This specification provides a comprehensive framework for building a robust admin dashboard that integrates seamlessly with the existing GovStack platform while providing powerful content management capabilities for administrators.
