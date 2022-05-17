import os
from flask import Flask, request
from flask_cors import CORS
from services import CampaignService

app = Flask(__name__)
CORS(app)


@app.route('/campaign/<slug>', methods=['GET'])
def campaign(slug: str):
    service = CampaignService()
    data = service.get_campaign(slug)

    return data, 200

@app.route('/tab', methods=["POST"])
def tab():
    service = CampaignService()
    if request.method == "POST":
        try:
            data = service.create_tab(**request.get_json())
        except Exception as e:
            return {'error': str(e)}, 400

        return data, 201
