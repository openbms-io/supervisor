#!/usr/bin/env node
/**
 * Generate all schemas: TypeScript -> JSON Schema -> Pydantic
 * Orchestrates the complete schema generation pipeline
 */

import { spawn } from "child_process";
import path from "path";
import { fileURLToPath } from "url";

// ES module __dirname equivalent
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function runCommand(command, args = [], options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      stdio: "inherit",
      cwd: path.join(__dirname, ".."),
      ...options,
    });

    child.on("close", (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(
          new Error(
            `Command "${command} ${args.join(" ")}" failed with code ${code}`,
          ),
        );
      }
    });

    child.on("error", reject);
  });
}

async function generateAll() {
  try {
    console.log("🚀 Starting complete schema generation pipeline...\n");

    // Step 1: Generate JSON Schema directly from TypeScript source
    console.log("🔄 Step 1: Generating JSON Schema from TypeScript source...");
    await runCommand("npm", ["run", "generate:json"]);
    console.log("✅ JSON Schema generation complete\n");

    // Step 2: Compile TypeScript schemas for final output
    console.log("📦 Step 2: Compiling TypeScript schemas for output...");
    await runCommand("npm", ["run", "build:ts"]);
    console.log("✅ TypeScript compilation complete\n");

    // Step 3: Generate Pydantic models from JSON Schema
    console.log("🐍 Step 3: Generating Pydantic models...");
    await runCommand("npm", ["run", "generate:python"]);
    console.log("✅ Pydantic model generation complete\n");

    console.log("🎉 Schema generation pipeline completed successfully!");
    console.log("\n📁 Generated outputs:");
    console.log("   • TypeScript: ./typescript/");
    console.log("   • JSON Schema: ./json-schema/");
    console.log("   • Python: ./python/bms_schemas/");
  } catch (error) {
    console.error("❌ Schema generation failed:", error.message);
    process.exit(1);
  }
}

generateAll();
