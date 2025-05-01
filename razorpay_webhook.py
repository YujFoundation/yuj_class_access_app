from flask import Blueprint, request, jsonify, abort
import hmac
import hashlib
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime

# Create Blueprint for webhook
razorpay_webhook_bp = Blueprint('razorpay_webhook', __name__)

# Razorpay webhook secret (must be bytes)
RAZORPAY_SECRET = b'yfpc100#yfpc100#'

# Google Sheets setup
SHEET_ID = '1MwNaqdsGKLIBO60EU84AyvwUX6mspBdrxagFiKSlNQg'
SHEET_NAME = 'PaymentsRaw'
CREDENTIALS_FILE = 'credentials.json'  # Path to your service account JSON

# 🔐 Verify Razorpay webhook signature
def verify_signature(payload, received_signature):
    generated_signature = hmac.new(RAZORPAY_SECRET, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(generated_signature, received_signature)

# 📥 Append validated payment data to Google Sheet
def append_to_sheet(data):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

    sheet.append_row([
        data.get('email', ''),
        data.get('contact', ''),
        data.get('order_id', ''),
        data.get('id', ''),
        float(data.get('amount', 0)) / 100,  # Convert from paise to INR
        data.get('status', ''),
        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ])

# 🚀 Webhook endpoint
@razorpay_webhook_bp.route('/razorpay', methods=['POST'])
def handle_webhook():
    payload = request.data
    signature = request.headers.get('X-Razorpay-Signature')

    if not signature or not verify_signature(payload, signature):
        abort(400, 'Invalid signature')

    data = request.json.get('payload', {}).get('payment', {}).get('entity', {})
    if not data:
        abort(400, 'Invalid payload format')

    append_to_sheet(data)
    return jsonify({'status': 'success'}), 200
