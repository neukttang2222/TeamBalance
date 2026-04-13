-- Phase 1 canonical migration for task versioning, score lock, bonus log, and activity log.
-- Target DB: PostgreSQL / Supabase Postgres.
--
-- This file is intentionally bootstrap-safe and additive:
-- 1. Creates the current `tasks` baseline if it does not exist.
-- 2. Adds phase 1 columns with `IF NOT EXISTS` for existing MVP databases.
-- 3. Creates supporting phase 1 tables and indexes with `IF NOT EXISTS`.
--
-- Runtime auto-init in `app/db/session.py` should be treated as a local/dev safety net.
-- Shared/staging/production deployments should treat this migration file as the canonical schema path.

CREATE TABLE IF NOT EXISTS tasks (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255),
    user_name VARCHAR(255),
    creator_user_id VARCHAR(255),
    title VARCHAR(255) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    task_goal TEXT NOT NULL,
    task_weight INTEGER NOT NULL,
    status VARCHAR(32) NOT NULL,
    work_status VARCHAR(32) NOT NULL DEFAULT 'IN_PROGRESS',
    score_lock_status VARCHAR(32) NOT NULL DEFAULT 'UNLOCKED',
    base_points DOUBLE PRECISION NOT NULL DEFAULT 0,
    locked_main_score DOUBLE PRECISION,
    total_delta_bonus DOUBLE PRECISION NOT NULL DEFAULT 0,
    approved_version_no INTEGER,
    approved_submission_id VARCHAR(36),
    approved_by VARCHAR(255),
    approved_at TIMESTAMP,
    closed_by VARCHAR(255),
    closed_at TIMESTAMP,
    canceled_by VARCHAR(255),
    canceled_at TIMESTAMP,
    content TEXT,
    ai_question TEXT,
    user_answer TEXT,
    raw_score INTEGER,
    weighted_score INTEGER,
    ai_comment TEXT,
    failed_stage VARCHAR(32),
    error_message TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    submitted_at TIMESTAMP,
    scored_at TIMESTAMP
);

ALTER TABLE tasks ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS user_name VARCHAR(255);
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS creator_user_id VARCHAR(255);
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS work_status VARCHAR(32) NOT NULL DEFAULT 'IN_PROGRESS';
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS score_lock_status VARCHAR(32) NOT NULL DEFAULT 'UNLOCKED';
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS base_points DOUBLE PRECISION NOT NULL DEFAULT 0;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS locked_main_score DOUBLE PRECISION;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS total_delta_bonus DOUBLE PRECISION NOT NULL DEFAULT 0;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS approved_version_no INTEGER;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS approved_submission_id VARCHAR(36);
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS approved_by VARCHAR(255);
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS closed_by VARCHAR(255);
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS closed_at TIMESTAMP;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS canceled_by VARCHAR(255);
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS canceled_at TIMESTAMP;

CREATE INDEX IF NOT EXISTS ix_tasks_project_id_status ON tasks (project_id, status);
CREATE INDEX IF NOT EXISTS ix_tasks_project_id_work_status ON tasks (project_id, work_status);

CREATE TABLE IF NOT EXISTS task_submissions (
    id VARCHAR(36) PRIMARY KEY,
    task_id VARCHAR(36) NOT NULL,
    version_no INTEGER NOT NULL,
    submission_content TEXT,
    submission_note TEXT,
    evaluation_status VARCHAR(32) NOT NULL,
    ai_question TEXT,
    user_answer TEXT,
    raw_score INTEGER,
    ai_factor DOUBLE PRECISION,
    provisional_score DOUBLE PRECISION,
    ai_comment TEXT,
    failed_stage VARCHAR(32),
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    submitted_by VARCHAR(255),
    submitted_at TIMESTAMP NOT NULL,
    question_generated_at TIMESTAMP,
    answered_at TIMESTAMP,
    scored_at TIMESTAMP,
    last_retried_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_task_submissions_task_version ON task_submissions (task_id, version_no);
CREATE INDEX IF NOT EXISTS ix_task_submissions_task_id_version_no ON task_submissions (task_id, version_no);
CREATE INDEX IF NOT EXISTS ix_task_submissions_task_id_evaluation_status ON task_submissions (task_id, evaluation_status);

CREATE TABLE IF NOT EXISTS task_bonus_logs (
    id VARCHAR(36) PRIMARY KEY,
    task_id VARCHAR(36) NOT NULL,
    submission_id VARCHAR(36),
    version_no INTEGER,
    bonus_points DOUBLE PRECISION NOT NULL,
    reason_code VARCHAR(32) NOT NULL,
    reason_detail TEXT,
    approved_by VARCHAR(255),
    approved_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_task_bonus_logs_task_id_created_at ON task_bonus_logs (task_id, created_at);

CREATE TABLE IF NOT EXISTS task_activity_logs (
    id VARCHAR(36) PRIMARY KEY,
    task_id VARCHAR(36) NOT NULL,
    submission_id VARCHAR(36),
    actor_user_id VARCHAR(255),
    action_type VARCHAR(32) NOT NULL,
    from_work_status VARCHAR(32),
    to_work_status VARCHAR(32),
    from_score_lock_status VARCHAR(32),
    to_score_lock_status VARCHAR(32),
    metadata TEXT,
    created_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_task_activity_logs_task_id_created_at ON task_activity_logs (task_id, created_at);
CREATE INDEX IF NOT EXISTS ix_task_activity_logs_submission_id ON task_activity_logs (submission_id);
CREATE INDEX IF NOT EXISTS ix_task_activity_logs_action_type ON task_activity_logs (action_type, created_at);
