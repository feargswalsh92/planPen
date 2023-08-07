import os
import pickle
import logging
import datetime
from typing import Dict
from quart import Quart, request, send_file, Response, redirect
from quart_cors import cors
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

app = cors(Quart(__name__), allow_origin="https://chat.openai.com")

SCOPES = ['https://www.googleapis.com/auth/calendar.events']
logger = logging.getLogger(__name__)


@app.get("/logo.png")
async def plugin_logo():
    return await send_file('logo.png', mimetype='image/png')


@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest():
    with open("./.well-known/ai-plugin.json") as f:
        return Response(f.read(), mimetype="text/json")


@app.get("/openapi.yaml")
async def openapi_spec():
    with open("openapi.yaml") as f:
        return Response(f.read(), mimetype="text/yaml")


def authenticate_and_get_service() -> str:
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            client_config = {
                "installed": {
                    "client_id": os.getenv('GOOGLE_CLIENT_ID'),
                    "project_id": "calendarwizard-387304",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_secret": os.getenv('GCP_SECRET'),
                    "redirect_uri": 'https://6481149ef84208702f5388ab89672ef9.auth.portal-pluginlab.ai/oauth/handler',
                    "scope": ['https://www.googleapis.com/auth/calendar.events'],
                },
            }

            flow = Flow.from_client_config(client_config, SCOPES)
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true')

            return authorization_url

    service = build('calendar', 'v3', credentials=creds)
    return service


@app.route("/create-calendar-event", methods=['POST'])
async def create_calendar_event():
    request_data = await request.get_json()

    # service = authenticate_and_get_service()
    # if isinstance(service, str):
    #     print('is string')
    #     print(service)
    #     return redirect(service)

    event_details = {
        'summary': request_data['title'],
        'location': request_data['location'],
        'start': {
            'dateTime': datetime.datetime.strptime(request_data['date'] + ' ' + request_data['time'],
                                                   '%Y-%m-%d %H:%M').isoformat(),
        },
        'end': {
            'dateTime': (
                    datetime.datetime.strptime(request_data['date'] + ' ' + request_data['time'],
                                               '%Y-%m-%d %H:%M') + datetime.timedelta(
                hours=int(request_data['duration'].split()[0]))).isoformat(),
        },
    }

    event = service.events().insert(calendarId='primary', body=event_details).execute()
    # logger.info("Event created successfully")

    return Response("Event created successfully", status=200)

@app.get("/oauth")
async def oauth():
    query_string = request.query_string.decode('utf-8')
    parts = query_string.split('&')
    kvps = {}
    for part in parts:
        k, v = part.split('=')
        v = v.replace("%2F", "/").replace("%3A", ":")
        kvps[k] = v
    print("OAuth key value pairs from the ChatGPT Request: ", kvps)
    url = kvps["redirect_uri"] + f"?code={OPENAI_CODE}"
    print("URL: ", url)
    return quart.Response(
        f'<a href="{url}">Click to authorize</a>'
    )

# Sample names
OPENAI_CLIENT_ID = "id"
OPENAI_CLIENT_SECRET = "secret"
OPENAI_CODE = "abc123"
OPENAI_TOKEN = "def456"

@app.post("/auth/oauth_exchange")
async def oauth_exchange():
    request = await quart.request.get_json(force=True)
    print(f"oauth_exchange {request=}")

    if request["client_id"] != OPENAI_CLIENT_ID:
        raise RuntimeError("bad client ID")
    if request["client_secret"] != OPENAI_CLIENT_SECRET:
        raise RuntimeError("bad client secret")
    if request["code"] != OPENAI_CODE:
        raise RuntimeError("bad code")

    return {
        "access_token": OPENAI_TOKEN,
        "token_type": "bearer"
    }



def main():
    app.run(debug=False, host="0.0.0.0")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
