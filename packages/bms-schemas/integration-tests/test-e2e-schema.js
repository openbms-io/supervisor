#!/usr/bin/env node
/**
 * End-to-End Schema Integration Test
 * Tests that both Designer (TypeScript) and IoT Supervisor (Python) use the same schema
 */

import { FlowNodeSchema, NodeTypeSchema } from "../src/index";

async function testE2ESchemaIntegration() {
  console.log("🚀 Starting End-to-End Schema Integration Test...\n");

  // Test 1: Create FlowNode using TypeScript schema
  console.log("📦 Test 1: TypeScript Schema Validation");
  const testNode = {
    id: "e2e-test-node",
    type: "input.sensor",
    position: { x: 150, y: 250 },
    data: { label: "E2E Test Sensor", unit: "°F" },
  };

  const validation = FlowNodeSchema.safeParse(testNode);
  if (!validation.success) {
    console.error("❌ TypeScript validation failed:", validation.error.issues);
    return false;
  }

  console.log("✅ TypeScript validation passed");
  console.log(`   Node: ${testNode.id} (${testNode.type})`);

  // Test 2: Send to IoT Supervisor API for Python validation
  console.log("\n🐍 Test 2: Python Schema Validation via API");

  try {
    const response = await fetch("http://localhost:8081/api/config/deploy", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify([testNode]),
    });

    if (!response.ok) {
      console.error(
        "❌ API request failed:",
        response.status,
        response.statusText,
      );
      return false;
    }

    const result = await response.json();
    console.log("✅ Python validation passed via API");
    console.log(`   ${result.message}`);
    console.log(`   Config ID: ${result.config_id}`);
  } catch (error) {
    console.error("❌ API test failed:", error.message);
    return false;
  }

  // Test 3: Verify schema consistency
  console.log("\n🔍 Test 3: Schema Consistency Check");

  try {
    const nodeTypesResponse = await fetch(
      "http://localhost:8081/api/schema/node-types",
    );
    const nodeTypesResult = await nodeTypesResponse.json();

    const pythonNodeTypes = new Set(nodeTypesResult.node_types);
    const typescriptNodeTypes = new Set(NodeTypeSchema.options);

    // Check if sets are equal
    const setsEqual =
      pythonNodeTypes.size === typescriptNodeTypes.size &&
      [...pythonNodeTypes].every((type) => typescriptNodeTypes.has(type));

    if (!setsEqual) {
      console.error("❌ Schema inconsistency detected!");
      console.error("Python types:", [...pythonNodeTypes]);
      console.error("TypeScript types:", [...typescriptNodeTypes]);
      return false;
    }

    console.log("✅ Schema consistency verified");
    console.log(`   Both platforms support ${pythonNodeTypes.size} node types`);
  } catch (error) {
    console.error("❌ Schema consistency check failed:", error.message);
    return false;
  }

  console.log("\n🎉 End-to-End Schema Integration Test PASSED!");
  console.log("\n📋 Summary:");
  console.log("   ✅ Zod schema validates in TypeScript (Designer)");
  console.log("   ✅ Pydantic schema validates in Python (IoT Supervisor)");
  console.log("   ✅ Both schemas are consistent and synchronized");
  console.log("   ✅ API communication works between both apps");

  return true;
}

// Run the test
testE2ESchemaIntegration()
  .then((success) => process.exit(success ? 0 : 1))
  .catch((error) => {
    console.error("❌ Test failed with error:", error);
    process.exit(1);
  });
