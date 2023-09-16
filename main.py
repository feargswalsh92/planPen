import os
import pickle
import logging
import datetime
import time
from typing import Dict
from quart import Quart, request, send_file, Response, redirect
from quart_cors import cors
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from pluginlab_admin import App

app = App(
    secret_key=os.getenv('PLUGINLAB_SECRET'),
    plugin_id="5946f3207938eda5df21fb091c517e1c",
)

# to manage auth-related stuff, mostly members
auth = app.get_auth()


app = cors(Quart(__name__), allow_origin="https://chat.openai.com")

SCOPES = ['https://www.googleapis.com/auth/calendar.events']
logger = logging.getLogger(__name__)


@app.get("/logo.png")
async def plugin_logo():
    return await send_file('logo.png', mimetype='image/png')

@app.get("/legal")
async def legal_page():
    return await send_file('legal.html', mimetype='text/html')

@app.get("/privacy_policy")
async def privacy_policy():
    return await send_file('privacy_policy.html', mimetype='text/html')


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
    try:
        request_data = await request.get_json()
        print("Request Headers:", request.headers)
    
        time_zone = time.tzname[0]
    
        authorization_header = request.headers.get('Authorization')
        mem_id = request.headers.get('X-Pluginlab-User-Id')
        print(mem_id)
        if authorization_header:
          token = authorization_header.split("Bearer ")[1]
        else:
          token = None
        
        # payload = auth.verify_token(token)
    
        try :
             refreshed_identities = auth.refresh_member_identity_token(mem_id, "google")
        except Exception as error:
            print('error', error)
            print('auth', auth)
        
    
        identities = auth.get_member_identities(mem_id)
    
        print('refresh_token', identities.google.refresh_token)
    
        # refreshed_identity = auth.refresh_member_identity_token(mem_id, "google")
    
        if(identities.google is None):
          return
        creds = Credentials(
            token=identities.google.access_token,
            refresh_token=identities.google.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv('GOOGLE_CLIENT_ID'),
            client_secret=os.getenv('GCP_SECRET')
        )
    
        service = build('calendar', 'v3', credentials=creds)
        event_details = {
            'summary': request_data['title'],
            'location': request_data['location'],
            'start': {
                'dateTime': datetime.datetime.strptime(request_data['date'] + ' ' + request_data['time'],
                                                       '%m-%d-%Y %H:%M').isoformat(),
                'timeZone': time_zone,
            },
            'end': {
                'dateTime': (
                        datetime.datetime.strptime(request_data['date'] + ' ' + request_data['time'],
                                                   '%m-%d-%Y %H:%M') + datetime.timedelta(
                    hours=int(request_data['duration'].split()[0]))).isoformat(),
                'timeZone': time_zone,
            },
        }
    
        
    
        event = service.events().insert(calendarId='primary', body=event_details).execute()
        html_link = event.get('htmlLink', 'Link not found')
        # logger.info("Event created successfully")
    
        return Response(f"Event created successfully, you can view it here {html_link}", status=200)

    except KeyError as e:
        return Response(f"Missing key in request data: {e}", status=400)
    except ValueError as e:
        return Response(f"Value error: {e}", status=400)
    except Exception as e:
        return Response(f"An unexpected error occurred: {e}", status=500)

def main():
    app.run(debug=False, host="0.0.0.0")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
