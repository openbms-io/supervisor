ALTER TABLE `deployment_config` RENAME COLUMN "device_id" TO "iot_device_id";--> statement-breakpoint
ALTER TABLE `deployment_config` ADD `project_id` text NOT NULL REFERENCES projects(id);--> statement-breakpoint
CREATE INDEX `idx_deployment_config_project_id` ON `deployment_config` (`project_id`);--> statement-breakpoint
CREATE UNIQUE INDEX `unique_deployment_config_per_project` ON `deployment_config` (`project_id`);
