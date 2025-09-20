-- Seed initial projects only if table is empty
INSERT INTO projects (id, name, description, flow_config, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000001', 'Sample Project', 'Seeded project', '{}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
WHERE (SELECT COUNT(*) FROM projects) = 0
UNION ALL
SELECT '00000000-0000-0000-0000-000000000002', 'Second Project', 'Another example project', '{}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
WHERE (SELECT COUNT(*) FROM projects) = 0;
