/**
 * Edge type constants for React Flow
 *
 * React Flow built-in edge types:
 * - 'default': Bezier curve edge (default if no type specified)
 * - 'straight': Straight line edge
 * - 'step': Step/orthogonal edge with 90-degree angles
 * - 'smoothstep': Smooth step edge with rounded corners
 * - 'simplebezier': Simple bezier curve without handles
 *
 * Custom edge types:
 * - 'control-flow': Custom edge for showing activation state
 */
export const EDGE_TYPES = {
  // React Flow built-in types
  DEFAULT: 'default', // Bezier curve edge
  STRAIGHT: 'straight', // Straight line edge
  STEP: 'step', // Step edge with 90-degree angles
  SMOOTHSTEP: 'smoothstep', // Smooth step edge with rounded corners
  SIMPLEBEZIER: 'simplebezier', // Simple bezier curve

  // Custom types
  CONTROL_FLOW: 'control-flow', // Custom edge with activation state
  BIDIRECTIONAL_FLOW: 'bidirectional-flow', // Custom edge for bidirectional flow
} as const

export type EdgeType = (typeof EDGE_TYPES)[keyof typeof EDGE_TYPES]
