-- Phase 3 auth/session additive migration.
-- Canonical path for deployed DBs. Runtime auto-init remains a local/dev safety net.

CREATE TABLE IF NOT EXISTS user_profiles (
  id VARCHAR(36) PRIMARY KEY,
  email VARCHAR(320) NOT NULL,
  display_name VARCHAR(255),
  created_at TIMESTAMPTZ NOT NULL,
  last_login_at TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_user_profiles_email
  ON user_profiles (email);

CREATE TABLE IF NOT EXISTS auth_sessions (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL,
  token_hash VARCHAR(64) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  expires_at TIMESTAMPTZ,
  revoked_at TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_auth_sessions_token_hash
  ON auth_sessions (token_hash);

CREATE INDEX IF NOT EXISTS ix_auth_sessions_user_id
  ON auth_sessions (user_id);
