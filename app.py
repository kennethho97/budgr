import os
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv

import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.institutions_get_request import InstitutionsGetRequest
from plaid.configuration import Configuration
from plaid.api_client import ApiClient
from plaid.exceptions import ApiException

# Load .env variables
load_dotenv()

PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
env = os.getenv("PLAID_ENV", "sandbox").lower()

# Correct Plaid Environment mapping (only sandbox and production are supported in v10)
PLAID_ENV = {
    "sandbox": plaid.Environment.Sandbox,
    "production": plaid.Environment.Production
}[env]

# Set up Plaid client
configuration = Configuration(
    host=PLAID_ENV,
    api_key={
        'clientId': PLAID_CLIENT_ID,
        'secret': PLAID_SECRET,
    }
)
api_client = ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

# Create Flask app
app = Flask(__name__)

# Public-facing homepage
@app.route('/')
def home():
    return render_template('home.html')

# Route to serve index.html (Plaid Link test page)
@app.route('/link')
def link():
    return render_template('index.html')

# Endpoint: Return a new link token
@app.route('/api/create_link_token', methods=['GET'])
def create_link_token():
    try:
        request = LinkTokenCreateRequest(
            user=LinkTokenCreateRequestUser(client_user_id="budgr-123"),
            client_name="Budgr",
            products=[Products("transactions")],
            country_codes=[CountryCode("US")],
            language="en"
        )
        response = client.link_token_create(request)
        return jsonify({'link_token': response['link_token']})
    except ApiException as e:
        return jsonify({
            "error": {
                "status_code": e.status,
                "message": e.body,
                "reason": e.reason
            }
        }), 500

# Endpoint: List available institutions (to confirm access level)
@app.route('/api/list_institutions')
def list_institutions():
    try:
        request = InstitutionsGetRequest(
            country_codes=[CountryCode("US")],
            count=10,
            offset=0
        )
        response = client.institutions_get(request)
        institutions = [{"name": inst.name, "id": inst.institution_id} for inst in response.institutions]
        return jsonify(institutions)
    except ApiException as e:
        return jsonify({
            "error": {
                "status_code": e.status,
                "message": e.body,
                "reason": e.reason
            }
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
