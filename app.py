from flask import Flask, request, jsonify
from flask_cors import CORS
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Setup Google Sheets API
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
client = gspread.authorize(creds)

# ✅ Your actual Sheet ID
SHEET_ID = '1MwNaqdsGKLIBO60EU84AyvwUX6mspBdrxagFiKSlNQg'  # YujFoundation Sheet
ACTIVE_SHEET = 'ActiveUsers'
SETTINGS_SHEET = 'Settings'

@app.route('/')
def home():
    return "✅ Yuj Foundation Class Access App is Running"

@app.route('/verify', methods=['POST'])
def verify_user():
    phone = request.json.get('phone', '').strip()

    if not phone:
        return jsonify({'status': 'error', 'message': 'Phone number required'}), 400

    try:
        # Read active user numbers
        sheet = client.open_by_key(SHEET_ID).worksheet(ACTIVE_SHEET)
        numbers = sheet.col_values(1)[1:]  # skip header row

        if phone in numbers:
            settings = client.open_by_key(SHEET_ID).worksheet(SETTINGS_SHEET)
            meet_link = settings.acell('E2').value.strip()

            if meet_link:
                return jsonify({'status': 'success', 'link': meet_link})
            else:
                return jsonify({'status': 'not_scheduled'})
        else:
            return jsonify({'status': 'not_found'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
