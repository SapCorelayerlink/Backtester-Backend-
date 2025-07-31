import requests
import time
import json

BASE_URL = "http://127.0.0.1:8000/api/v1/broker/IBKRBroker"

def print_response(name, response):
    """Helper function to print API responses."""
    print(f"--- {name} ---")
    try:
        print(f"Status Code: {response.status_code}")
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2))
    except json.JSONDecodeError:
        print("Response Text:")
        print(response.text)
    print("-" * (len(name) + 8))
    print()

def test_ibkr_api():
    """Main function to test all IBKR API endpoints."""
    
    # 1. Get Account Info
    print("Testing: Get Account Info")
    try:
        response = requests.get(f"{BASE_URL}/account-info")
        print_response("Get Account Info", response)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

    # 2. Get Positions
    print("Testing: Get Positions")
    try:
        response = requests.get(f"{BASE_URL}/positions")
        print_response("Get Positions", response)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

    # 3. Get Open Orders
    print("Testing: Get Open Orders (before placing new order)")
    try:
        response = requests.get(f"{BASE_URL}/open-orders")
        print_response("Get Open Orders (Initial)", response)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

    # 4. Place a test order
    print("Testing: Place Order")
    order_to_place = {
        "order": {
            "symbol": "AAPL",
            "qty": 1,
            "side": "BUY",
            "order_type": "MKT"
        }
    }
    placed_order_id = None
    try:
        response = requests.post(f"{BASE_URL}/order", json=order_to_place)
        print_response("Place Order", response)
        if response.status_code == 200:
            response_data = response.json()
            result = response_data.get("result")
            if result and result.get("order_id"):
                placed_order_id = result["order_id"]
                print(f"Successfully placed order with ID: {placed_order_id}")
            else:
                print("Order placement did not return an order_id.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

    if not placed_order_id:
        print("\nCould not place order, skipping cancel test.")
        return

    # Give the order time to register
    print("\nWaiting 2 seconds for order to register...")
    time.sleep(2)

    # 5. Get Open Orders again to see the new order
    print("Testing: Get Open Orders (after placing new order)")
    try:
        response = requests.get(f"{BASE_URL}/open-orders")
        print_response("Get Open Orders (Updated)", response)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


    # 6. Cancel the order
    print(f"Testing: Cancel Order (ID: {placed_order_id})")
    cancel_req = {"order_id": placed_order_id}
    try:
        response = requests.post(f"{BASE_URL}/cancel-order", json=cancel_req)
        print_response("Cancel Order", response)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

    # 7. Final check of open orders
    print("\nWaiting 2 seconds for cancellation to process...")
    time.sleep(2)
    print("Testing: Get Open Orders (after canceling order)")
    try:
        response = requests.get(f"{BASE_URL}/open-orders")
        print_response("Get Open Orders (Final)", response)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    test_ibkr_api() 