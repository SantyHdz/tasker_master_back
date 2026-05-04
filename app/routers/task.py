from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timedelta

from app.database import get_db
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.utils.deps import get_current_user
from app.utils.datetime_utils import ensure_timezone_aware, get_current_utc

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse)
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
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


@router.get("/", response_model=list[TaskResponse])
def get_tasks(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,  # fixed: was 10
    is_completed: bool | None = None,
    priority_id: int | None = None,
):
    query = db.query(Task).filter(Task.user_id == current_user.id)

    if is_completed is not None:
        query = query.filter(Task.is_completed == is_completed)

    if priority_id is not None:
        query = query.filter(Task.priority_id == priority_id)

    return query.order_by(Task.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    task = db.query(Task).filter(
        Task.id == task_id, Task.user_id == current_user.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: UUID,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
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


@router.patch("/{task_id}/toggle", response_model=TaskResponse)
def toggle_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Toggle is_completed — used by the frontend checkbox."""
    task = db.query(Task).filter(
        Task.id == task_id, Task.user_id == current_user.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.is_completed = not task.is_completed
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}")
def delete_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    task = db.query(Task).filter(
        Task.id == task_id, Task.user_id == current_user.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return {"message": "Task deleted"}


@router.get("/notifications/pending")
def get_pending_notifications(
    db: Session = Depends(get_db),
):
    """
    Get tasks that need notifications.
    This endpoint is for n8n workflow to check which tasks need reminders.
    Returns tasks where due_date is approaching and notification flags are not set.
    """
    current_time = get_current_utc()

    # Tasks due in 24 hours (±1 hour window) that haven't been notified
    tasks_24h = db.query(Task).filter(
        Task.due_date.isnot(None),
        Task.is_completed == False,
        Task.notified_24h == False,
        Task.due_date >= current_time + timedelta(hours=23),
        Task.due_date <= current_time + timedelta(hours=25)
    ).all()

    # Tasks due in 1 hour (±5 minutes window) that haven't been notified
    tasks_1h = db.query(Task).filter(
        Task.due_date.isnot(None),
        Task.is_completed == False,
        Task.notified_1h == False,
        Task.due_date >= current_time + timedelta(minutes=55),
        Task.due_date <= current_time + timedelta(minutes=65)
    ).all()

    # Tasks due in 10 minutes (±2 minutes window) that haven't been notified
    tasks_10m = db.query(Task).filter(
        Task.due_date.isnot(None),
        Task.is_completed == False,
        Task.notified_10m == False,
        Task.due_date >= current_time + timedelta(minutes=8),
        Task.due_date <= current_time + timedelta(minutes=12)
    ).all()

    return {
        "24h": [TaskResponse.model_validate(task) for task in tasks_24h],
        "1h": [TaskResponse.model_validate(task) for task in tasks_1h],
        "10m": [TaskResponse.model_validate(task) for task in tasks_10m],
        "current_time": current_time.isoformat()
    }


@router.patch("/{task_id}/notifications/{notification_type}")
def mark_notification_sent(
    task_id: UUID,
    notification_type: str,
    db: Session = Depends(get_db),
):
    """
    Mark a notification as sent for a specific task.
    notification_type can be: '24h', '1h', '10m'
    This endpoint is for n8n workflow to mark notifications as sent.
    """
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