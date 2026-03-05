/*
  # FIILTHY Core Schema - Initial Setup

  1. New Tables
    - `users`
      - `id` (uuid, primary key)
      - `email` (text, unique)
      - `plan` (text, default 'free')
      - `referral_code` (text, unique, for referral system)
      - `referred_by` (text, stores referrer's code)
      - `referral_count` (int, default 0)
      - `created_at` (timestamptz)
      - `updated_at` (timestamptz)

    - `projects`
      - `id` (uuid, primary key)
      - `owner_id` (uuid, references users)
      - `name` (text)
      - `url` (text)
      - `niche` (text)
      - `keywords` (jsonb, array of keywords)
      - `locations` (jsonb, array of locations)
      - `max_concurrent_jobs` (int, default 1)
      - `created_at` (timestamptz)
      - `updated_at` (timestamptz)

    - `leads`
      - `id` (uuid, primary key)
      - `project_id` (uuid, references projects)
      - `url` (text)
      - `url_hash` (text, unique index for deduplication)
      - `title` (text)
      - `content` (text)
      - `source` (text, e.g., 'reddit', 'hn', 'serp')
      - `author` (text)
      - `score` (int, 0-100)
      - `intent` (text, 'high'|'medium'|'low')
      - `reasons` (jsonb, scoring details)
      - `status` (text, default 'new')
      - `created_at` (timestamptz)
      - `last_seen_at` (timestamptz)

    - `jobs`
      - `id` (uuid, primary key)
      - `owner_id` (uuid, references users)
      - `project_id` (uuid, references projects)
      - `type` (text, job type)
      - `payload` (jsonb)
      - `status` (text, default 'queued')
      - `priority` (int, default 100)
      - `attempts` (int, default 0)
      - `max_attempts` (int, default 5)
      - `locked_by` (text)
      - `locked_at` (timestamptz)
      - `run_after` (timestamptz)
      - `duration_ms` (int)
      - `result` (jsonb)
      - `error` (text)
      - `created_at` (timestamptz)

    - `usage_counters`
      - `user_id` (uuid, references users)
      - `period_start` (timestamptz)
      - `scans` (int, default 0)
      - `serp_queries` (int, default 0)
      - `deep_fetches` (int, default 0)
      - `ai_classifications` (int, default 0)
      - `notifications` (int, default 0)
      - `updated_at` (timestamptz)
      - Primary key: (user_id, period_start)

    - `credit_ledger`
      - `id` (uuid, primary key)
      - `user_id` (uuid, references users)
      - `event` (text)
      - `delta` (int, credit change)
      - `meta` (jsonb)
      - `created_at` (timestamptz)

    - `query_cache`
      - `query` (text, primary key)
      - `last_run` (timestamptz)

    - `url_cache`
      - `url` (text, primary key)
      - `fetched_at` (timestamptz)
      - `content` (text)

    - `referral_events`
      - `id` (uuid, primary key)
      - `referrer_user_id` (uuid, references users)
      - `referred_user_id` (uuid, references users)
      - `referral_code` (text)
      - `event` (text)
      - `created_at` (timestamptz)

  2. Security
    - Enable RLS on all tables
    - Users can read/update their own user data
    - Users can manage their own projects
    - Users can view their own leads
    - Jobs are accessible by owner
    - Usage counters are accessible by owner
    - Credit ledger is read-only for users
    - Cache tables are system-only

  3. Important Notes
    - All tables use UUIDs for primary keys
    - Timestamps use timestamptz for proper timezone handling
    - JSONB used for flexible metadata storage
    - Indexes added for common query patterns
    - RLS policies enforce data isolation
*/

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  email text UNIQUE NOT NULL,
  plan text DEFAULT 'free' NOT NULL,
  referral_code text UNIQUE,
  referred_by text,
  referral_count int DEFAULT 0 NOT NULL,
  created_at timestamptz DEFAULT now() NOT NULL,
  updated_at timestamptz DEFAULT now() NOT NULL
);

ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own data"
  ON users FOR SELECT
  TO authenticated
  USING (auth.uid() = id);

CREATE POLICY "Users can update own data"
  ON users FOR UPDATE
  TO authenticated
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name text NOT NULL,
  url text NOT NULL,
  niche text,
  keywords jsonb DEFAULT '[]'::jsonb NOT NULL,
  locations jsonb DEFAULT '[]'::jsonb NOT NULL,
  max_concurrent_jobs int DEFAULT 1 NOT NULL,
  created_at timestamptz DEFAULT now() NOT NULL,
  updated_at timestamptz DEFAULT now() NOT NULL
);

ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own projects"
  ON projects FOR SELECT
  TO authenticated
  USING (auth.uid() = owner_id);

CREATE POLICY "Users can create own projects"
  ON projects FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = owner_id);

CREATE POLICY "Users can update own projects"
  ON projects FOR UPDATE
  TO authenticated
  USING (auth.uid() = owner_id)
  WITH CHECK (auth.uid() = owner_id);

CREATE POLICY "Users can delete own projects"
  ON projects FOR DELETE
  TO authenticated
  USING (auth.uid() = owner_id);

-- Leads table
CREATE TABLE IF NOT EXISTS leads (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id uuid REFERENCES projects(id) ON DELETE CASCADE,
  url text NOT NULL,
  url_hash text NOT NULL,
  title text,
  content text,
  source text,
  author text,
  score int DEFAULT 0 NOT NULL,
  intent text DEFAULT 'low' NOT NULL,
  reasons jsonb DEFAULT '{}'::jsonb NOT NULL,
  status text DEFAULT 'new' NOT NULL,
  created_at timestamptz DEFAULT now() NOT NULL,
  last_seen_at timestamptz DEFAULT now() NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS leads_url_hash_idx ON leads(url_hash);
CREATE INDEX IF NOT EXISTS leads_project_id_idx ON leads(project_id);
CREATE INDEX IF NOT EXISTS leads_score_idx ON leads(score DESC);
CREATE INDEX IF NOT EXISTS leads_intent_idx ON leads(intent);
CREATE INDEX IF NOT EXISTS leads_status_idx ON leads(status);

ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view leads for own projects"
  ON leads FOR SELECT
  TO authenticated
  USING (
    project_id IN (
      SELECT id FROM projects WHERE owner_id = auth.uid()
    )
  );

CREATE POLICY "Users can create leads for own projects"
  ON leads FOR INSERT
  TO authenticated
  WITH CHECK (
    project_id IN (
      SELECT id FROM projects WHERE owner_id = auth.uid()
    )
  );

CREATE POLICY "Users can update leads for own projects"
  ON leads FOR UPDATE
  TO authenticated
  USING (
    project_id IN (
      SELECT id FROM projects WHERE owner_id = auth.uid()
    )
  )
  WITH CHECK (
    project_id IN (
      SELECT id FROM projects WHERE owner_id = auth.uid()
    )
  );

-- Jobs table
CREATE TABLE IF NOT EXISTS jobs (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  project_id uuid REFERENCES projects(id) ON DELETE CASCADE,
  type text NOT NULL,
  payload jsonb DEFAULT '{}'::jsonb NOT NULL,
  status text DEFAULT 'queued' NOT NULL,
  priority int DEFAULT 100 NOT NULL,
  attempts int DEFAULT 0 NOT NULL,
  max_attempts int DEFAULT 5 NOT NULL,
  locked_by text,
  locked_at timestamptz,
  run_after timestamptz DEFAULT now() NOT NULL,
  duration_ms int,
  result jsonb,
  error text,
  created_at timestamptz DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS jobs_status_idx ON jobs(status);
CREATE INDEX IF NOT EXISTS jobs_owner_id_idx ON jobs(owner_id);
CREATE INDEX IF NOT EXISTS jobs_project_id_idx ON jobs(project_id);
CREATE INDEX IF NOT EXISTS jobs_run_after_idx ON jobs(run_after);

ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own jobs"
  ON jobs FOR SELECT
  TO authenticated
  USING (auth.uid() = owner_id);

CREATE POLICY "Users can create own jobs"
  ON jobs FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = owner_id);

CREATE POLICY "Users can update own jobs"
  ON jobs FOR UPDATE
  TO authenticated
  USING (auth.uid() = owner_id)
  WITH CHECK (auth.uid() = owner_id);

-- Usage counters table
CREATE TABLE IF NOT EXISTS usage_counters (
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  period_start timestamptz NOT NULL,
  scans int DEFAULT 0 NOT NULL,
  serp_queries int DEFAULT 0 NOT NULL,
  deep_fetches int DEFAULT 0 NOT NULL,
  ai_classifications int DEFAULT 0 NOT NULL,
  notifications int DEFAULT 0 NOT NULL,
  updated_at timestamptz DEFAULT now() NOT NULL,
  PRIMARY KEY (user_id, period_start)
);

ALTER TABLE usage_counters ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own usage"
  ON usage_counters FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

-- Credit ledger table
CREATE TABLE IF NOT EXISTS credit_ledger (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  event text NOT NULL,
  delta int NOT NULL,
  meta jsonb DEFAULT '{}'::jsonb NOT NULL,
  created_at timestamptz DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS credit_ledger_user_id_idx ON credit_ledger(user_id);

ALTER TABLE credit_ledger ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own credit history"
  ON credit_ledger FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

-- Query cache table (system-only, no RLS needed for service role)
CREATE TABLE IF NOT EXISTS query_cache (
  query text PRIMARY KEY,
  last_run timestamptz DEFAULT now() NOT NULL
);

-- URL cache table (system-only, no RLS needed for service role)
CREATE TABLE IF NOT EXISTS url_cache (
  url text PRIMARY KEY,
  fetched_at timestamptz DEFAULT now() NOT NULL,
  content text
);

-- Referral events table
CREATE TABLE IF NOT EXISTS referral_events (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  referrer_user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  referred_user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  referral_code text NOT NULL,
  event text NOT NULL,
  created_at timestamptz DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS referral_events_referrer_idx ON referral_events(referrer_user_id);

ALTER TABLE referral_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own referral events"
  ON referral_events FOR SELECT
  TO authenticated
  USING (auth.uid() = referrer_user_id OR auth.uid() = referred_user_id);