-- Rename column from flow_config to workflow_config on projects table
-- This migration updates existing databases to match the new schema

PRAGMA foreign_keys=off;
--> statement-breakpoint

-- Create new table with desired schema
CREATE TABLE projects_new (
  id TEXT PRIMARY KEY NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  workflow_config TEXT DEFAULT '{}' NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint

-- Copy data from old table, mapping flow_config -> workflow_config
INSERT INTO projects_new (id, name, description, workflow_config, created_at, updated_at)
SELECT id, name, description, flow_config, created_at, updated_at FROM projects;
--> statement-breakpoint

-- Drop old table and rename new
DROP TABLE projects;
--> statement-breakpoint
ALTER TABLE projects_new RENAME TO projects;
--> statement-breakpoint

-- Recreate indexes
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects (created_at);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS idx_projects_updated_at ON projects (updated_at);
--> statement-breakpoint

PRAGMA foreign_keys=on;
