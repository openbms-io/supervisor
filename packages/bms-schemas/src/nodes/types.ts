/**
 * Node Type Schema
 * Defines all available node types in the BMS flow system
 */
import { z } from "zod";

export const NodeTypeSchema = z
  .enum([
    "input.sensor",
    "input.manual",
    "input.timer",
    "logic.compare",
    "logic.calculate",
    "logic.condition",
    "control.pid",
    "control.schedule",
    "control.sequence",
    "output.actuator",
    "output.alarm",
    "output.display",
  ])
  .describe("Available node types for BMS flow programming");

export type NodeType = z.infer<typeof NodeTypeSchema>;

// Node type categories for organization
export const INPUT_NODE_TYPES = [
  "input.sensor",
  "input.manual",
  "input.timer",
] as const;

export const LOGIC_NODE_TYPES = [
  "logic.compare",
  "logic.calculate",
  "logic.condition",
] as const;

export const CONTROL_NODE_TYPES = [
  "control.pid",
  "control.schedule",
  "control.sequence",
] as const;

export const OUTPUT_NODE_TYPES = [
  "output.actuator",
  "output.alarm",
  "output.display",
] as const;
