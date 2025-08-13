#!/bin/bash
#
# This script ensures port 8000 is free, cleans up database locks,
# and then starts the FastAPI server with auto-reloading enabled.
#

# --- Kill process on port 8000 ---
echo "--- Ensuring port 8000 is free ---"
ATTEMPTS=0
MAX_ATTEMPTS=5
while [ $ATTEMPTS -lt $MAX_ATTEMPTS ]; do
    # -t gives just the PID, -i checks for the port
    PID=$(lsof -t -i:8000)
    if [ -n "$PID" ]; then
        echo "Found process(es) $PID on port 8000. Attempting to kill..."
        # Kill all processes found on the port
        kill -9 $PID
        sleep 2 # Give the OS time to release the port
    else
        echo "Port 8000 is free."
        break # Exit the loop
    fi
    ATTEMPTS=$((ATTEMPTS + 1))
done

if [ $ATTEMPTS -eq $MAX_ATTEMPTS ]; then
    echo "Failed to free port 8000 after $MAX_ATTEMPTS attempts. Please check manually."
    exit 1
fi
echo ""


# --- Clear database locks ---
echo "--- Step 1: Clearing database locks ---"
# Ensure the cleanup script is executable
chmod +x ./scripts/clear_db_locks.sh
# Run the cleanup script
./scripts/clear_db_locks.sh
echo ""


# --- Start the server ---
echo "--- Step 2: Starting the FastAPI server ---"
echo "Starting uvicorn with auto-reload..."
echo "Access the API at http://127.0.0.1:8000"
echo "-------------------------------------------"

# Start the server (corrected line without the trailing '%')
uvicorn api.main:app --reload 