import json
import os 
import openai

import quart
import quart_cors
import pickle
from quart import request
from google_auth_oauthlib.flow import InstalledAppFlow
import datetime
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
    creds = None

    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=8080)

        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    # With the credentials, we can build the service
    service = build('calendar', 'v3', credentials=creds)
    
    return service

@app.route("/create-calendar-event", methods=['POST'])
async def create_calendar_event():
    request_data = await quart.request.get_json()
    print(request_data)
    # Get the event details from the request


    # Authenticate and get the Google Calendar service
    service = authenticate_and_get_service()


        # Get the event details from the request
    event_details = {
        'summary': request_data['title'],
        'location': request_data['location'],
        'start': {
            'dateTime': datetime.datetime.strptime(request_data['date'] + ' ' + request_data['time'], '%Y-%m-%d %H:%M').isoformat(),
        },
        'end': {
            'dateTime': (datetime.datetime.strptime(request_data['date'] + ' ' + request_data['time'], '%Y-%m-%d %H:%M') + datetime.timedelta(hours=int(request_data['duration'].split()[0]))).isoformat(),
        },
    }

    # Create the event
    event = service.events().insert(calendarId='primary', body=event_details).execute()

    # response = get_completion_from_messages(context)
    # print(response)

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

