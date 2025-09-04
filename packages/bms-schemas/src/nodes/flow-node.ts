/**
 * Flow Node Schema
 * Main schema for nodes in the BMS flow programming system
 */
import { z } from "zod";
import { PositionSchema } from "../common/position";
import { NodeTypeSchema } from "./types";

export const FlowNodeSchema = z
  .object({
    id: z.string().min(1).describe("Unique identifier for the node"),
    type: NodeTypeSchema,
    position: PositionSchema,
    data: z.object({}).passthrough().describe("Node-specific data properties"),
  })
  .describe("Flow node in BMS programming interface");

export type FlowNode = z.infer<typeof FlowNodeSchema>;
