from flask import Flask, request, send_file, Response
import json
import os
import requests
from pathlib import Path

app = Flask(__name__)

APP_DIR = Path(__file__).parent
CALL_STATE_FILE = APP_DIR / "call_state.json"
TYPED_AUDIO_FILE = APP_DIR / "typed_message.mp3"

WEBHOOK_BASE_URL = "https://profound-vibrancy-production-48fe.up.railway.app"
SIGNALWIRE_NUMBER = "+13183468404"
KATHY_PHONE_NUMBER = "+13184262462"

CONFERENCE_NAME = "kathy_voice_room"

SIGNALWIRE_PROJECT_ID = "547b4293-fd73-480e-809c-85af3ac21004"
SIGNALWIRE_API_TOKEN = "PT726ab6df92adaa8abb79de7e9940748bb77adb0fdc225ecf"
SIGNALWIRE_SPACE_URL = "myvoiceaid.signalwire.com"


def save_call_state(data):
    with open(CALL_STATE_FILE, "w") as f:
        json.dump(data, f)


def load_call_state():
    try:
        with open(CALL_STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {
            "in_call": False,
            "active_call_sid": None,
            "caller_number": None,
            "status": "none"
        }


def call_kathy_into_conference():
    print(">>> CALLING KATHY INTO CONFERENCE")

    if not SIGNALWIRE_PROJECT_ID or not SIGNALWIRE_API_TOKEN or not SIGNALWIRE_SPACE_URL:
        print("!!! Missing SignalWire env vars")
        return None

    url = f"https://{SIGNALWIRE_SPACE_URL}/api/laml/2010-04-01/Accounts/{SIGNALWIRE_PROJECT_ID}/Calls.json"

    payload = {
        "To": KATHY_PHONE_NUMBER,
        "From": SIGNALWIRE_NUMBER,
        "Url": f"{WEBHOOK_BASE_URL}/kathy-join-conference",
        "Method": "GET",
        "StatusCallback": f"{WEBHOOK_BASE_URL}/call-status",
        "StatusCallbackMethod": "POST"
    }

    response = requests.post(
        url,
        data=payload,
        auth=(SIGNALWIRE_PROJECT_ID, SIGNALWIRE_API_TOKEN),
        timeout=15
    )

    print("SignalWire response:", response.status_code, response.text)

    if response.status_code >= 400:
        return None

    try:
        return response.json().get("sid") or response.json().get("Sid")
    except Exception:
        return None


@app.route("/incoming-call", methods=["GET", "POST"])
def incoming_call():
    print(">>> INCOMING CALL HIT")
    print("METHOD:", request.method)
    print("ARGS:", dict(request.args))
    print("FORM:", dict(request.form))

    call_sid = (
        request.values.get("CallSid")
        or request.values.get("call_sid")
        or request.values.get("callsid")
        or request.values.get("Sid")
        or request.values.get("sid")
    )

    caller_number = (
        request.values.get("From")
        or request.values.get("from")
        or request.values.get("Caller")
        or request.values.get("caller")
    )

    kathy_call_sid = call_kathy_into_conference()

    save_call_state({
        "in_call": True,
        "active_call_sid": call_sid,
        "kathy_call_sid": kathy_call_sid,
        "caller_number": caller_number,
        "status": "conference"
    })

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Dial>
        <Conference
            startConferenceOnEnter="true"
            endConferenceOnExit="true">
            {CONFERENCE_NAME}
        </Conference>
    </Dial>
</Response>"""

    return Response(xml, mimetype="text/xml")


@app.route("/kathy-join-conference", methods=["GET", "POST"])
def kathy_join_conference():
    print(">>> KATHY JOIN CONFERENCE HIT")
    print("METHOD:", request.method)
    print("ARGS:", dict(request.args))
    print("FORM:", dict(request.form))

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Dial>
        <Conference
            startConferenceOnEnter="true"
            endConferenceOnExit="true">
            {CONFERENCE_NAME}
        </Conference>
    </Dial>
</Response>"""

    return Response(xml, mimetype="text/xml")


@app.route("/upload-typed-audio", methods=["POST"])
def upload_typed_audio():
    print(">>> UPLOAD TYPED AUDIO HIT")

    audio_bytes = request.get_data()

    if not audio_bytes:
        return "No audio received", 400

    with open(TYPED_AUDIO_FILE, "wb") as f:
        f.write(audio_bytes)

    return "OK", 200


@app.route("/typed-message-cxml", methods=["GET", "POST"])
def typed_message_cxml():
    print(">>> TYPED MESSAGE CXML HIT")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{WEBHOOK_BASE_URL}/typed-message-audio</Play>
    <Redirect method="GET">https://profound-vibrancy-production-48fe.up.railway.app/kathy-join-conference</Redirect>
</Response>"""

    return Response(xml, mimetype="text/xml")


@app.route("/typed-message-audio", methods=["GET"])
def typed_message_audio():
    print(">>> TYPED MESSAGE AUDIO HIT")

    if not TYPED_AUDIO_FILE.exists():
        return "Typed audio file not found", 404

    return send_file(
        TYPED_AUDIO_FILE,
        mimetype="audio/mpeg"
    )

@app.route("/call-status", methods=["GET", "POST"])
def call_status():
    print(">>> CALL STATUS HIT")
    print("METHOD:", request.method)
    print("ARGS:", dict(request.args))
    print("FORM:", dict(request.form))

    call_status = (
        request.values.get("CallStatus")
        or request.values.get("call_status")
        or request.values.get("callstatus")
        or request.values.get("DialCallStatus")
    )

    if call_status in ["completed", "failed", "busy", "no-answer", "canceled"]:
        current_state = load_call_state()
        save_call_state({
            **current_state,
            "in_call": False,
            "active_call_sid": None,
            "kathy_call_sid": None,
            "status": call_status
        })

    return "OK", 200


@app.route("/set-call-state", methods=["POST"])
def set_call_state():
    print(">>> SET CALL STATE HIT")

    call_sid = request.values.get("call_sid")
    caller_number = request.values.get("caller_number")

    save_call_state({
        "in_call": True,
        "active_call_sid": call_sid,
        "caller_number": caller_number,
        "status": "manual"
    })

    return "OK", 200


@app.route("/call-state", methods=["GET"])
def get_call_state():
    return load_call_state(), 200
    
@app.route("/start-kathy-leg", methods=["GET", "POST"])
def start_kathy_leg():
    print(">>> START KATHY LEG HIT")

    kathy_call_sid = call_kathy_into_conference()

    current_state = load_call_state()
    save_call_state({
        **current_state,
        "kathy_call_sid": kathy_call_sid,
        "in_call": True,
        "status": "conference"
    })

    return "OK", 200

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
