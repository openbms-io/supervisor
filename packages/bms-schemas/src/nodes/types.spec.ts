/**
 * Node Type Schema Tests
 */
import {
  NodeTypeSchema,
  type NodeType,
  INPUT_NODE_TYPES,
  LOGIC_NODE_TYPES,
  CONTROL_NODE_TYPES,
  OUTPUT_NODE_TYPES,
} from "./types";

describe("NodeTypeSchema", () => {
  describe("Valid node types", () => {
    test("should accept all input node types", () => {
      INPUT_NODE_TYPES.forEach((nodeType) => {
        const result = NodeTypeSchema.safeParse(nodeType);
        expect(result.success).toBe(true);
        if (result.success) {
          expect(result.data).toBe(nodeType);
        }
      });
    });

    test("should accept all logic node types", () => {
      LOGIC_NODE_TYPES.forEach((nodeType) => {
        const result = NodeTypeSchema.safeParse(nodeType);
        expect(result.success).toBe(true);
        if (result.success) {
          expect(result.data).toBe(nodeType);
        }
      });
    });

    test("should accept all control node types", () => {
      CONTROL_NODE_TYPES.forEach((nodeType) => {
        const result = NodeTypeSchema.safeParse(nodeType);
        expect(result.success).toBe(true);
        if (result.success) {
          expect(result.data).toBe(nodeType);
        }
      });
    });

    test("should accept all output node types", () => {
      OUTPUT_NODE_TYPES.forEach((nodeType) => {
        const result = NodeTypeSchema.safeParse(nodeType);
        expect(result.success).toBe(true);
        if (result.success) {
          expect(result.data).toBe(nodeType);
        }
      });
    });
  });

  describe("Invalid node types", () => {
    test("should reject invalid string", () => {
      const result = NodeTypeSchema.safeParse("invalid.type");
      expect(result.success).toBe(false);
    });

    test("should reject empty string", () => {
      const result = NodeTypeSchema.safeParse("");
      expect(result.success).toBe(false);
    });

    test("should reject number", () => {
      const result = NodeTypeSchema.safeParse(123);
      expect(result.success).toBe(false);
    });

    test("should reject null", () => {
      const result = NodeTypeSchema.safeParse(null);
      expect(result.success).toBe(false);
    });

    test("should reject undefined", () => {
      const result = NodeTypeSchema.safeParse(undefined);
      expect(result.success).toBe(false);
    });

    test("should reject object", () => {
      const result = NodeTypeSchema.safeParse({ type: "input.sensor" });
      expect(result.success).toBe(false);
    });
  });

  describe("Type categories", () => {
    test("should have correct count of node types", () => {
      const allTypes = [
        ...INPUT_NODE_TYPES,
        ...LOGIC_NODE_TYPES,
        ...CONTROL_NODE_TYPES,
        ...OUTPUT_NODE_TYPES,
      ];

      expect(allTypes).toHaveLength(12);
      expect(NodeTypeSchema.options).toHaveLength(12);
    });

    test("should have all types in enum", () => {
      const allTypes = [
        ...INPUT_NODE_TYPES,
        ...LOGIC_NODE_TYPES,
        ...CONTROL_NODE_TYPES,
        ...OUTPUT_NODE_TYPES,
      ];

      allTypes.forEach((nodeType) => {
        expect(NodeTypeSchema.options).toContain(nodeType);
      });
    });
  });

  describe("Type inference", () => {
    test("should infer correct NodeType type", () => {
      const nodeType: NodeType = "input.sensor";

      // TypeScript compile-time check
      expect(typeof nodeType).toBe("string");
      expect(INPUT_NODE_TYPES.includes(nodeType as any)).toBe(true);
    });
  });
});
