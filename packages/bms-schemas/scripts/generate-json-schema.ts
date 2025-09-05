#!/usr/bin/env ts-node
/**
 * Generate JSON Schema from Zod schemas
 */
import { zodToJsonSchema } from "zod-to-json-schema";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { FlowNodeSchema } from "../src/nodes/flow-node";

// ES module __dirname equivalent
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function generateJsonSchema() {
  try {
    console.log("🔄 Generating JSON Schema from Zod schemas...");

    // Ensure output directory exists
    const outputDir = path.join(__dirname, "../json-schema");
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    // Generate FlowNode JSON Schema
    const flowNodeJsonSchema = zodToJsonSchema(FlowNodeSchema, {
      name: "FlowNode",
      target: "openApi3",
    });

    const flowNodeOutputPath = path.join(outputDir, "flow-node.json");
    fs.writeFileSync(
      flowNodeOutputPath,
      JSON.stringify(flowNodeJsonSchema, null, 2),
    );
    console.log("✅ Generated JSON Schema:", flowNodeOutputPath);
  } catch (error) {
    console.error("❌ Error generating JSON Schema:", error);
    process.exit(1);
  }
}

generateJsonSchema();
