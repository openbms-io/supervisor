#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}    BMS IoT App Container Starting${NC}"
echo -e "${BLUE}========================================${NC}"

# Set container environment flag
export DOCKER_CONTAINER=true

# Ensure data directory exists and has proper permissions
if [ ! -d "/data" ]; then
    echo -e "${YELLOW}Creating /data directory...${NC}"
    mkdir -p /data
fi

# Copy certificate to data directory if it doesn't exist
if [ ! -f "/data/emqxsl-ca.crt" ] && [ -f "./emqxsl-ca.crt" ]; then
    echo -e "${YELLOW}Copying TLS certificate to persistent storage...${NC}"
    cp ./emqxsl-ca.crt /data/emqxsl-ca.crt
fi

# Function to check if device is provisioned
check_provisioning() {
    echo -e "${BLUE}Checking device provisioning status...${NC}"

    # Check if deployment config exists in database
    python -c "
import sys
import sqlite3
from pathlib import Path

db_path = Path('/data/bms_bacnet.db')
if not db_path.exists():
    print('Database not found')
    sys.exit(1)

try:
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Check if deployment_config table exists (might not exist before migrations)
    cursor.execute(\"\"\"
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='deployment_config'
    \"\"\")
    table_exists = cursor.fetchone()

    if not table_exists:
        print('deployment_config table does not exist (migrations needed)')
        conn.close()
        sys.exit(1)

    # Table exists, check for records
    cursor.execute('SELECT COUNT(*) FROM deployment_config')
    count = cursor.fetchone()[0]
    conn.close()

    if count == 0:
        print('No deployment config found')
        sys.exit(1)
    else:
        print('Device is provisioned')
        sys.exit(0)
except Exception as e:
    print(f'Error checking provisioning: {e}')
    sys.exit(1)
"
    return $?
}

# Function to show provisioning instructions
show_provisioning_instructions() {
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}    DEVICE NOT PROVISIONED${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo -e "${YELLOW}This device needs to be provisioned before it can start.${NC}"
    echo ""
    echo -e "${GREEN}To provision this device:${NC}"
    echo -e "1. SSH into the device:"
    echo -e "   ${BLUE}balena ssh <device-uuid>${NC}"
    echo ""
    echo -e "2. Run the provisioning command:"
    echo -e "   ${BLUE}python -m src.cli config setup --interactive${NC}"
    echo ""
    echo -e "3. Provide the required information:"
    echo -e "   - Organization ID"
    echo -e "   - Site ID"
    echo -e "   - Device ID"
    echo -e "   - MQTT configuration"
    echo -e "   - API credentials"
    echo ""
    echo -e "${GREEN}After provisioning, the container will automatically start the application.${NC}"
    echo ""
    echo -e "${YELLOW}The container will check for provisioning every 30 seconds...${NC}"
    echo -e "${RED}========================================${NC}"
}


# Function to wait for provisioning
wait_for_provisioning() {
    # Show manual provisioning instructions and wait
    while true; do
        if check_provisioning; then
            echo -e "${GREEN}✅ Device is provisioned! Starting application...${NC}"
            break
        else
            show_provisioning_instructions
            echo -e "${YELLOW}Waiting 30 seconds before next check...${NC}"
            sleep 30
        fi
    done
}

# Handle different commands
case "$1" in
    "run-main")
        echo -e "${BLUE}Preparing to start BMS IoT application...${NC}"

        # Check if provisioned
        if ! check_provisioning; then
            wait_for_provisioning
        else
            echo -e "${GREEN}✅ Device is already provisioned!${NC}"
        fi

        echo -e "${BLUE}Running database migrations...${NC}"
        echo -e "${YELLOW}Applying schema updates with Alembic...${NC}"

        # Run Alembic migrations
        if ! alembic upgrade head; then
            echo -e "${RED}❌ Database migration failed!${NC}"
            echo -e "${RED}Container cannot start with outdated schema${NC}"
            echo -e "${RED}Check logs above for migration errors${NC}"
            exit 1
        fi

        echo -e "${GREEN}✅ Database migrations completed successfully${NC}"
        echo -e "${GREEN}Starting BMS IoT application...${NC}"
        exec python -m src.cli run-main
        ;;

    "bash")
        echo -e "${BLUE}Starting interactive bash shell...${NC}"
        exec /bin/bash
        ;;

    "provision")
        echo -e "${BLUE}Starting provisioning mode...${NC}"
        exec python -m src.cli config setup --interactive
        ;;

    "migrate")
        echo -e "${BLUE}Running database migrations only...${NC}"
        echo -e "${YELLOW}Applying schema updates with Alembic...${NC}"

        if ! alembic upgrade head; then
            echo -e "${RED}❌ Database migration failed!${NC}"
            exit 1
        fi

        echo -e "${GREEN}✅ Database migrations completed successfully${NC}"
        exit 0
        ;;

    "check-provisioning")
        if check_provisioning; then
            echo -e "${GREEN}✅ Device is provisioned${NC}"
            exit 0
        else
            echo -e "${RED}❌ Device is not provisioned${NC}"
            exit 1
        fi
        ;;

    *)
        # Pass through any other commands
        echo -e "${BLUE}Executing command: $@${NC}"
        exec "$@"
        ;;
esac
