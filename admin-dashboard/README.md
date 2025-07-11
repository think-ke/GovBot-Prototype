# GovStack Admin Dashboard

A comprehensive administrative interface for managing documents, websites, and content collections in the GovStack AI-powered eCitizen Services platform.

## Features

- **Document Management**: Upload, organize, and manage documents with version control
- **Website Crawling**: Configure and monitor website crawling jobs
- **Collection Management**: Organize content into logical collections
- **Real-time Monitoring**: Track crawl progress and system health
- **Modern UI**: Built with Next.js 15, TypeScript, and Tailwind CSS

## Tech Stack

- **Frontend**: Next.js 15.2.4 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS with Shadcn/ui components
- **State Management**: React Query for server state, Zustand for client state
- **Forms**: React Hook Form with Zod validation
- **File Upload**: React Dropzone
- **Icons**: Lucide React

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or pnpm
- Running GovStack API server

### Installation

1. Navigate to the admin dashboard directory:
```bash
cd admin-dashboard
```

2. Install dependencies:
```bash
npm install
# or
pnpm install
```

3. Create environment variables:
```bash
cp .env.example .env.local
```

4. Update the environment variables:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_KEY=your-api-key
```

5. Run the development server:
```bash
npm run dev
# or
pnpm dev
```

6. Open [http://localhost:3001](http://localhost:3001) in your browser.

## Project Structure

```
admin-dashboard/
├── app/                          # Next.js App Router pages
│   ├── layout.tsx               # Root layout
│   ├── page.tsx                 # Dashboard overview
│   ├── documents/               # Document management pages
│   ├── websites/                # Website management pages
│   └── collections/             # Collection management pages
├── components/                   # React components
│   ├── ui/                      # Shadcn/ui components
│   ├── layout/                  # Layout components
│   ├── dashboard/               # Dashboard components
│   ├── documents/               # Document management components
│   ├── websites/                # Website management components
│   └── collections/             # Collection management components
├── lib/                         # Utility libraries
│   ├── api-client.ts           # API client for backend communication
│   ├── types.ts                # TypeScript type definitions
│   └── utils.ts                # General utilities
└── hooks/                       # Custom React hooks
```

## API Integration

The dashboard integrates with the GovStack FastAPI backend through the following endpoints:

### Document Management
- `POST /documents/` - Upload documents
- `GET /documents/` - List documents
- `GET /documents/{id}` - Get document details
- `DELETE /documents/{id}` - Delete documents

### Website Management
- `POST /crawl/` - Start website crawling
- `GET /crawl/{task_id}` - Get crawl status
- `GET /webpages/` - List webpages
- `GET /webpages/collection/{collection_id}` - Get webpages by collection

### Collection Management
- `GET /collections/` - List collections
- `POST /collections/` - Create collection
- `PUT /collections/{id}` - Update collection
- `DELETE /collections/{id}` - Delete collection

## Configuration

### Environment Variables

- `NEXT_PUBLIC_API_URL`: Base URL for the GovStack API (default: http://localhost:8000)
- `NEXT_PUBLIC_API_KEY`: API key for authentication

### API Authentication

The dashboard uses API key authentication. Set your API key in the environment variables or configure it in the API client.

## Development

### Adding New Features

1. **Create Components**: Add new components in the appropriate directory under `components/`
2. **Add Pages**: Create new pages in the `app/` directory following Next.js App Router conventions
3. **Update API Client**: Add new API methods in `lib/api-client.ts`
4. **Add Types**: Define TypeScript types in `lib/types.ts`

### Code Style

- Use TypeScript for all new code
- Follow React best practices
- Use Tailwind CSS for styling
- Implement proper error handling
- Add loading states for async operations

## Deployment

### Production Build

```bash
npm run build
npm start
```

### Docker Deployment

Create a Dockerfile:

```dockerfile
FROM node:18-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app
ENV NODE_ENV production
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3001
ENV PORT 3001
CMD ["node", "server.js"]
```

### Environment Configuration

For production deployment:

1. Set production API URL
2. Configure proper API keys
3. Set up proper CORS settings
4. Configure reverse proxy if needed

## Monitoring and Analytics

The dashboard includes:

- Real-time crawl job monitoring
- System health checks
- Error tracking and reporting
- Performance metrics

## Security

- API key-based authentication
- Input validation and sanitization
- Secure file upload handling
- CORS protection
- Rate limiting (implemented on API side)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Troubleshooting

### Common Issues

1. **API Connection Issues**: Check that the API server is running and accessible
2. **Authentication Errors**: Verify API key configuration
3. **Build Errors**: Ensure all dependencies are installed
4. **CORS Issues**: Configure CORS settings on the API server

### Debugging

- Check browser console for JavaScript errors
- Verify network requests in browser dev tools
- Check API server logs for backend issues
- Use React Query DevTools for state debugging

## License

This project is part of the GovStack platform and follows the same licensing terms.
