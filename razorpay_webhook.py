from flask import Blueprint, request, jsonify, abort
import hmac
import hashlib
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import traceback

razorpay_webhook_bp = Blueprint('razorpay_webhook', __name__)

RAZORPAY_SECRET = b'yfpc100#yfpc100#'
SHEET_ID = '1MwNaqdsGKLIBO60EU84AyvwUX6mspBdrxagFiKSlNQg'
SHEET_NAME = 'PaymentsRaw'
CREDENTIALS_FILE = 'service_account.json'

def verify_signature(payload, received_signature):
    try:
        generated_signature = hmac.new(RAZORPAY_SECRET, payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(generated_signature, received_signature)
    except Exception as e:
        print(f"❌ Signature verification failed: {e}")
        return False

def append_dynamic_row(data):
    try:
        print("📥 Connecting to Google Sheet...")
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

        headers = sheet.row_values(1)
        if not headers:
            headers = list(data.keys())
            headers.append('timestamp')
            sheet.append_row(headers)
            print("✅ Headers added:", headers)

        row = [str(data.get(h, '')) for h in headers[:-1]]
        row.append(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        sheet.append_row(row)
        print("✅ Data row added:", row)

    except Exception as e:
        print(f"❌ Error while appending to Google Sheet:\n{traceback.format_exc()}")

@razorpay_webhook_bp.route('/razorpay', methods=['POST'])
def handle_webhook():
    try:
        print("⚡ Razorpay webhook triggered")
        payload = request.data
        signature = request.headers.get('X-Razorpay-Signature')

        if not signature or not verify_signature(payload, signature):
            print("❌ Invalid Razorpay Signature")
            abort(400, 'Invalid signature')

        data = request.json.get('payload', {}).get('payment', {}).get('entity', {})
        if not data:
            print("❌ Invalid payload structure")
            abort(400, 'Invalid payload format')

        print("📦 Parsed Razorpay payment data:", data)
        append_dynamic_row(data)

        return jsonify({'status': 'success'}), 200

    except Exception as e:
        print(f"❌ Webhook processing error:\n{traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': 'Webhook processing failed'}), 500
