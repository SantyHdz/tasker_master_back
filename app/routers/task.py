from fastapi import APIRouter, Depends, HTTPException, Header, Response
from sqlalchemy.orm import Session, joinedload
from uuid import UUID
from datetime import datetime, timedelta

from app.database import get_db
from app.models.task import Task
from app.models.user import User
from app.models.priority import Priority
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.schemas.notification import PendingNotificationsResponse, UserNotification
from app.utils.deps import get_current_user
from app.utils.datetime_utils import ensure_timezone_aware, get_current_utc
from app.utils.security import verify_n8n_api_key

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={
        400: {"description": "Bad Request - Invalid input or priority_id"},
        401: {"description": "Unauthorized - Invalid or missing authentication"},
        404: {"description": "Not Found - Task not found"},
        422: {"description": "Unprocessable Entity - Validation error"}
    }
)


@router.post(
    "/",
    response_model=TaskResponse,
    status_code=200,
    summary="Create a new task",
    description="Create a new task for the authenticated user. Tasks can have a title, description, priority, and optional due date. The due date triggers automatic notifications at 24h, 1h, and 10 minutes before the event.",
    responses={
        200: {
            "description": "Task successfully created",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "title": "Complete project report",
                        "description": "Finish the quarterly report and submit to management",
                        "priority_id": 3,
                        "is_completed": False,
                        "due_date": "2026-05-10T14:00:00Z",
                        "notified_24h": False,
                        "notified_1h": False,
                        "notified_10m": False,
                        "created_at": "2026-05-05T10:00:00Z",
                        "updated_at": "2026-05-05T10:00:00Z"
                    }
                }
            }
        }
    }
)
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Create a new task for the authenticated user.

    - **title**: Task title (required, max 200 characters)
    - **description**: Task description (optional, max 1000 characters)
    - **priority_id**: Priority level ID (required, must be valid: 1=Low, 2=Medium, 3=High)
    - **due_date**: Optional due date in ISO 8601 format (triggers notifications)

    Returns the created task with all fields including timestamps.
    """
    # Validate priority_id exists
    priority = db.query(Priority).filter(Priority.id == task.priority_id).first()
    if not priority:
        raise HTTPException(status_code=400, detail="Invalid priority_id")

    db_task = Task(
        title=task.title,
        description=task.description,
        priority_id=task.priority_id,
        due_date=ensure_timezone_aware(task.due_date),
        user_id=current_user.id,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.get(
    "/",
    response_model=list[TaskResponse],
    summary="Get user's tasks",
    description="Retrieve all tasks for the authenticated user with optional filtering, search, and pagination. Results are ordered by creation date (newest first). Pagination metadata is returned in response headers.",
    responses={
        200: {
            "description": "Tasks retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "550e8400-e29b-41d4-a716-446655440000",
                            "title": "Complete project report",
                            "description": "Finish the quarterly report",
                            "priority_id": 3,
                            "is_completed": False,
                            "due_date": "2026-05-10T14:00:00Z",
                            "notified_24h": False,
                            "notified_1h": False,
                            "notified_10m": False,
                            "created_at": "2026-05-05T10:00:00Z",
                            "updated_at": "2026-05-05T10:00:00Z"
                        }
                    ]
                }
            }
        }
    }
)
def get_tasks(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    skip: int = 0,
    limit: int = 20,  # Reduced from 100 for better pagination
    is_completed: bool | None = None,
    priority_id: int | None = None,
    search: str | None = None,
    response: Response = None,
):
    """
    Retrieve tasks for the authenticated user with optional filtering.

    - **skip**: Number of tasks to skip (for pagination, default: 0)
    - **limit**: Maximum number of tasks to return (default: 20, max: 100)
    - **is_completed**: Filter by completion status (optional)
    - **priority_id**: Filter by priority level (optional)
    - **search**: Search in title and description (case-insensitive, optional)

    Returns a list of tasks ordered by creation date (newest first).
    Pagination metadata is included in response headers:
    - X-Total-Count: Total number of tasks matching the query
    - X-Page-Size: Number of tasks per page
    """
    query = db.query(Task).filter(Task.user_id == current_user.id)

    if is_completed is not None:
        query = query.filter(Task.is_completed == is_completed)

    if priority_id is not None:
        query = query.filter(Task.priority_id == priority_id)

    if search:
        # Search in title and description
        search_pattern = f"%{search}%"
        query = query.filter(
            (Task.title.ilike(search_pattern)) |
            (Task.description.ilike(search_pattern))
        )

    # Get total count for pagination metadata
    total_count = query.count()

    # Get paginated results
    tasks = query.order_by(Task.created_at.desc()).offset(skip).limit(limit).all()

    # Add pagination metadata to response headers
    if response:
        response.headers["X-Total-Count"] = str(total_count)
        response.headers["X-Page-Size"] = str(limit)

    return tasks


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get a specific task",
    description="Retrieve a single task by ID. Only returns tasks that belong to the authenticated user.",
    responses={
        200: {
            "description": "Task retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "title": "Complete project report",
                        "description": "Finish the quarterly report",
                        "priority_id": 3,
                        "is_completed": False,
                        "due_date": "2026-05-10T14:00:00Z",
                        "notified_24h": False,
                        "notified_1h": False,
                        "notified_10m": False,
                        "created_at": "2026-05-05T10:00:00Z",
                        "updated_at": "2026-05-05T10:00:00Z"
                    }
                }
            }
        },
        404: {
            "description": "Task not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Task not found"}
                }
            }
        }
    }
)
def get_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Retrieve a specific task by ID.

    - **task_id**: UUID of the task to retrieve

    Returns the task if it exists and belongs to the authenticated user.
    """
    task = db.query(Task).filter(
        Task.id == task_id, Task.user_id == current_user.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update a task",
    description="Update an existing task. Only updates fields that are provided in the request body. The task must belong to the authenticated user.",
    responses={
        200: {
            "description": "Task updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "title": "Updated task title",
                        "description": "Updated description",
                        "priority_id": 2,
                        "is_completed": True,
                        "due_date": "2026-05-10T14:00:00Z",
                        "notified_24h": True,
                        "notified_1h": True,
                        "notified_10m": False,
                        "created_at": "2026-05-05T10:00:00Z",
                        "updated_at": "2026-05-05T12:00:00Z"
                    }
                }
            }
        },
        404: {
            "description": "Task not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Task not found"}
                }
            }
        }
    }
)
def update_task(
    task_id: UUID,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Update an existing task.

    - **task_id**: UUID of the task to update
    - **task_update**: Partial update object with fields to modify

    Only updates fields that are provided. All fields are optional.
    """
    task = db.query(Task).filter(
        Task.id == task_id, Task.user_id == current_user.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    for key, value in task_update.model_dump(exclude_unset=True).items():
        if key == 'due_date':
            value = ensure_timezone_aware(value)
        setattr(task, key, value)

    db.commit()
    db.refresh(task)
    return task


@router.patch(
    "/{task_id}/toggle",
    response_model=TaskResponse,
    summary="Toggle task completion",
    description="Toggle the completion status of a task. This is a convenience endpoint for quickly marking tasks as complete/incomplete via checkbox interactions.",
    responses={
        200: {
            "description": "Task completion toggled successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "title": "Complete project report",
                        "description": "Finish the quarterly report",
                        "priority_id": 3,
                        "is_completed": True,
                        "due_date": "2026-05-10T14:00:00Z",
                        "notified_24h": False,
                        "notified_1h": False,
                        "notified_10m": False,
                        "created_at": "2026-05-05T10:00:00Z",
                        "updated_at": "2026-05-05T12:00:00Z"
                    }
                }
            }
        },
        404: {
            "description": "Task not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Task not found"}
                }
            }
        }
    }
)
def toggle_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Toggle the completion status of a task.

    - **task_id**: UUID of the task to toggle

    Flips the is_completed field between True and False.
    """
    task = db.query(Task).filter(
        Task.id == task_id, Task.user_id == current_user.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.is_completed = not task.is_completed
    db.commit()
    db.refresh(task)
    return task


@router.delete(
    "/{task_id}",
    status_code=200,
    summary="Delete a task",
    description="Permanently delete a task. This action cannot be undone. The task must belong to the authenticated user.",
    responses={
        200: {
            "description": "Task deleted successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Task deleted"}
                }
            }
        },
        404: {
            "description": "Task not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Task not found"}
                }
            }
        }
    }
)
def delete_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Permanently delete a task.

    - **task_id**: UUID of the task to delete

    Returns a confirmation message. This action cannot be undone.
    """
    task = db.query(Task).filter(
        Task.id == task_id, Task.user_id == current_user.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return {"message": "Task deleted"}


@router.get(
    "/notifications/pending",
    summary="Get pending notifications",
    description="Retrieve tasks that need notifications for the n8n workflow. Returns tasks where due_date is approaching (24h, 1h, or 10 minutes) and notification flags are not set. Requires API key authentication via X-API-Key header.",
    responses={
        200: {
            "description": "Pending notifications retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "24h": [
                            {
                                "id": "550e8400-e29b-41d4-a716-446655440000",
                                "title": "Complete project report",
                                "description": "Finish the quarterly report",
                                "priority_id": 3,
                                "is_completed": False,
                                "due_date": "2026-05-10T14:00:00Z",
                                "notified_24h": False,
                                "notified_1h": False,
                                "notified_10m": False,
                                "created_at": "2026-05-05T10:00:00Z",
                                "updated_at": "2026-05-05T10:00:00Z"
                            }
                        ],
                        "1h": [],
                        "10m": [],
                        "current_time": "2026-05-05T10:00:00Z"
                    }
                }
            }
        },
        401: {
            "description": "Unauthorized - Invalid or missing API key",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid API key"}
                }
            }
        }
    }
)
def get_pending_notifications(
    db: Session = Depends(get_db),
    x_api_key: str = Header(None, description="API key for n8n authentication")
):
    """
    Get tasks that need notifications for the n8n workflow, grouped by user and Telegram chat ID.

    This endpoint checks for tasks that are due within specific time windows:
    - 24 hours (±1 hour window)
    - 1 hour (±5 minutes window)
    - 10 minutes (±2 minutes window)

    Only returns tasks where the corresponding notification flag is not set and users have telegram_chat_id configured.

    - **x_api_key**: API key for authentication (required)

    Returns tasks grouped by user/telegram_chat_id with notification time windows.
    """
    # Verify API key
    if not x_api_key or not verify_n8n_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")

    current_time = get_current_utc()
    users_data = {}

    # Tasks due in 24 hours (±1 hour window) that haven't been notified
    tasks_24h = db.query(Task).options(joinedload(Task.user)).join(User).filter(
        Task.user_id == User.id,
        Task.due_date.isnot(None),
        Task.is_completed == False,
        Task.notified_24h == False,
        Task.due_date >= current_time + timedelta(hours=23),
        Task.due_date <= current_time + timedelta(hours=25),
        User.telegram_chat_id.isnot(None)
    ).all()

    # Tasks due in 1 hour (±5 minutes window) that haven't been notified
    tasks_1h = db.query(Task).options(joinedload(Task.user)).join(User).filter(
        Task.user_id == User.id,
        Task.due_date.isnot(None),
        Task.is_completed == False,
        Task.notified_1h == False,
        Task.due_date >= current_time + timedelta(minutes=55),
        Task.due_date <= current_time + timedelta(minutes=65),
        User.telegram_chat_id.isnot(None)
    ).all()

    # Tasks due in 10 minutes (±2 minutes window) that haven't been notified
    tasks_10m = db.query(Task).options(joinedload(Task.user)).join(User).filter(
        Task.user_id == User.id,
        Task.due_date.isnot(None),
        Task.is_completed == False,
        Task.notified_10m == False,
        Task.due_date >= current_time + timedelta(minutes=8),
        Task.due_date <= current_time + timedelta(minutes=12),
        User.telegram_chat_id.isnot(None)
    ).all()

    # Group tasks by user/telegram_chat_id
    for task in tasks_24h:
        user_key = f"{task.user_id}:{task.user.telegram_chat_id}"
        if user_key not in users_data:
            users_data[user_key] = {
                "telegram_chat_id": task.user.telegram_chat_id,
                "user_id": task.user_id,
                "tasks": {"24h": [], "1h": [], "10m": []}
            }
        users_data[user_key]["tasks"]["24h"].append(TaskResponse.model_validate(task))

    for task in tasks_1h:
        user_key = f"{task.user_id}:{task.user.telegram_chat_id}"
        if user_key not in users_data:
            users_data[user_key] = {
                "telegram_chat_id": task.user.telegram_chat_id,
                "user_id": task.user_id,
                "tasks": {"24h": [], "1h": [], "10m": []}
            }
        users_data[user_key]["tasks"]["1h"].append(TaskResponse.model_validate(task))

    for task in tasks_10m:
        user_key = f"{task.user_id}:{task.user.telegram_chat_id}"
        if user_key not in users_data:
            users_data[user_key] = {
                "telegram_chat_id": task.user.telegram_chat_id,
                "user_id": task.user_id,
                "tasks": {"24h": [], "1h": [], "10m": []}
            }
        users_data[user_key]["tasks"]["10m"].append(TaskResponse.model_validate(task))

    # Convert to list format for response
    users_list = list(users_data.values())

    return PendingNotificationsResponse(users=users_list, current_time=current_time.isoformat())


@router.patch(
    "/{task_id}/notifications/{notification_type}",
    summary="Mark notification as sent",
    description="Mark a notification as sent for a specific task. This is used by the n8n workflow to track which notifications have been delivered. Requires API key authentication via X-API-Key header.",
    responses={
        200: {
            "description": "Notification marked as sent successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Notification 24h marked as sent",
                        "task": {
                            "id": "550e8400-e29b-41d4-a716-446655440000",
                            "title": "Complete project report",
                            "description": "Finish the quarterly report",
                            "priority_id": 3,
                            "is_completed": False,
                            "due_date": "2026-05-10T14:00:00Z",
                            "notified_24h": True,
                            "notified_1h": False,
                            "notified_10m": False,
                            "created_at": "2026-05-05T10:00:00Z",
                            "updated_at": "2026-05-05T10:00:00Z"
                        }
                    }
                }
            }
        },
        400: {
            "description": "Bad Request - Invalid notification type",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid notification type. Must be '24h', '1h', or '10m'"}
                }
            }
        },
        401: {
            "description": "Unauthorized - Invalid or missing API key",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid API key"}
                }
            }
        },
        404: {
            "description": "Task not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Task not found"}
                }
            }
        }
    }
)
def mark_notification_sent(
    task_id: UUID,
    notification_type: str,
    db: Session = Depends(get_db),
    x_api_key: str = Header(None, description="API key for n8n authentication")
):
    """
    Mark a notification as sent for a specific task.

    This endpoint is used by the n8n workflow to track which notifications have been delivered.

    - **task_id**: UUID of the task
    - **notification_type**: Type of notification to mark (must be '24h', '1h', or '10m')
    - **x_api_key**: API key for authentication (required)

    Returns a confirmation message and the updated task.
    """
    # Verify API key
    if not x_api_key or not verify_n8n_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if notification_type == "24h":
        task.notified_24h = True
    elif notification_type == "1h":
        task.notified_1h = True
    elif notification_type == "10m":
        task.notified_10m = True
    else:
        raise HTTPException(status_code=400, detail="Invalid notification type. Must be '24h', '1h', or '10m'")

    db.commit()
    db.refresh(task)
    return {"message": f"Notification {notification_type} marked as sent", "task": TaskResponse.model_validate(task)}