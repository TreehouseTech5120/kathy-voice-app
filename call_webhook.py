from flask import Flask, request, send_file
import json
import os
from pathlib import Path

app = Flask(__name__)

APP_DIR = Path(__file__).parent
CALL_STATE_FILE = APP_DIR / "call_state.json"
TYPED_AUDIO_FILE = APP_DIR / "typed_message.mp3"

WEBHOOK_BASE_URL = "https://profound-vibrancy-production-48fe.up.railway.app"

INTRO_AUDIO_URL = "https://github.com/TreehouseTech5120/kathy-voice-app/raw/refs/heads/main/Hi%20this%20is%20Kathy.mp3"


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

    with open(CALL_STATE_FILE, "w") as f:
        json.dump({
            "in_call": True,
            "active_call_sid": call_sid,
            "caller_number": caller_number
        }, f)

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{INTRO_AUDIO_URL}</Play>
    <Pause length="600"/>
</Response>""", 200, {"Content-Type": "text/xml"}


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

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{WEBHOOK_BASE_URL}/typed-message-audio</Play>
    <Pause length="600"/>
</Response>""", 200, {"Content-Type": "text/xml"}


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
    )

    if call_status in ["completed", "failed", "busy", "no-answer", "canceled"]:
        with open(CALL_STATE_FILE, "w") as f:
            json.dump({
                "in_call": False,
                "active_call_sid": None,
                "caller_number": None,
                "status": call_status
            }, f)

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
            "caller_number": None
        }

    return data, 200


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
