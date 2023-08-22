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
def create_tab():
    service = CampaignService()
    if request.method == "POST":
        try:
            kwargs = {**request.get_json()}
            kwargs['user_agent'] = request.headers.get('User-Agent')
            kwargs['ip_address'] = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
            kwargs['referrer'] = kwargs.get('referrer', request.headers.get("Referer"))
            data = service.create_tab(**kwargs)
        except Exception as e:
            return {'error': str(e)}, 400

        return data, 201

@app.route('/tab/<tab_id>', methods=["GET"])
def get_tab(tab_id):
    service = CampaignService()
    if request.method == "GET":
        try:
            data = service.get_tab(tab_id)
        except Exception as e:
            return {'error': str(e)}, 400

        return data, 200
