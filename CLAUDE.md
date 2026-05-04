# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Tasker Master is a FastAPI-based task management API with PostgreSQL backend (Supabase). It provides user authentication, task CRUD operations, and priority-based task organization with notification tracking for n8n integration.

## Architecture

### Layer Structure
- **app/main.py**: FastAPI application entry point with CORS middleware and router registration
- **app/database.py**: SQLAlchemy database configuration and session management
- **app/models/**: SQLAlchemy ORM models (User, Task, Priority)
- **app/schemas/**: Pydantic schemas for request/response validation
- **app/routers/**: API route handlers organized by domain (auth, tasks, users, health)
- **app/utils/**: Utility functions (security, dependencies, datetime handling)
- **app/services/**: Currently empty, reserved for business logic layer

### Database Models
- **User**: UUID primary key, email (unique), password_hash, name, created_at
- **Task**: UUID primary key, title, description, priority_id (FK), due_date, is_completed, user_id (FK), created_at, plus notification tracking fields (notified_24h, notified_1h, notified_10m)
- **Priority**: SmallInteger primary key, name (unique)

### Authentication Flow
1. JWT-based authentication using python-jose
2. Password hashing with bcrypt
3. OAuth2PasswordBearer scheme with tokenUrl="auth/login"
4. Protected routes use `get_current_user` dependency from app/utils/deps.py
5. Token includes user ID in "sub" claim

## Common Development Commands

### Running the Application
```bash
# Start the development server
uvicorn app.main:app --reload

# Start with specific host/port
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Create virtual environment (if needed)
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

### Database
- Database URL configured in .env file
- Uses PostgreSQL with psycopg2-binary
- SQLAlchemy handles ORM and migrations
- Current database: Supabase PostgreSQL instance

## API Structure

### Endpoints
- **POST /auth/register**: User registration, returns JWT token
- **POST /auth/login**: User login, returns JWT token
- **GET /users/me**: Get current user info (protected)
- **POST /users/**: Create user (alternative to register)
- **GET /tasks/**: List tasks with filtering (is_completed, priority_id), pagination (skip, limit)
- **POST /tasks/**: Create task (protected)
- **GET /tasks/{task_id}**: Get specific task (protected)
- **PUT /tasks/{task_id}**: Update task (protected)
- **PATCH /tasks/{task_id}/toggle**: Toggle task completion status (protected)
- **DELETE /tasks/{task_id}**: Delete task (protected)
- **GET /tasks/notifications/pending**: Get tasks needing notifications (for n8n)
- **PATCH /tasks/{task_id}/notifications/{notification_type}**: Mark notification as sent (for n8n)
- **GET /**: Root endpoint
- **GET /health**: Health check endpoint with database status

### Request/Response Patterns
- All task endpoints require authentication via `get_current_user` dependency
- Tasks are scoped to current_user.id (user isolation)
- Pydantic schemas validate input and serialize output
- Response models use `from_attributes = True` for ORM compatibility

## Key Patterns

### Database Operations
- Use `db.query(Model).filter(...)` for queries
- Always commit after modifications: `db.commit()`
- Refresh after commit to get updated values: `db.refresh(db_obj)`
- Use `Session = Depends(get_db)` dependency for database access

### Authentication
- Protected routes must include `current_user=Depends(get_current_user)` parameter
- User isolation: always filter by `current_user.id` in queries
- Token validation handled automatically by OAuth2PasswordBearer

### Error Handling
- Use HTTPException for API errors
- 400 for validation/invalid input
- 401 for authentication failures
- 404 for resource not found

### Task Updates
- Use `model_dump(exclude_unset=True)` for partial updates
- Iterate over dict to update only provided fields
- Example: `for key, value in task_update.model_dump(exclude_unset=True).items(): setattr(task, key, value)`

### Timezone Handling
- All datetime fields must be timezone-aware
- Use `ensure_timezone_aware()` from app/utils/datetime_utils.py for conversion
- API stores and returns times in UTC
- Pydantic validators enforce timezone-aware datetimes
- JWT tokens use `datetime.now(timezone.utc)` instead of deprecated `datetime.utcnow()`

## Recent Changes

### Notification Tracking & N8N Integration
The Task model has been extended with notification tracking fields for n8n integration:
- `notified_24h`: Boolean flag for 24-hour advance notifications
- `notified_1h`: Boolean flag for 1-hour advance notifications
- `notified_10m`: Boolean flag for 10-minute advance notifications

These fields use `server_default="false"` and are nullable=False to ensure proper tracking.

### New N8N Endpoints
- **GET /tasks/notifications/pending**: Returns tasks needing notifications in time windows (24h, 1h, 10m)
- **PATCH /tasks/{task_id}/notifications/{type}**: Marks notifications as sent

### Code Quality Improvements
- Fixed duplicate `toggle_task` endpoint definition
- Added timezone-aware datetime handling throughout the application
- Improved password validation (minimum 8 characters)
- Enhanced database connection validation in health check
- Added proper string length constraints to model fields
- Improved error messages and API documentation
- Fixed deprecated `datetime.utcnow()` usage in JWT token creation
- Added `__repr__` methods to models for better debugging
- Removed unused imports and cleaned up database configuration

## Known Issues

- No test suite currently implemented
- No database migration system (Alembic) configured
- N8N workflow needs to be configured (see N8N_WORKFLOW_GUIDE.md)