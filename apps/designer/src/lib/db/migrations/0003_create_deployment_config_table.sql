CREATE TABLE `deployment_config` (
	`id` text PRIMARY KEY NOT NULL,
	`organization_id` text NOT NULL,
	`site_id` text NOT NULL,
	`device_id` text NOT NULL,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`updated_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE INDEX `idx_deployment_config_created_at` ON `deployment_config` (`created_at`);--> statement-breakpoint
CREATE INDEX `idx_deployment_config_updated_at` ON `deployment_config` (`updated_at`);
