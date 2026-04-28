-- EXTENSIONES
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =========================
-- TABLA: users
-- =========================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- TABLA: priorities
-- =========================
CREATE TABLE priorities (
    id SMALLINT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- Datos iniciales (seed)
INSERT INTO priorities (id, name) VALUES
(1, 'Low'),
(2, 'Medium'),
(3, 'High');

-- =========================
-- TABLA: tasks
-- =========================
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT,
    priority_id SMALLINT NOT NULL,
    due_date TIMESTAMP WITH TIME ZONE,
    is_completed BOOLEAN DEFAULT FALSE,
    user_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_user
        FOREIGN KEY(user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_priority
        FOREIGN KEY(priority_id)
        REFERENCES priorities(id)
		ON DELETE RESTRICT
);

-- =========================
-- ÍNDICES (rendimiento)
-- =========================

-- Buscar tareas por usuario rápido
CREATE INDEX idx_tasks_user_id ON tasks(user_id);

-- Para filtros por estado
CREATE INDEX idx_tasks_completed ON tasks(is_completed);

-- Para automatización (n8n: tareas próximas)
CREATE INDEX idx_tasks_due_date ON tasks(due_date);

-- Índice compuesto (muy útil)
CREATE INDEX idx_tasks_user_due ON tasks(user_id, due_date);

UPDATE tasks
SET notified = false
WHERE title = 'Revisar correos urgentes';


ALTER TABLE tasks
ADD COLUMN notified_24h BOOLEAN DEFAULT FALSE,
ADD COLUMN notified_1h BOOLEAN DEFAULT FALSE,
ADD COLUMN notified_10m BOOLEAN DEFAULT FALSE;

UPDATE tasks
SET due_date = NOW() + INTERVAL '2 hours'
WHERE title = 'Aprender FastAPI';

select * from users;