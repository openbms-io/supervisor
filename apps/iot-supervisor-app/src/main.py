"""
BMS IoT Supervisor - FastAPI application entry point
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import uvicorn

from python.flow_node import FlowNode, Type as NodeType

app = FastAPI(
    title="BMS IoT Supervisor",
    description="FastAPI runtime for BMS execution on IoT devices",
    version="0.1.0",
)

# Configure CORS for Designer app communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Designer app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "BMS IoT Supervisor is running"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "bms-iot-supervisor"}


@app.get("/status")
async def status():
    """Status endpoint"""
    return {"service": "bms-iot-supervisor", "version": "0.1.0", "status": "running"}


@app.post("/api/config/deploy")
async def deploy_config(flow_nodes: List[FlowNode]):
    """Deploy configuration endpoint with schema validation"""
    try:
        # Validate all nodes using shared schema
        validated_nodes = []
        for node in flow_nodes:
            # Additional validation can be added here
            validated_nodes.append(node)

        return {
            "status": "success",
            "message": f"Configuration with {len(validated_nodes)} nodes deployed successfully",
            "config_id": f"config-{len(validated_nodes)}-nodes",
            "nodes": [
                {"id": node.id, "type": node.type.value} for node in validated_nodes
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {str(e)}")


@app.get("/api/config/validate")
async def validate_node(node: FlowNode):
    """Validate a single FlowNode"""
    try:
        return {
            "status": "valid",
            "node_id": node.id,
            "type": node.type.value,
            "message": "Node validation successful",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid node: {str(e)}")


@app.get("/api/schema/node-types")
async def get_node_types():
    """Get available node types from schema"""
    return {
        "node_types": [node_type.value for node_type in NodeType],
        "count": len(NodeType),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
