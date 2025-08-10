# Supabase Integration Guide

This document explains the Supabase integration implemented for the KeepInTouch backend, replacing the previous in-memory storage system with production-ready data persistence.

## Overview

The Supabase integration provides:
- **Database**: PostgreSQL with full CRUD operations
- **Authentication**: Built-in auth with JWT tokens
- **Storage**: File uploads and management
- **Real-time**: Database change subscriptions
- **Row Level Security**: Fine-grained access control

## Architecture

### Repository Pattern
The application uses the repository pattern to abstract database operations:

```
src/keepintouch/storage/
├── supabase_client.py          # Supabase client wrapper
├── supabase_storage.py         # File storage management
└── repositories/
    ├── base_repository.py      # Base CRUD operations
    ├── user_repository.py      # User-specific operations
    ├── onboarding_repository.py # Onboarding session management
    ├── document_repository.py  # File metadata management
    └── visibility_repository.py # Privacy settings management
```

### Database Schema
Complete schema with 9 main tables:
- `users` - Core user information
- `visibility_categories` - Privacy settings
- `info_sources` - External data connections
- `documents` - File metadata
- `diary_entries` - Time-based life updates
- `life_facts` - Timeless personal information
- `friends` - User relationships
- `conversations` - Chat sessions
- `onboarding_sessions` - Temporary session data

## Configuration

### Environment Variables
Required environment variables in `.env`:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
```

### Auto-Detection
The application automatically detects Supabase configuration:
- If configured: Uses Supabase for persistence
- If not configured: Falls back to in-memory storage

## Database Setup

### 1. Create Supabase Project
1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Wait for database provisioning

### 2. Run Schema Migration
Execute the schema file in Supabase SQL Editor:
```bash
# Copy content of database/schema.sql to Supabase SQL Editor
# This creates all tables, indexes, and RLS policies
```

### 3. Optional: Seed Data
Run the seed data for testing:
```bash
# Copy content of database/seed.sql to Supabase SQL Editor
# This creates sample users and data for development
```

## Usage Examples

### Repository Usage
```python
from storage.repositories import UserRepository, OnboardingRepository

# Create repositories
user_repo = UserRepository(use_service_key=True)
onboarding_repo = OnboardingRepository()

# Create user
user = await user_repo.create_user({
    "username": "johndoe",
    "email": "john@example.com", 
    "full_name": "John Doe",
    "bio": "Software engineer"
})

# Start onboarding session
session = await onboarding_repo.create_session(user["id"])
```

### File Storage
```python
from storage.supabase_storage import upload_user_file, get_user_file_url

# Upload file
result = await upload_user_file(
    user_id="123",
    file_content=file_bytes,
    filename="document.pdf"
)

# Get signed URL for access
url = await get_user_file_url(result["file_path"], expires_in=3600)
```

### Direct Client Access
```python
from storage.supabase_client import get_supabase_raw_client

client = get_supabase_raw_client(use_service_key=True)
response = client.table("users").select("*").eq("username", "johndoe").execute()
```

## API Changes

### Dual Endpoint System
The application now supports both storage backends:

**With Supabase configured:**
- Uses `/api/onboarding` routes with Supabase backend
- Data persisted to PostgreSQL database
- Files uploaded to Supabase Storage

**Without Supabase configured:**
- Uses `/api/onboarding` routes with memory backend
- Data stored in memory (development only)
- Files stored locally in temp directory

### New Endpoints
Additional endpoints for Supabase integration:
- `GET /api/onboarding/user/{user_id}/files` - Get user's files with signed URLs
- `GET /api/onboarding/health` - Extended health check with Supabase status

## Security Features

### Row Level Security (RLS)
All tables have RLS enabled with policies:
```sql
-- Users can only access their own data
CREATE POLICY "Users can manage their own data" ON users
  FOR ALL USING (auth.uid() = id::text::uuid);

-- Public profiles are readable by anyone
CREATE POLICY "Public profiles are readable" ON users
  FOR SELECT USING (is_public = true);
```

### File Storage Security
- Private bucket with no public access
- Signed URLs for temporary file access
- User-specific file organization
- MIME type validation

## Development vs Production

### Development Mode
Without Supabase configured:
- In-memory data storage
- Local file storage
- No authentication required
- Data lost on restart

### Production Mode
With Supabase configured:
- PostgreSQL database persistence
- Supabase Storage for files
- JWT authentication (when implemented)
- Data persisted across restarts
- Real-time capabilities
- Automatic backups

## Testing

### Unit Tests
Test repositories with mock Supabase client:
```python
# Example test
async def test_user_creation():
    user_repo = UserRepository()
    user = await user_repo.create_user({
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User"
    })
    assert user["username"] == "testuser"
```

### Integration Tests
Test with actual Supabase test database:
```python
# Use separate test project for integration tests
SUPABASE_TEST_URL = "https://test-project.supabase.co"
```

## Monitoring and Logging

### Application Logging
All repository operations are logged:
```python
import logging
logger = logging.getLogger(__name__)

# Repository operations include structured logging
logger.info(f"Created user: {user_id}")
logger.error(f"Failed to create user: {error}")
```

### Supabase Dashboard
Monitor via Supabase dashboard:
- Database usage and performance
- Storage usage and costs
- API request metrics
- Real-time connections

## Migration Path

### From Memory to Supabase
1. Set up Supabase project
2. Run schema migration
3. Add environment variables
4. Restart application
5. Existing memory data will be lost (expected)

### From Development to Production
1. Create production Supabase project
2. Update environment variables
3. Import/migrate any test data as needed
4. Configure monitoring and backups

## Performance Considerations

### Connection Pooling
Supabase client manages connection pooling automatically.

### Query Optimization
- Indexes created for common query patterns
- Repository methods use efficient queries
- Batch operations where possible

### Caching
Consider adding Redis caching layer for:
- Frequently accessed user profiles
- Session data
- File metadata

## Costs

### Supabase Pricing
- Database: Based on compute and storage
- Storage: $0.021 per GB per month
- Bandwidth: $0.09 per GB
- Auth: Free up to 50K monthly active users

### Optimization Tips
- Use appropriate data types (UUID vs TEXT)
- Implement file cleanup for unused documents
- Monitor storage usage via dashboard
- Use signed URLs instead of proxy downloads

## Future Enhancements

### Planned Features
1. **Authentication Middleware** - JWT token validation
2. **Real-time Updates** - Live chat and notifications  
3. **Advanced RLS** - Friend-based access policies
4. **File Processing** - Image resizing, document parsing
5. **Backup Strategy** - Automated database backups
6. **Analytics** - User behavior tracking
7. **Multi-tenant** - Organization-based data isolation

### Scalability
- Supabase scales automatically
- Consider read replicas for heavy read workloads
- Implement database sharding if needed
- Use CDN for file delivery

This completes the Supabase integration foundation for the KeepInTouch application, providing enterprise-grade data persistence and scalability.