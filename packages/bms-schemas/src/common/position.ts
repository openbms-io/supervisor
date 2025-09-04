/**
 * Position Schema
 * Defines 2D coordinate positioning for nodes
 */
import { z } from "zod";

export const PositionSchema = z
  .object({
    x: z.number().describe("X coordinate position"),
    y: z.number().describe("Y coordinate position"),
  })
  .describe("2D position coordinates for node placement");

export type Position = z.infer<typeof PositionSchema>;
