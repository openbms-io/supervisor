/**
 * Position Schema Tests
 */
import { PositionSchema, type Position } from "./position";

describe("PositionSchema", () => {
  describe("Valid positions", () => {
    test("should accept valid integer coordinates", () => {
      const position = { x: 100, y: 200 };
      const result = PositionSchema.safeParse(position);

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toEqual(position);
      }
    });

    test("should accept valid float coordinates", () => {
      const position = { x: 100.5, y: 200.75 };
      const result = PositionSchema.safeParse(position);

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toEqual(position);
      }
    });

    test("should accept negative coordinates", () => {
      const position = { x: -50, y: -100 };
      const result = PositionSchema.safeParse(position);

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toEqual(position);
      }
    });

    test("should accept zero coordinates", () => {
      const position = { x: 0, y: 0 };
      const result = PositionSchema.safeParse(position);

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toEqual(position);
      }
    });
  });

  describe("Invalid positions", () => {
    test("should reject missing x coordinate", () => {
      const position = { y: 200 };
      const result = PositionSchema.safeParse(position);

      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues[0].path).toContain("x");
      }
    });

    test("should reject missing y coordinate", () => {
      const position = { x: 100 };
      const result = PositionSchema.safeParse(position);

      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues[0].path).toContain("y");
      }
    });

    test("should reject string coordinates", () => {
      const position = { x: "100", y: "200" };
      const result = PositionSchema.safeParse(position);

      expect(result.success).toBe(false);
    });

    test("should reject null coordinates", () => {
      const position = { x: null, y: null };
      const result = PositionSchema.safeParse(position);

      expect(result.success).toBe(false);
    });

    test("should reject undefined coordinates", () => {
      const position = { x: undefined, y: undefined };
      const result = PositionSchema.safeParse(position);

      expect(result.success).toBe(false);
    });

    test("should allow additional properties (extensible)", () => {
      const position = { x: 100, y: 200, z: 300 };
      const result = PositionSchema.safeParse(position);

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.x).toBe(100);
        expect(result.data.y).toBe(200);
        // Additional properties are allowed but not validated
      }
    });
  });

  describe("Type inference", () => {
    test("should infer correct Position type", () => {
      const position: Position = { x: 100, y: 200 };

      // TypeScript compile-time check
      expect(typeof position.x).toBe("number");
      expect(typeof position.y).toBe("number");
    });
  });
});
