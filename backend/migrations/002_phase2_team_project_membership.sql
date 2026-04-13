-- Phase 2-1 additive migration for team, project, membership, and project-scoped task reads.
-- Target DB: PostgreSQL / Supabase Postgres.

CREATE TABLE IF NOT EXISTS teams (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_by VARCHAR(255),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS team_members (
    id VARCHAR(36) PRIMARY KEY,
    team_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    team_role VARCHAR(32),
    joined_at TIMESTAMP NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_team_members_team_user ON team_members (team_id, user_id);
CREATE INDEX IF NOT EXISTS ix_team_members_team_id_user_id ON team_members (team_id, user_id);

CREATE TABLE IF NOT EXISTS projects (
    id VARCHAR(36) PRIMARY KEY,
    team_id VARCHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_by VARCHAR(255),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_projects_team_id_created_at ON projects (team_id, created_at);

CREATE TABLE IF NOT EXISTS project_members (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    role VARCHAR(32) NOT NULL,
    joined_at TIMESTAMP NOT NULL,
    CONSTRAINT ck_project_members_role CHECK (role IN ('owner', 'manager', 'member'))
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_project_members_project_user ON project_members (project_id, user_id);
CREATE INDEX IF NOT EXISTS ix_project_members_project_id_user_id ON project_members (project_id, user_id);
CREATE INDEX IF NOT EXISTS ix_project_members_project_id_role ON project_members (project_id, role);

ALTER TABLE tasks ADD COLUMN IF NOT EXISTS parent_task_id VARCHAR(36);
CREATE INDEX IF NOT EXISTS ix_tasks_parent_task_id ON tasks (parent_task_id);
