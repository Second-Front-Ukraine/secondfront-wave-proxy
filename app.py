import os
from flask import Flask
from flask_cors import CORS
from services import CampaignService

app = Flask(__name__)
CORS(app)


@app.route('/campaign/<slug>')
def get_campaign(slug: str):
    data = CampaignService().get_campaign(slug)

    return data

@app.route('/invoice')
def create_invoice():
    pass

@app.route('/account')
def get_account():
    pass
