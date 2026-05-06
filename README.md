# 🗂️ Tasker Master — Backend API

<div align="center">

![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-Auth-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white)
![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)

**API REST para gestión de tareas con autenticación JWT y automatización de notificaciones vía n8n + Telegram.**

[Endpoints](#-endpoints) · [Instalación](#-instalación) · [Variables de entorno](#-variables-de-entorno) · [Base de datos](#-base-de-datos) · [n8n Integration](#-integración-con-n8n)

</div>

---

## 📋 Tabla de contenidos

- [Descripción general](#-descripción-general)
- [Arquitectura del sistema](#-arquitectura-del-sistema)
- [Stack tecnológico](#-stack-tecnológico)
- [Estructura del proyecto](#-estructura-del-proyecto)
- [Base de datos](#-base-de-datos)
- [Instalación local](#-instalación-local)
- [Variables de entorno](#-variables-de-entorno)
- [Endpoints](#-endpoints)
- [Autenticación](#-autenticación)
- [Integración con n8n](#-integración-con-n8n)
- [Rate Limiting](#-rate-limiting)
- [Deploy en Render](#-deploy-en-render)

---

## 📖 Descripción general

El backend de **Tasker Master** es una API REST construida con **FastAPI** que provee:

- ✅ Registro y login de usuarios con JWT
- ✅ CRUD completo de tareas con prioridades y fechas límite
- ✅ Sistema de notificaciones con tracking por ventanas de tiempo (24h, 1h, 10min)
- ✅ Endpoint dedicado para integración con flujos de **n8n**
- ✅ Rate limiting para protección contra abuso
- ✅ Health check con verificación de conexión a base de datos

---

## 🏗️ Arquitectura del sistema

```
Usuario
  ↓
Frontend (Next.js — Vercel)
  ↓
Backend API (FastAPI — Render)   ← estás aquí
  ↓
Database (PostgreSQL — Supabase)
  ↓
n8n (Railway)
  ↓
Telegram Bot
```

---

## 🛠️ Stack tecnológico

| Tecnología | Rol | Versión |
|---|---|---|
| **FastAPI** | Framework principal | 0.100+ |
| **SQLAlchemy** | ORM | 2.0+ |
| **PostgreSQL** | Base de datos | 15+ |
| **python-jose** | Manejo de JWT | latest |
| **bcrypt** | Hash de contraseñas | latest |
| **slowapi** | Rate limiting | latest |
| **Pydantic** | Validación de datos | v2 |
| **python-dotenv** | Variables de entorno | latest |

---

## 📁 Estructura del proyecto

```
backend/
├── app/
│   ├── main.py                  # Entry point, CORS, rate limiting, routers
│   ├── database.py              # Conexión SQLAlchemy + sesión DB
│   ├── models/
│   │   ├── user.py              # Modelo User
│   │   ├── task.py              # Modelo Task (con columnas de notificación)
│   │   ├── priority.py          # Modelo Priority
│   │   └── scripts.sql          # Scripts SQL de creación e índices
│   ├── schemas/
│   │   ├── user.py              # Pydantic schemas: UserCreate, UserLogin, UserResponse
│   │   └── task.py              # Pydantic schemas: TaskCreate, TaskUpdate, TaskResponse
│   ├── routers/
│   │   ├── auth.py              # POST /auth/register, POST /auth/login
│   │   ├── user.py              # GET /users/me
│   │   ├── task.py              # CRUD /tasks + endpoints de notificación
│   │   └── health.py            # GET /health
│   └── utils/
│       ├── deps.py              # Dependency injection: get_current_user
│       ├── security.py          # JWT, bcrypt, API key n8n
│       └── datetime_utils.py    # Helpers de timezone UTC
├── .env                         # Variables de entorno (no commitear)
├── requirements.txt
└── README.md
```

---

## 🗄️ Base de datos

### Diagrama de tablas

```
┌─────────────────────┐       ┌──────────────────────────────────┐
│        users        │       │              tasks               │
├─────────────────────┤       ├──────────────────────────────────┤
│ id          UUID PK │◄──┐   │ id            UUID PK            │
│ email       TEXT    │   └───│ user_id       UUID FK → users.id │
│ password_hash TEXT  │       │ title         TEXT               │
│ name        TEXT    │       │ description   TEXT               │
│ created_at  TSTZ    │       │ priority_id   SMALLINT FK        │
└─────────────────────┘       │ due_date      TSTZ               │
                              │ is_completed  BOOLEAN            │
                              │ notified_24h  BOOLEAN            │
                              │ notified_1h   BOOLEAN            │
                              │ notified_10m  BOOLEAN            │
                              │ created_at    TSTZ               │
                              └──────────────────────────────────┘
                                          │
                              ┌───────────▼──────────┐
                              │       priorities     │
                              ├──────────────────────┤
                              │ id    SMALLINT PK    │
                              │ name  TEXT           │
                              ├──────────────────────┤
                              │ 1 → Low              │
                              │ 2 → Medium           │
                              │ 3 → High             │
                              └──────────────────────┘
```

### Índices

```sql
CREATE INDEX idx_tasks_user_id   ON tasks(user_id);
CREATE INDEX idx_tasks_completed ON tasks(is_completed);
CREATE INDEX idx_tasks_due_date  ON tasks(due_date);
CREATE INDEX idx_tasks_user_due  ON tasks(user_id, due_date);  -- compuesto
```

### Columnas de tracking de notificaciones

Las columnas `notified_24h`, `notified_1h` y `notified_10m` permiten que el workflow de n8n sepa cuáles notificaciones ya fueron enviadas, evitando duplicados:

```sql
ALTER TABLE tasks
ADD COLUMN notified_24h BOOLEAN DEFAULT FALSE,
ADD COLUMN notified_1h  BOOLEAN DEFAULT FALSE,
ADD COLUMN notified_10m BOOLEAN DEFAULT FALSE;
```

---

## ⚙️ Instalación local

### Requisitos previos

- Python 3.11+
- PostgreSQL 15+ (o cuenta en [Supabase](https://supabase.com))

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/tasker-master.git
cd tasker-master/backend

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate      # Linux/Mac
# venv\Scripts\activate       # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# 5. Crear las tablas en la base de datos
# Ejecutar app/models/scripts.sql en tu instancia de PostgreSQL

# 6. Levantar el servidor
uvicorn app.main:app --reload --port 8000
```

La API estará disponible en `http://localhost:8000`  
Documentación interactiva: `http://localhost:8000/docs`

---

## 🔐 Variables de entorno

Crea un archivo `.env` en la raíz del backend con los siguientes valores:

```env
# Base de datos
DATABASE_URL=postgresql://usuario:password@host:5432/nombre_db

# JWT
SECRET_KEY=tu_clave_secreta_super_segura_aqui

# CORS — separar con comas si son varios orígenes
ALLOWED_ORIGINS=http://localhost:3000,https://tu-app.vercel.app

# API Key para autenticar llamadas desde n8n
N8N_API_KEY=tu_api_key_para_n8n

# Entorno
ENV=development   # o "production"
```

> ⚠️ **Nunca subas el archivo `.env` al repositorio.** Asegúrate de tenerlo en `.gitignore`.

---

## 📡 Endpoints

### 🔑 Autenticación

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| `POST` | `/auth/register` | Registrar nuevo usuario | ❌ |
| `POST` | `/auth/login` | Login y obtener JWT | ❌ |

#### `POST /auth/register`

```json
// Request body
{
  "email": "usuario@ejemplo.com",
  "password": "contraseña123",
  "name": "Juan Pérez"
}

// Response 201
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

#### `POST /auth/login`

```json
// Request body
{
  "email": "usuario@ejemplo.com",
  "password": "contraseña123"
}

// Response 200
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

---

### 👤 Usuarios

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| `GET` | `/users/me` | Obtener datos del usuario actual | ✅ JWT |

---

### ✅ Tareas

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| `POST` | `/tasks/` | Crear tarea | ✅ JWT |
| `GET` | `/tasks/` | Listar tareas (con filtros y paginación) | ✅ JWT |
| `GET` | `/tasks/{task_id}` | Obtener tarea por ID | ✅ JWT |
| `PUT` | `/tasks/{task_id}` | Actualizar tarea | ✅ JWT |
| `PATCH` | `/tasks/{task_id}/toggle` | Cambiar estado completado | ✅ JWT |
| `DELETE` | `/tasks/{task_id}` | Eliminar tarea | ✅ JWT |

#### `POST /tasks/`

```json
// Request body
{
  "title": "Entregar reporte mensual",
  "description": "Incluir métricas de abril",
  "priority_id": 3,
  "due_date": "2026-05-10T14:00:00Z"
}

// Response 200
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Entregar reporte mensual",
  "description": "Incluir métricas de abril",
  "priority_id": 3,
  "is_completed": false,
  "due_date": "2026-05-10T14:00:00Z",
  "notified_24h": false,
  "notified_1h": false,
  "notified_10m": false,
  "created_at": "2026-05-06T10:00:00Z"
}
```

#### `GET /tasks/` — Query params disponibles

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `skip` | `int` | Offset para paginación (default: 0) |
| `limit` | `int` | Máximo de resultados (default: 20) |
| `is_completed` | `bool` | Filtrar por estado |
| `priority_id` | `int` | Filtrar por prioridad |
| `search` | `string` | Buscar en título y descripción |

> Los headers de respuesta incluyen `X-Total-Count` y `X-Page-Size` para paginación.

---

### 🔔 Notificaciones (para n8n)

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| `GET` | `/tasks/notifications/pending` | Obtener tareas pendientes de notificar | ✅ API Key |
| `PATCH` | `/tasks/{task_id}/notifications/{type}` | Marcar notificación como enviada | ✅ API Key |

Estos endpoints usan autenticación por **API Key** via header `X-API-Key`, no JWT.

#### `GET /tasks/notifications/pending`

```json
// Response 200
{
  "24h": [ /* tareas que vencen en ~24 horas */ ],
  "1h":  [ /* tareas que vencen en ~1 hora */ ],
  "10m": [ /* tareas que vencen en ~10 minutos */ ],
  "current_time": "2026-05-06T10:00:00Z"
}
```

#### `PATCH /tasks/{task_id}/notifications/{type}`

`type` puede ser: `24h`, `1h` o `10m`

```json
// Response 200
{
  "message": "Notification 24h marked as sent",
  "task": { /* TaskResponse */ }
}
```

---

### 🏥 Health Check

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/health` | Estado del servidor y base de datos |

```json
// Response 200
{
  "status": "ok",
  "version": "1.0.0",
  "database": "healthy"
}
```

---

## 🔒 Autenticación

La API usa **JWT (JSON Web Tokens)** con el algoritmo `HS256`.

- Los tokens tienen una expiración de **60 minutos**
- Para acceder a rutas protegidas, incluir el header:

```
Authorization: Bearer <token>
```

El flujo completo:

```
Cliente → POST /auth/login → Recibe JWT
Cliente → GET /tasks/ + Authorization: Bearer <JWT> → Datos del usuario
```

---

## 🤖 Integración con n8n

El sistema incluye un mecanismo de notificaciones diseñado para integrarse con **n8n** y enviar alertas por **Telegram**.

### Ventanas de tiempo

| Ventana | Tolerancia | Campo en DB |
|---------|-----------|-------------|
| 24 horas | ± 1 hora | `notified_24h` |
| 1 hora | ± 5 minutos | `notified_1h` |
| 10 minutos | ± 2 minutos | `notified_10m` |

### Workflow sugerido en n8n

```
Trigger: Cron (cada 10 minutos)
  ↓
HTTP Request → GET /tasks/notifications/pending
  (Header: X-API-Key: <N8N_API_KEY>)
  ↓
IF → ¿Hay tareas en "10m", "1h" o "24h"?
  ↓
Telegram → Enviar mensaje con título y fecha límite
  ↓
HTTP Request → PATCH /tasks/{id}/notifications/{type}
  (Marcar como notificada para no reenviar)
```

### Autenticación desde n8n

Las llamadas desde n8n deben incluir el header:

```
X-API-Key: <valor de N8N_API_KEY en .env>
```

---

## 🛡️ Rate Limiting

El backend usa **slowapi** para proteger los endpoints de autenticación:

| Endpoint | Límite |
|----------|--------|
| `POST /auth/register` | 5 requests / minuto |
| `POST /auth/login` | 10 requests / minuto |

Al exceder el límite se retorna `HTTP 429 Too Many Requests`.

---

## 🚀 Deploy en Render

### Pasos

1. Crea un nuevo **Web Service** en [Render](https://render.com)
2. Conecta tu repositorio de GitHub
3. Configura:

| Campo | Valor |
|-------|-------|
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

4. Agrega las variables de entorno en el panel de Render:
   - `DATABASE_URL`
   - `SECRET_KEY`
   - `ALLOWED_ORIGINS`
   - `N8N_API_KEY`
   - `ENV=production`

> 💡 La base de datos PostgreSQL está en **Supabase** (gratuito), apuntada desde `DATABASE_URL`.

---

## 📊 Prioridades de tareas

| ID | Nombre | Uso |
|----|--------|-----|
| `1` | Low | Tareas de baja urgencia |
| `2` | Medium | Tareas normales |
| `3` | High | Tareas críticas o urgentes |

---

## 📝 Notas adicionales

- Todas las fechas se almacenan y retornan en **UTC con timezone** (`TIMESTAMP WITH TIME ZONE`)
- El campo `due_date` debe enviarse en formato **ISO 8601** con timezone, por ejemplo: `2026-05-10T14:00:00Z`
- Los passwords requieren mínimo **8 caracteres**
- Las tareas se ordenan por `created_at` descendente (más nuevas primero)
- El campo `user_id` se asigna automáticamente desde el JWT; no es necesario enviarlo en el body

---

<div align="center">

Hecho con ❤️ · **Tasker Master** © 2026

</div>
