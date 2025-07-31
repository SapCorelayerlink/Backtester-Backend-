#!/bin/bash
#
# This script tests the smart data endpoint to fetch and backfill data.
#

# Use today's date for the request
START_DATE=$(date -v-1d '+%Y-%m-%d')
END_DATE=$(date '+%Y-%m-%d')
SYMBOL="AAPL"
TIMEFRAME="1min"
BROKER="ibkr" # or "mock"

echo "Requesting data for ${SYMBOL} (${TIMEFRAME}) from ${START_DATE} to ${END_DATE}..."
echo ""

curl -X GET "http://127.0.0.1:8000/api/v1/data/${SYMBOL}/${TIMEFRAME}?start_date=${START_DATE}&end_date=${END_DATE}&broker_name=${BROKER}" | json_pp

echo ""
echo "Request complete." 