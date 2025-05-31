from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

POSTEX_API_KEY = os.getenv("POSTEX_API_KEY")
WHATSAPP_API_URL = "https://api.ultramsg.com/instanceID/messages/chat"
WHATSAPP_TOKEN = os.getenv("ULTRAMSG_TOKEN")

@app.route("/webhook/orders", methods=["POST"])
def handle_order():
    data = request.get_json()

    name = data["customer"]["first_name"]
    phone = data["customer"]["phone"]
    address = data["shipping_address"]["address1"]
    city = data["shipping_address"]["city"]
    amount = data["total_price"]
    order_id = data["id"]
    items = data["line_items"]

    product_list = [{"name": i["title"], "qty": i["quantity"]} for i in items]

    postex_payload = {
        "customer_name": name,
        "customer_phone": phone,
        "address": f"{address}, {city}",
        "city": city,
        "cod_amount": amount,
        "products": product_list,
        "client_reference": f"shopify_{order_id}"
    }

    postex_res = requests.post(
        "https://api.postex.pk/v1/order",
        json=postex_payload,
        headers={"Authorization": f"Bearer {POSTEX_API_KEY}"}
    )

    if postex_res.status_code != 200:
        return jsonify({"error": "PostEx failed"}), 500

    tracking = postex_res.json().get("tracking_number")

    message = f"Hi {name}, your order #{order_id} has been placed via PostEx. Tracking: {tracking}"
    whatsapp_payload = {"token": WHATSAPP_TOKEN, "to": phone, "body": message}

    whats_res = requests.post(WHATSAPP_API_URL, json=whatsapp_payload)

    if whats_res.status_code != 200:
        return jsonify({"error": "WhatsApp failed"}), 500

    return jsonify({"message": "Order sent to PostEx and WhatsApp!"})

if __name__ == "__main__":
    app.run()
