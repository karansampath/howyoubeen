# Storage System Documentation

This document explains the KeepInTouch storage architecture, supporting both local storage for development/prototyping and Supabase for production deployment.

## Architecture Overview

The storage system uses an abstract interface pattern with pluggable backends:

```
StorageService (Abstract)
├── LocalStorageService (Development/Prototype)
└── SupabaseStorageService (Production)
```

Both implementations provide the same interface, allowing seamless switching between local and cloud storage without changing application logic.

## Storage Service Interface

### Core Operations
```python
class StorageService(ABC):
    # User Management
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool
    
    # Onboarding Sessions
    async def create_onboarding_session(self, user_id: str = None) -> str
    async def update_onboarding_session(self, session_id: str, data: Dict[str, Any]) -> bool
    async def get_onboarding_session(self, session_id: str) -> Optional[Dict[str, Any]]
    
    # File Management
    async def save_file(self, user_id: str, file_content: bytes, filename: str) -> str
    async def get_file_url(self, file_path: str) -> Optional[str]
    async def delete_file(self, file_path: str) -> bool
    
    # Document Metadata
    async def create_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]
    async def get_documents_for_user(self, user_id: str) -> List[Dict[str, Any]]
```

## Local Storage Service

### Overview
The `LocalStorageService` provides in-memory storage with local file system for development and prototyping.

### Features
- **In-Memory Database**: All data stored in Python dictionaries
- **Local File Storage**: Files saved to temporary directory
- **No External Dependencies**: Works without any database setup
- **Fast Development**: Instant startup, no configuration needed
- **Data Persistence**: Optional JSON file backup
- **Automatic Cleanup**: Temporary files cleaned on shutdown

### Implementation Details
```python
class LocalStorageService(StorageService):
    def __init__(self, backup_file: Optional[str] = None):
        self.users: Dict[str, Dict] = {}
        self.sessions: Dict[str, Dict] = {}
        self.documents: Dict[str, Dict] = {}
        self.temp_dir = tempfile.mkdtemp(prefix="keepintouch_")
        self.backup_file = backup_file
        
        # Load from backup if available
        if backup_file and os.path.exists(backup_file):
            self._load_from_backup()
```

### File Organization
```
/tmp/keepintouch_XXXXX/
├── users/
│   ├── user_123/
│   │   ├── documents/
│   │   │   ├── resume.pdf
│   │   │   └── photo.jpg
│   │   └── profile_image.jpg
│   └── user_456/
│       └── documents/
└── sessions/
    └── temp_uploads/
```

### Configuration
```python
# Use local storage
storage_service = LocalStorageService(backup_file="data/backup.json")

# Or without backup
storage_service = LocalStorageService()
```

### Advantages
- ✅ Zero setup required
- ✅ Fast development iteration
- ✅ No external dependencies
- ✅ Perfect for prototyping
- ✅ Easy debugging and inspection

### Limitations
- ❌ Data lost on restart (unless backed up)
- ❌ No concurrent access support
- ❌ Limited by available memory
- ❌ No production-grade features
- ❌ Single-machine only

## Supabase Storage Service

### Overview
The `SupabaseStorageService` provides production-ready storage using Supabase's PostgreSQL database and file storage.

### Features
- **PostgreSQL Database**: ACID transactions, indexes, constraints
- **File Storage**: CDN-backed file storage with signed URLs
- **Authentication**: Built-in user management and JWT tokens
- **Real-time**: Database change subscriptions
- **Row Level Security**: Fine-grained access control
- **Automatic Backups**: Point-in-time recovery
- **Global CDN**: Fast file delivery worldwide
- **Monitoring**: Built-in analytics and logging

### Implementation Details
```python
class SupabaseStorageService(StorageService):
    def __init__(self, supabase_url: str, supabase_key: str):
        self.client = create_client(supabase_url, supabase_key)
        self.storage_bucket = "user-documents"
        
        # Initialize repositories
        self.user_repo = UserRepository(self.client)
        self.onboarding_repo = OnboardingRepository(self.client)
        self.document_repo = DocumentRepository(self.client)
```

### Database Schema
Complete PostgreSQL schema with:
- **9 Main Tables**: users, documents, diary_entries, etc.
- **Foreign Key Constraints**: Data integrity
- **Indexes**: Optimized queries
- **RLS Policies**: Security rules
- **Triggers**: Automatic timestamps

### File Storage Structure
```
Supabase Storage Bucket: "user-documents"
├── user_123/
│   ├── documents/
│   │   ├── uuid1_resume.pdf
│   │   └── uuid2_photo.jpg
│   └── profile/
│       └── uuid3_avatar.jpg
└── user_456/
    └── documents/
        └── uuid4_journal.txt
```

### Configuration
```bash
# Environment variables
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

```python
# Use Supabase storage
storage_service = SupabaseStorageService(
    supabase_url=os.getenv("SUPABASE_URL"),
    supabase_key=os.getenv("SUPABASE_SERVICE_KEY")
)
```

### Advantages
- ✅ Production-ready scalability
- ✅ ACID transactions and consistency
- ✅ Automatic backups and recovery
- ✅ Global CDN for file delivery
- ✅ Built-in authentication
- ✅ Real-time capabilities
- ✅ Row-level security
- ✅ Professional monitoring tools

### Limitations
- ❌ Requires external service setup
- ❌ Internet connection required
- ❌ Usage-based costs
- ❌ More complex configuration

## Setting Up Storage

### Development Setup (Local Storage)

1. **No Configuration Required**
   ```python
   # Local storage works out of the box
   from storage.local_storage_service import LocalStorageService
   storage = LocalStorageService()
   ```

2. **Optional: Enable Data Persistence**
   ```python
   # Save data between restarts
   storage = LocalStorageService(backup_file="data/dev_backup.json")
   ```

3. **Environment Variables**
   ```bash
   # Optional: Configure local storage
   LOCAL_STORAGE_BACKUP=data/dev_backup.json
   LOCAL_STORAGE_TEMP_DIR=/tmp/keepintouch_dev
   ```

### Production Setup (Supabase)

#### Step 1: Create Supabase Project
1. Go to [supabase.com](https://supabase.com)
2. Sign up or log in
3. Click "New Project"
4. Choose organization and region
5. Set database password
6. Wait for project initialization (~2 minutes)

#### Step 2: Set Up Database Schema
1. Go to SQL Editor in Supabase dashboard
2. Copy contents of `backend/database/schema.sql`
3. Paste and execute in SQL Editor
4. Verify tables are created in Table Editor

#### Step 3: Configure Storage Bucket
1. Go to Storage in Supabase dashboard
2. Create bucket named "user-documents"
3. Set as private bucket
4. Configure upload policies:
   ```sql
   -- Allow authenticated users to upload to their folder
   CREATE POLICY "Users can upload own files" ON storage.objects
   FOR INSERT WITH CHECK (
     auth.uid()::text = (storage.foldername(name))[1]
   );
   ```

#### Step 4: Environment Configuration
1. Get project credentials from Settings > API
2. Add to `.env` file:
   ```bash
   SUPABASE_URL=https://your-project-ref.supabase.co
   SUPABASE_ANON_KEY=your_anon_key_here
   SUPABASE_SERVICE_KEY=your_service_role_key_here
   ```

#### Step 5: Test Connection
```bash
# Start the application
python main.py

# Check health endpoint
curl http://localhost:8000/health
# Should show "storage_backend": "supabase"
```

## Switching Between Storage Backends

### Automatic Detection
```python
def get_storage_service() -> StorageService:
    """Factory function to get appropriate storage service"""
    
    # Check if Supabase is configured
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if supabase_url and supabase_key:
        logger.info("Using Supabase storage")
        return SupabaseStorageService(supabase_url, supabase_key)
    else:
        logger.info("Using local storage")
        return LocalStorageService(
            backup_file=os.getenv("LOCAL_STORAGE_BACKUP")
        )
```

### Manual Override
```python
# Force local storage for testing
storage = LocalStorageService()

# Force Supabase for production
storage = SupabaseStorageService(url, key)
```

## Data Migration

### Local to Supabase
```python
async def migrate_local_to_supabase():
    """Migrate data from local storage to Supabase"""
    
    # Load local data
    local_storage = LocalStorageService(backup_file="data/backup.json")
    
    # Initialize Supabase
    supabase_storage = SupabaseStorageService(url, key)
    
    # Migrate users
    for user_id, user_data in local_storage.users.items():
        await supabase_storage.create_user(user_data)
    
    # Migrate files
    for doc_id, doc_data in local_storage.documents.items():
        # Upload file to Supabase Storage
        # Update file path in document record
```

### Backup and Restore
```python
# Backup Supabase data
async def backup_supabase_data():
    """Export all data from Supabase"""
    supabase = SupabaseStorageService(url, key)
    
    backup_data = {
        "users": await supabase.get_all_users(),
        "documents": await supabase.get_all_documents(),
        "sessions": await supabase.get_all_sessions()
    }
    
    with open("backup.json", "w") as f:
        json.dump(backup_data, f, indent=2)
```

## Performance Considerations

### Local Storage
- **Memory Usage**: Scales linearly with data size
- **File I/O**: Direct filesystem access (fast)
- **Concurrency**: Single-threaded access only
- **Backup Size**: JSON file grows with data

### Supabase Storage
- **Connection Pooling**: Automatic connection management
- **Query Optimization**: Use indexes and efficient queries
- **File CDN**: Global distribution for fast access
- **Caching**: Consider Redis layer for frequent queries

## Monitoring and Debugging

### Local Storage
```python
# Debug local storage state
def debug_local_storage(storage: LocalStorageService):
    print(f"Users: {len(storage.users)}")
    print(f"Sessions: {len(storage.sessions)}")
    print(f"Documents: {len(storage.documents)}")
    print(f"Temp dir: {storage.temp_dir}")
```

### Supabase Storage
- **Dashboard Monitoring**: Built-in metrics and logs
- **Query Performance**: Slow query detection
- **Storage Usage**: File storage and bandwidth metrics
- **Error Tracking**: Automatic error logging

## Best Practices

### Development
1. Use local storage for rapid prototyping
2. Enable backup for important test data
3. Clean up temporary files regularly
4. Test with realistic data volumes

### Production
1. Always use Supabase for production
2. Set up monitoring and alerts
3. Configure Row Level Security policies
4. Implement proper file cleanup procedures
5. Monitor storage costs and usage
6. Regular database maintenance

### Migration
1. Test migration process thoroughly
2. Backup data before migration
3. Verify data integrity after migration
4. Plan for downtime during migration
5. Have rollback procedure ready

This storage architecture provides flexibility for development while ensuring production readiness when needed.