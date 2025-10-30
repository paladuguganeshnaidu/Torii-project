-- Database schema suggestions for separating PII and authentication data
-- Run these statements in your database migration tooling.

-- Users table: PII and public profile data
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(150) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    email VARCHAR(320) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    is_active BOOLEAN DEFAULT true
);

-- Auth table: stores password hashes and auth-related metadata
CREATE TABLE auth (
    user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    password_hash TEXT NOT NULL,
    password_algo VARCHAR(50) NOT NULL DEFAULT 'argon2',
    last_password_change TIMESTAMP WITH TIME ZONE,
    failed_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Login history: record of logins (avoid storing IPs in plaintext if regulated)
CREATE TABLE login_history (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    successful BOOLEAN,
    ip_address VARCHAR(100),
    user_agent TEXT,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Password reset tokens (short lived)
CREATE TABLE password_resets (
    token TEXT PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
