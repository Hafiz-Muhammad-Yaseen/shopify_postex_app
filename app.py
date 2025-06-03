from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Only required token
POSTEX_TOKEN = os.environ.get('POSTEX_TOKEN') or 'your_postex_token_here'
POSTEX_ORDER_CREATION_URL = "https://api.postex.pk/services/integration/api/order/v3/create-order"

# Sample webhook to receive Shopify orders and send to PostEx
@app.route('/webhook/shopify/order', methods=['POST'])
def handle_shopify_order():
    data = request.json

    # Extract fields from Shopify order payload
    order_id = data.get("id")
    customer = data.get("customer", {})
    shipping_address = data.get("shipping_address", {})
    total_price = data.get("total_price")
    line_items = data.get("line_items", [])

    postex_payload = {
        "cityName": shipping_address.get("city"),
        "customerName": f"{customer.get('first_name', '')} {customer.get('last_name', '')}",
        "customerPhone": shipping_address.get("phone", "03000000000"),  # fallback
        "deliveryAddress": f"{shipping_address.get('address1', '')}, {shipping_address.get('address2', '')}",
        "invoiceDivision": 1,
        "invoicePayment": total_price,
        "items": sum(item.get("quantity", 1) for item in line_items),
        "orderDetail": ", ".join([f"{item['quantity']}x {item['title']}" for item in line_items]),
        "orderRefNumber": str(order_id),
        "orderType": "Normal"
    }

    headers = {
        "token": POSTEX_TOKEN,
        "Content-Type": "application/json"
    }

    try:
        res = requests.post(POSTEX_ORDER_CREATION_URL, json=postex_payload, headers=headers)
        res.raise_for_status()
        tracking_number = res.json().get("dist", {}).get("trackingNumber")

        return jsonify({"message": "Order sent to PostEx", "tracking": tracking_number}), 200
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# PostEx webhook receiver for tracking updates
@app.route('/webhook/postex/tracking', methods=['POST'])
def postex_tracking_webhook():
    data = request.json
    print("Received PostEx Tracking Webhook:", data)
    return "OK", 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
