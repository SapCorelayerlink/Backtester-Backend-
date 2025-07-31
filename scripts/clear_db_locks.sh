#!/bin/bash
#
# This script forcefully finds and terminates any processes that are holding a
# lock on the SQLite database file, preventing the application from starting.
# It also cleans up any stale lock files.
#
# Usage: ./scripts/clear_db_locks.sh
#

DB_FILE="data/tradeflow.db"
LOCK_FILE="data/tradeflow.db.lock"

echo "Checking for processes locking ${DB_FILE}..."

# Get PIDs of processes locking the file. -t option gives terse output (PIDs only).
PIDS=$(lsof -t "${DB_FILE}" 2>/dev/null)

if [ -z "$PIDS" ]; then
    echo "No processes found locking the database."
else
    echo "Found the following processes locking the database:"
    # Show process details to the user before killing
    lsof "${DB_FILE}"
    echo ""
    echo "Attempting to terminate these processes..."
    # Use kill -9 for forceful termination.
    for PID in $PIDS; do
        if kill -9 "${PID}"; then
            echo "Successfully terminated process ${PID}."
        else
            echo "Failed to terminate process ${PID}. It may have already exited."
        fi
    done
fi

if [ -f "$LOCK_FILE" ]; then
    echo "Removing stale lock file: ${LOCK_FILE}"
    rm -f "$LOCK_FILE"
fi

echo ""
echo "Cleanup complete. You should be able to start the server now." 