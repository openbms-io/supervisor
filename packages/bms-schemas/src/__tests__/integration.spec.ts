/**
 * Integration Tests
 * Tests cross-schema functionality and end-to-end validation
 */
import {
  FlowNodeSchema,
  PositionSchema,
  NodeTypeSchema,
  VersionSchema,
  withVersion,
  getVersionMetadata,
  SCHEMA_VERSION,
} from "../index";

describe("Schema Integration", () => {
  describe("Cross-schema validation", () => {
    test("should validate complete flow with multiple nodes", () => {
      const nodes = [
        {
          id: "temp-sensor",
          type: "input.sensor",
          position: { x: 100, y: 100 },
          data: { label: "Temperature Sensor", unit: "°C" },
        },
        {
          id: "pid-controller",
          type: "control.pid",
          position: { x: 300, y: 100 },
          data: { setpoint: 22.5, kp: 1.0, ki: 0.1, kd: 0.05 },
        },
        {
          id: "actuator",
          type: "output.actuator",
          position: { x: 500, y: 100 },
          data: { label: "HVAC Damper", range: [0, 100] },
        },
      ];

      nodes.forEach((node) => {
        const result = FlowNodeSchema.safeParse(node);
        expect(result.success).toBe(true);
      });
    });
  });

  describe("Schema versioning", () => {
    test("should create versioned schema wrapper", () => {
      const versionedFlowNode = withVersion(FlowNodeSchema, "FlowNode");

      const nodeData = {
        id: "test-node",
        type: "input.sensor",
        position: { x: 100, y: 200 },
        data: { label: "Test Sensor" },
      };

      const versionedData = {
        schema_info: getVersionMetadata("FlowNode"),
        data: nodeData,
      };

      const result = versionedFlowNode.safeParse(versionedData);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.schema_info.version).toBe(SCHEMA_VERSION);
        expect(result.data.schema_info.schema_name).toBe("FlowNode");
        expect(result.data.data).toEqual(nodeData);
      }
    });

    test("should validate version metadata", () => {
      const metadata = getVersionMetadata("TestSchema");
      const result = VersionSchema.safeParse(metadata);

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.version).toBe(SCHEMA_VERSION);
        expect(result.data.generated_at).toBeDefined();
      }
    });
  });

  describe("Export consistency", () => {
    test("should export all required schemas", () => {
      expect(PositionSchema).toBeDefined();
      expect(NodeTypeSchema).toBeDefined();
      expect(FlowNodeSchema).toBeDefined();
      expect(VersionSchema).toBeDefined();
      expect(withVersion).toBeDefined();
      expect(getVersionMetadata).toBeDefined();
    });

    test("should maintain schema relationships", () => {
      // FlowNode should use Position and NodeType
      const testNode = {
        id: "relationship-test",
        type: "logic.condition",
        position: { x: 250, y: 300 },
        data: { condition: "x > 0" },
      };

      // All three schemas should validate their parts
      expect(FlowNodeSchema.safeParse(testNode).success).toBe(true);
      expect(PositionSchema.safeParse(testNode.position).success).toBe(true);
      expect(NodeTypeSchema.safeParse(testNode.type).success).toBe(true);
    });
  });

  describe("Error handling", () => {
    test("should provide clear validation errors", () => {
      const invalidNode = {
        id: "",
        type: "invalid.type",
        position: { x: "invalid", y: null },
        data: "not an object",
      };

      const result = FlowNodeSchema.safeParse(invalidNode);
      expect(result.success).toBe(false);
      if (!result.success) {
        const issues = result.error.issues;
        expect(issues.length).toBeGreaterThan(0);

        // Should have errors for id, type, position, and data
        const paths = issues.map((issue) => issue.path.join("."));
        expect(paths.some((path) => path.includes("id"))).toBe(true);
        expect(paths.some((path) => path.includes("type"))).toBe(true);
        expect(paths.some((path) => path.includes("position"))).toBe(true);
        expect(paths.some((path) => path.includes("data"))).toBe(true);
      }
    });
  });
});
