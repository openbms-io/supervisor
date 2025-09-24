#!/bin/bash

# Balena deployment script for BMS IoT App
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}    BMS IoT App Balena Deployment${NC}"
echo -e "${BLUE}========================================${NC}"

# Check if balena CLI is installed
if ! command -v balena &> /dev/null; then
    echo -e "${RED}❌ Balena CLI not found. Please install it first:${NC}"
    echo -e "   ${BLUE}https://github.com/balena-io/balena-cli/blob/master/INSTALL.md${NC}"
    exit 1
fi

# Check if logged in to Balena
if ! balena whoami &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not logged in to Balena. Please log in:${NC}"
    echo -e "   ${BLUE}balena login${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Balena CLI ready${NC}"

# Get deployment target
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: $0 <fleet-name-or-device-uuid> [org-id] [site-id] [device-id]${NC}"
    echo -e ""
    echo -e "${BLUE}Examples:${NC}"
    echo -e "  $0 myBmsFleet                    # Deploy to fleet"
    echo -e "  $0 abc123def456                  # Deploy to specific device"
    echo -e "  $0 myBmsFleet org1 site1 dev1    # Deploy with auto-config"
    echo -e ""
    echo -e "${BLUE}Available fleets:${NC}"
    balena fleets || echo "No fleets found"
    exit 1
fi

TARGET="$1"
ORG_ID="$2"
SITE_ID="$3"
DEVICE_ID="$4"

echo -e "${BLUE}Deployment target: ${TARGET}${NC}"

# Set environment variables if provided
if [ -n "$ORG_ID" ] && [ -n "$SITE_ID" ] && [ -n "$DEVICE_ID" ]; then
    echo -e "${YELLOW}Setting environment variables for auto-provisioning...${NC}"

    # Check if target is a device UUID or fleet name
    if [[ "$TARGET" =~ ^[a-f0-9]{8}[a-f0-9]{4}[a-f0-9]{4}[a-f0-9]{4}[a-f0-9]{12}$ ]]; then
        # Device UUID format
        echo -e "${BLUE}Setting variables for device: $TARGET${NC}"
        balena env add BMS_ORG_ID "$ORG_ID" --device "$TARGET" || true
        balena env add BMS_SITE_ID "$SITE_ID" --device "$TARGET" || true
        balena env add BMS_DEVICE_ID "$DEVICE_ID" --device "$TARGET" || true
    else
        # Fleet name format
        echo -e "${BLUE}Setting variables for fleet: $TARGET${NC}"
        balena env add BMS_ORG_ID "$ORG_ID" --application "$TARGET" || true
        balena env add BMS_SITE_ID "$SITE_ID" --application "$TARGET" || true
        balena env add BMS_DEVICE_ID "$DEVICE_ID" --application "$TARGET" || true
    fi

    echo -e "${GREEN}✅ Environment variables set for auto-provisioning${NC}"
fi

# Deploy the application
echo -e "${BLUE}Deploying BMS IoT App...${NC}"

# Get the monorepo root directory (2 levels up from this script)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
MONOREPO_ROOT="$( cd "$SCRIPT_DIR/../.." &> /dev/null && pwd )"

echo -e "${YELLOW}Building from monorepo root: $MONOREPO_ROOT${NC}"
echo -e "${YELLOW}Using Dockerfile: apps/bms-iot-app/Dockerfile${NC}"

# Change to monorepo root and push with specific Dockerfile
cd "$MONOREPO_ROOT"
balena push "$TARGET" --dockerfile apps/bms-iot-app/Dockerfile

if [ $? -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}    Deployment Successful! 🎉${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e ""
    echo -e "${BLUE}Next steps:${NC}"

    if [ -n "$ORG_ID" ] && [ -n "$SITE_ID" ] && [ -n "$DEVICE_ID" ]; then
        echo -e "1. ${GREEN}Device will auto-provision from environment variables${NC}"
        echo -e "2. ${BLUE}Monitor device logs: balena logs <device-uuid>${NC}"
        echo -e "3. ${BLUE}SSH access: balena ssh <device-uuid>${NC}"
    else
        echo -e "1. ${YELLOW}SSH into device: balena ssh <device-uuid>${NC}"
        echo -e "2. ${YELLOW}Run provisioning: python -m src.cli config setup --interactive${NC}"
        echo -e "3. ${GREEN}Device will start automatically after provisioning${NC}"
    fi

    echo -e ""
    echo -e "${BLUE}Useful commands:${NC}"
    echo -e "  balena devices                           # List all devices"
    echo -e "  balena logs <device-uuid>                # View device logs"
    echo -e "  balena ssh <device-uuid>                 # SSH into device"
    echo -e "  balena env add VAR_NAME value --device <uuid>  # Set device variables"

else
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
fi
