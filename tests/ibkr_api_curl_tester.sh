#!/bin/bash

# A script to test all broker API endpoints using curl.
# Requires 'jq' to be installed for parsing JSON responses.
# You can install it on macOS with: brew install jq

set -e # Exit immediately if a command exits with a non-zero status.

# --- Configuration ---
BASE_URL="http://127.0.0.1:8000"
BROKER_URL="$BASE_URL/api/v1/broker/IBKRBroker"

# --- Helper Functions ---
header() {
    echo ""
    echo "================================================="
    echo "  $1"
    echo "================================================="
    echo ""
}

# --- Test Execution ---

# 1. Health Check
header "1. Health Check"
curl -s -X GET "$BASE_URL/health" | jq .

# 2. Get Account Info
header "2. Get Account Info"
curl -s -X GET "$BROKER_URL/account-info" | jq .

# 3. Get Positions
header "3. Get Positions"
curl -s -X GET "$BROKER_URL/positions" | jq .

# 4. Get Open Orders (Initial)
header "4. Get Open Orders (Initial)"
curl -s -X GET "$BROKER_URL/open-orders" | jq .

# 5. Place a Market Order
header "5. Place a new Market Order for AAPL"
ORDER_PAYLOAD='{
  "order": {
    "symbol": "AAPL",
    "qty": 1,
    "side": "BUY",
    "order_type": "MKT"
  }
}'

ORDER_RESPONSE=$(curl -s -X POST "$BROKER_URL/order" \
-H "Content-Type: application/json" \
-d "$ORDER_PAYLOAD")

echo "Response from Place Order:"
echo $ORDER_RESPONSE | jq .

ORDER_ID=$(echo $ORDER_RESPONSE | jq -r '.result.order_id')

if [ -z "$ORDER_ID" ] || [ "$ORDER_ID" == "null" ]; then
    echo "Error: Could not get a valid Order ID from the response."
    exit 1
fi

echo -e "\nSuccessfully placed order. Order ID: $ORDER_ID"

# Wait a moment for the order to be registered by the system.
echo -e "\nWaiting 2 seconds for order to register..."
sleep 2

# 6. Get Open Orders (to see the new order)
header "6. Get Open Orders (to confirm new order $ORDER_ID)"
curl -s -X GET "$BROKER_URL/open-orders" | jq .

# 7. Cancel the Placed Order
header "7. Cancel Order ID: $ORDER_ID"
CANCEL_PAYLOAD="{\"order_id\": $ORDER_ID}"

CANCEL_RESPONSE=$(curl -s -X POST "$BROKER_URL/cancel-order" \
-H "Content-Type: application/json" \
-d "$CANCEL_PAYLOAD")

echo "Response from Cancel Order:"
echo $CANCEL_RESPONSE | jq .

# Wait for cancellation to process.
echo -e "\nWaiting 2 seconds for cancellation to process..."
sleep 2

# 8. Get Open Orders (Final check)
header "8. Get Open Orders (Final Check)"
curl -s -X GET "$BROKER_URL/open-orders" | jq .

# --- Strategy Endpoints ---

# 9. List Available Strategies
header "9. List Available Strategies"
curl -s -X GET "$BASE_URL/api/v1/strategies/" | jq .

# 10. List Running Strategies (should be empty)
header "10. List Running Strategies (Initial)"
curl -s -X GET "$BASE_URL/api/v1/strategies/running" | jq .

# 11. Start a Sample Strategy with MockBroker
header "11. Start SampleStrategy with MockBroker"
STRATEGY_PAYLOAD='{
  "name": "SampleStrategy",
  "broker": "MockBroker",
  "params": {
    "symbol": "TSLA",
    "fast_period": 5,
    "slow_period": 10
  }
}'
curl -s -X POST "$BASE_URL/api/v1/strategies/start" \
-H "Content-Type: application/json" \
-d "$STRATEGY_PAYLOAD" | jq .

# 12. List Running Strategies (should contain SampleStrategy)
header "12. List Running Strategies (After Start)"
curl -s -X GET "$BASE_URL/api/v1/strategies/running" | jq .

# 13. Stop the Sample Strategy
header "13. Stop SampleStrategy"
STOP_PAYLOAD='{
  "name": "SampleStrategy"
}'
curl -s -X POST "$BASE_URL/api/v1/strategies/stop" \
-H "Content-Type: application/json" \
-d "$STOP_PAYLOAD" | jq .

# 14. List Running Strategies (should be empty again)
header "14. List Running Strategies (Final)"
curl -s -X GET "$BASE_URL/api/v1/strategies/running" | jq .

echo ""
header "All API tests completed successfully."
echo ""

curl -X POST http://127.0.0.1:8000/api/v1/broker/IBKRBroker/cancel-all-orders 