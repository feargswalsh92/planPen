import json

import quart
import quart_cors
from quart import request

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

app = quart_cors.cors(quart.Quart(__name__), allow_origin="https://chat.openai.com")

@app.get("/logo.png")
async def plugin_logo():
    filename = 'logo.png'
    return await quart.send_file(filename, mimetype='image/png')

@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest():
    host = request.headers['Host']
    with open("./.well-known/ai-plugin.json") as f:
        text = f.read()
        return quart.Response(text, mimetype="text/json")

@app.get("/openapi.yaml")
async def openapi_spec():
    host = request.headers['Host']
    with open("openapi.yaml") as f:
        text = f.read()
        return quart.Response(text, mimetype="text/yaml")

# The scope required to modify Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar.events']

def authenticate_and_get_service():
    flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)

    # This will prompt the user's browser to open a Google login screen
    # After logging in and approving access, the user will be redirected to a local server
    # The server will get the authorization code from the response and continue the flow
    creds = flow.run_local_server(port=8080)
    
    # With the credentials, we can build the service
    service = build('calendar', 'v3', credentials=creds)
    
    return service

@app.route("/create-calendar-event", methods=['POST'])
async def create_calendar_event():
    # Get the event details from the request
    event_details = await request.get_json()
    print('event_details', event_details)

    # Authenticate and get the Google Calendar service
    service = authenticate_and_get_service()
    print('event_details', event_details)

    # Now you can use the service object to create a calendar event
    # You will need to implement the create_event function
    # This function should use the Google Calendar API to create an event with the provided details
    # create_event(service, event_details)

    return quart.Response("Event created successfully", status=200)

def main():
    app.run(debug=True, host="0.0.0.0", port=5003)

# Now you can use the service object to interact with the Google Calendar API

if __name__ == "__main__":
    main()

