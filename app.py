from flask import Flask, request, jsonify
from flask_cors import CORS
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from razorpay_webhook import razorpay_webhook_bp  # ✅ Correct import

# Initialize Flask
app = Flask(__name__)
CORS(app)

app.register_blueprint(razorpay_webhook_bp, url_prefix='/webhook')  # ✅ Correct route  # ✅ Register webhook route


# Google Sheets setup
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
client = gspread.authorize(creds)

# Configuration to match the Apps Script
SHEET_ID = '1MwNaqdsGKLIBO60EU84AyvwUX6mspBdrxagFiKSlNQg'
ACTIVE_SHEET = 'ActiveUsers'  # where phone numbers are stored
LINK_CELL = 'E2'  # where the Meet link is stored

@app.route('/')
def home():
    return "✅ Yuj Foundation Class Access App is Running"

@app.route('/verify', methods=['POST'])
def verify_user():
    phone = request.json.get('phone', '').strip()
    print(f"📞 Verifying phone: {phone}")

    if not phone:
        return jsonify({'status': 'error', 'message': 'Phone number required'}), 400

    try:
        sheet = client.open_by_key(SHEET_ID).worksheet(ACTIVE_SHEET)
        numbers = sheet.col_values(1)[1:]  # skip header

        if phone in [num.strip() for num in numbers]:
            print("✅ Phone found in sheet")

            meet_link = sheet.acell(LINK_CELL).value
            if meet_link and meet_link.strip() != "":
                return jsonify({'status': 'success', 'link': meet_link.strip()})
            else:
                return jsonify({'status': 'not_scheduled'})
        else:
            return jsonify({'status': 'not_found'})

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Something went wrong. Please contact support.'}), 500

if __name__ == '__main__':
    app.run(debug=True)
