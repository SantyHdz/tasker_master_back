from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.utils.deps import get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])


# Crear tarea
@router.post("/", response_model=TaskResponse)
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    db_task = Task(
        title=task.title,
        description=task.description,
        priority_id=task.priority_id,
        due_date=task.due_date,
        user_id=current_user.id
    )

    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    return db_task


# Obtener todas tus tareas
@router.get("/", response_model=list[TaskResponse])
def get_tasks(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),

    # PAGINACIÓN
    skip: int = 0,
    limit: int = 10,

    # FILTROS
    is_completed: bool | None = None,
    priority_id: int | None = None
):
    query = db.query(Task).filter(Task.user_id == current_user.id)

    if is_completed is not None:
        query = query.filter(Task.is_completed == is_completed)

    if priority_id is not None:
        query = query.filter(Task.priority_id == priority_id)

    tasks = query.offset(skip).limit(limit).all()

    return tasks


# Obtener una tarea por ID
@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


# Actualizar tarea
@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: UUID,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    for key, value in task_update.model_dump(exclude_unset=True).items():
        setattr(task, key, value)

    db.commit()
    db.refresh(task)

    return task


# Eliminar tarea
@router.delete("/{task_id}")
def delete_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()

    return {"message": "Task deleted"}