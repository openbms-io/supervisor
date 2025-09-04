/**
 * BMS Schema Versioning
 * Tracks schema versions for migration and compatibility
 */
import { z } from "zod";

export const SCHEMA_VERSION = "1.0.0";
export const SCHEMA_COMPATIBILITY = ">=1.0.0";

export const VersionSchema = z.object({
  version: z.string().default(SCHEMA_VERSION),
  compatibility: z.string().default(SCHEMA_COMPATIBILITY),
  generated_at: z.string().datetime().optional(),
});

export type Version = z.infer<typeof VersionSchema>;

export function withVersion<T extends z.ZodType>(
  schema: T,
  schemaName: string,
) {
  return z.object({
    schema_info: VersionSchema.extend({
      schema_name: z.string().default(schemaName),
    }),
    data: schema,
  });
}

export function getVersionMetadata(
  schemaName: string,
): Version & { schema_name: string } {
  return {
    version: SCHEMA_VERSION,
    compatibility: SCHEMA_COMPATIBILITY,
    schema_name: schemaName,
    generated_at: new Date().toISOString(),
  };
}
