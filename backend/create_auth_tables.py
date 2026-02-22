"""
Create Better Auth tables in Neon PostgreSQL.
Uses camelCase column names as expected by Better Auth.
Tables: user, session, account, verification
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

SQL = """
-- Drop existing tables and recreate with camelCase columns
DROP TABLE IF EXISTS "verification" CASCADE;
DROP TABLE IF EXISTS "account" CASCADE;
DROP TABLE IF EXISTS "session" CASCADE;
DROP TABLE IF EXISTS "user" CASCADE;

-- 1. USER table
CREATE TABLE "user" (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    "emailVerified" BOOLEAN NOT NULL DEFAULT FALSE,
    image           TEXT,
    "createdAt"     TIMESTAMP NOT NULL DEFAULT NOW(),
    "updatedAt"     TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 2. SESSION table
CREATE TABLE "session" (
    id              TEXT PRIMARY KEY,
    "expiresAt"     TIMESTAMP NOT NULL,
    token           TEXT NOT NULL UNIQUE,
    "createdAt"     TIMESTAMP NOT NULL DEFAULT NOW(),
    "updatedAt"     TIMESTAMP NOT NULL DEFAULT NOW(),
    "ipAddress"     TEXT,
    "userAgent"     TEXT,
    "userId"        TEXT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE
);

-- 3. ACCOUNT table
CREATE TABLE "account" (
    id                          TEXT PRIMARY KEY,
    "accountId"                 TEXT NOT NULL,
    "providerId"                TEXT NOT NULL,
    "userId"                    TEXT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    "accessToken"               TEXT,
    "refreshToken"              TEXT,
    "idToken"                   TEXT,
    "accessTokenExpiresAt"      TIMESTAMP,
    "refreshTokenExpiresAt"     TIMESTAMP,
    scope                       TEXT,
    password                    TEXT,
    "createdAt"                 TIMESTAMP NOT NULL DEFAULT NOW(),
    "updatedAt"                 TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 4. VERIFICATION table
CREATE TABLE "verification" (
    id              TEXT PRIMARY KEY,
    identifier      TEXT NOT NULL,
    value           TEXT NOT NULL,
    "expiresAt"     TIMESTAMP NOT NULL,
    "createdAt"     TIMESTAMP DEFAULT NOW(),
    "updatedAt"     TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_session_user_id ON "session"("userId");
CREATE INDEX idx_session_token ON "session"(token);
CREATE INDEX idx_account_user_id ON "account"("userId");
CREATE INDEX idx_account_provider ON "account"("providerId");
CREATE INDEX idx_verification_identifier ON "verification"(identifier);
"""

if __name__ == "__main__":
    print("Connecting to Neon PostgreSQL...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    print("Recreating Better Auth tables (camelCase columns)...")
    cur.execute(SQL)
    conn.commit()

    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    tables = [row[0] for row in cur.fetchall()]

    for table in ["user", "session", "account", "verification"]:
        if table in tables:
            print(f"  ✅ {table}")
        else:
            print(f"  ❌ {table} — MISSING")

    cur.close()
    conn.close()
    print("\nDone!")
