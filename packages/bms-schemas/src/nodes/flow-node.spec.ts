/**
 * Flow Node Schema Tests
 */
import { FlowNodeSchema, type FlowNode } from "./flow-node";

describe("FlowNodeSchema", () => {
  describe("Valid flow nodes", () => {
    test("should accept complete valid node", () => {
      const node: FlowNode = {
        id: "test-node-1",
        type: "input.sensor",
        position: { x: 100, y: 200 },
        data: { label: "Temperature Sensor" },
      };

      const result = FlowNodeSchema.safeParse(node);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toEqual(node);
      }
    });

    test("should accept node with empty data object", () => {
      const node = {
        id: "minimal-node",
        type: "logic.compare",
        position: { x: 0, y: 0 },
        data: {},
      };

      const result = FlowNodeSchema.safeParse(node);
      expect(result.success).toBe(true);
    });

    test("should accept node with complex data", () => {
      const node = {
        id: "complex-node",
        type: "control.pid",
        position: { x: 150, y: 250 },
        data: {
          setpoint: 22.5,
          kp: 1.0,
          ki: 0.1,
          kd: 0.05,
          config: {
            min_output: 0,
            max_output: 100,
          },
          tags: ["temperature", "control"],
        },
      };

      const result = FlowNodeSchema.safeParse(node);
      expect(result.success).toBe(true);
    });

    test("should accept all node types", () => {
      const nodeTypes = [
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
      ];

      nodeTypes.forEach((nodeType) => {
        const node = {
          id: `test-${nodeType}`,
          type: nodeType,
          position: { x: 100, y: 200 },
          data: {},
        };

        const result = FlowNodeSchema.safeParse(node);
        expect(result.success).toBe(true);
        if (result.success) {
          expect(result.data.type).toBe(nodeType);
        }
      });
    });
  });

  describe("Invalid flow nodes", () => {
    test("should reject missing id", () => {
      const node = {
        type: "input.sensor",
        position: { x: 100, y: 200 },
        data: {},
      };

      const result = FlowNodeSchema.safeParse(node);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues[0].path).toContain("id");
      }
    });

    test("should reject empty id", () => {
      const node = {
        id: "",
        type: "input.sensor",
        position: { x: 100, y: 200 },
        data: {},
      };

      const result = FlowNodeSchema.safeParse(node);
      expect(result.success).toBe(false);
    });

    test("should reject invalid node type", () => {
      const node = {
        id: "test-node",
        type: "invalid.type",
        position: { x: 100, y: 200 },
        data: {},
      };

      const result = FlowNodeSchema.safeParse(node);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues[0].path).toContain("type");
      }
    });

    test("should reject invalid position", () => {
      const node = {
        id: "test-node",
        type: "input.sensor",
        position: { x: "invalid", y: 200 },
        data: {},
      };

      const result = FlowNodeSchema.safeParse(node);
      expect(result.success).toBe(false);
    });

    test("should reject missing position", () => {
      const node = {
        id: "test-node",
        type: "input.sensor",
        data: {},
      };

      const result = FlowNodeSchema.safeParse(node);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues[0].path).toContain("position");
      }
    });

    test("should reject missing data", () => {
      const node = {
        id: "test-node",
        type: "input.sensor",
        position: { x: 100, y: 200 },
      };

      const result = FlowNodeSchema.safeParse(node);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues[0].path).toContain("data");
      }
    });

    test("should reject non-object data", () => {
      const node = {
        id: "test-node",
        type: "input.sensor",
        position: { x: 100, y: 200 },
        data: "invalid",
      };

      const result = FlowNodeSchema.safeParse(node);
      expect(result.success).toBe(false);
    });
  });

  describe("Type inference", () => {
    test("should infer correct FlowNode type", () => {
      const node: FlowNode = {
        id: "typed-node",
        type: "input.sensor",
        position: { x: 100, y: 200 },
        data: { label: "Test" },
      };

      // TypeScript compile-time checks
      expect(typeof node.id).toBe("string");
      expect(typeof node.type).toBe("string");
      expect(typeof node.position).toBe("object");
      expect(typeof node.data).toBe("object");
    });
  });

  describe("Schema composition", () => {
    test("should validate nested schemas correctly", () => {
      const node = {
        id: "composed-node",
        type: "logic.calculate",
        position: { x: 75.5, y: 125.25 },
        data: {
          formula: "A + B",
          inputs: ["sensor1", "sensor2"],
          output: "result",
        },
      };

      const result = FlowNodeSchema.safeParse(node);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.position.x).toBe(75.5);
        expect(result.data.position.y).toBe(125.25);
        expect(result.data.data.formula).toBe("A + B");
      }
    });
  });
});
