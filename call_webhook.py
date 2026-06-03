from flask import Flask, request, send_file, Response
import json
import os
from pathlib import Path

app = Flask(__name__)

APP_DIR = Path(__file__).parent
CALL_STATE_FILE = APP_DIR / "call_state.json"
TYPED_AUDIO_FILE = APP_DIR / "typed_message.mp3"

WEBHOOK_BASE_URL = "https://profound-vibrancy-production-48fe.up.railway.app"

KATHY_PHONE_NUMBER = "+13184264262"


def save_call_state(data):
    with open(CALL_STATE_FILE, "w") as f:
        json.dump(data, f)


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

    save_call_state({
        "in_call": True,
        "active_call_sid": call_sid,
        "caller_number": caller_number,
        "status": "bridging"
    })

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Dial>{KATHY_PHONE_NUMBER}</Dial>
</Response>"""

@app.route("/upload-typed-audio", methods=["POST"])
def upload_typed_audio():
    print(">>> UPLOAD TYPED AUDIO HIT")

    audio_bytes = request.get_data()

    if not audio_bytes:
        return "No audio received", 400

    with open(TYPED_AUDIO_FILE, "wb") as f:
        f.write(audio_bytes)

    return "OK", 200


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
        save_call_state({
            "in_call": False,
            "active_call_sid": None,
            "caller_number": None,
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
    try:
        with open(CALL_STATE_FILE, "r") as f:
            data = json.load(f)
    except Exception:
        data = {
            "in_call": False,
            "active_call_sid": None,
            "caller_number": None,
            "status": "none"
        }

    return data, 200


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
