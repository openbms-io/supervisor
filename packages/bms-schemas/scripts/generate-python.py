#!/usr/bin/env python3
"""
Generate Pydantic models from JSON Schema
"""

import os
import subprocess
import sys
from pathlib import Path

def generate_pydantic_models():
    """Generate Pydantic models from JSON Schema files"""
    try:
        print("🔄 Generating Pydantic models from JSON Schema...")

        # Get script directory and project paths
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        json_schema_dir = project_root / "json-schema"
        python_output_dir = project_root / "python"

        # Ensure output directory exists
        python_output_dir.mkdir(parents=True, exist_ok=True)

        # Check if JSON schema files exist
        if not json_schema_dir.exists() or not list(json_schema_dir.glob("*.json")):
            print("❌ No JSON schema files found. Run 'npm run generate:json' first.")
            sys.exit(1)

        # Generate models for each JSON schema file
        schema_files = list(json_schema_dir.glob("*.json"))

        for schema_file in schema_files:
            model_name = schema_file.stem.replace("-", "_")
            output_file = python_output_dir / f"{model_name}.py"

            print(f"  📄 Processing {schema_file.name} -> {output_file.name}")

            # Run datamodel-code-generator
            cmd = [
                "datamodel-codegen",
                "--input", str(schema_file),
                "--output", str(output_file),
                "--input-file-type", "jsonschema",
                "--output-model-type", "pydantic_v2.BaseModel",
                "--target-python-version", "3.11",
                "--use-schema-description",
                "--use-field-description",
                "--snake-case-field",
                "--strict-nullable",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"❌ Error generating {output_file.name}:")
                print(result.stderr)
                sys.exit(1)

        # Generate index.py to export all models (mirrors TypeScript structure)
        index_file = python_output_dir / "index.py"

        with open(index_file, "w") as f:
            f.write('"""\nGenerated Pydantic models from JSON Schema\n"""\n\n')

            for schema_file in schema_files:
                model_name = schema_file.stem.replace("-", "_")
                f.write(f"from .{model_name} import *\n")

        print(f"✅ Generated {len(schema_files)} Pydantic model(s)")
        print(f"   Output: {python_output_dir}")

    except Exception as error:
        print(f"❌ Error generating Pydantic models: {error}")
        sys.exit(1)

if __name__ == "__main__":
    generate_pydantic_models()
