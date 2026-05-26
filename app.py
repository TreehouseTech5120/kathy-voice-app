import base64
import json
import os
import requests
import streamlit as st
import time
from pathlib import Path
APP_DIR = Path(__file__).parent
TYPED_AUDIO_FILE = APP_DIR / "typed_message.mp3"
CALL_STATE_FILE = APP_DIR / "call_state.json"
from streamlit_autorefresh import st_autorefresh
from requests.auth import HTTPBasicAuth
from elevenlabs.client import ElevenLabs
SIGNALWIRE_SPACE = "myvoiceaid"
SIGNALWIRE_PROJECT_ID = "547b4293-fd73-480e-809c-85af3ac21004"
SIGNALWIRE_API_TOKEN = "PT726ab6df92adaa8abb79de7e9940748bb77adb0fdc225ecf"
SIGNALWIRE_FROM_NUMBER = "+13183468404"

SIGNALWIRE_BASE_URL = (
    f"https://{SIGNALWIRE_SPACE}.signalwire.com/api/laml/2010-04-01/"
    f"Accounts/{SIGNALWIRE_PROJECT_ID}"
)
def check_for_active_webhook_call():
    WEBHOOK_BASE_URL = "https://profound-vibrancy-production-48fe.up.railway.app"

    try:
        response = requests.get(f"{WEBHOOK_BASE_URL}/call-state", timeout=5)

        if response.status_code != 200:
            return

        data = response.json()

        if data.get("in_call"):
            st.session_state.in_call = True
            st.session_state.active_call_sid = data.get("active_call_sid")
            st.session_state.current_contact = data.get("caller_number", "Unknown Caller")
            st.session_state.mode = "call"

    except Exception:
        return
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    button {
        height: 90px !important;
        font-size: 22px !important;
        border-radius: 15px !important;
    }

    textarea {
        font-size: 22px !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Kathy Voice App")

VOICE_ID = "Z6M3ubAywLVnfDsgdx17"
api_key = "54a1338ac3c251f013476ce31fac0d320d9657f0a37718283ebe8fe2a72425fa"
client = ElevenLabs(api_key=api_key)

if "in_call" not in st.session_state:
    st.session_state.in_call = False

if "active_call_sid" not in st.session_state:
    st.session_state.active_call_sid = ""

if "current_contact" not in st.session_state:
    st.session_state.current_contact = ""

if "last_spoken" not in st.session_state:
    st.session_state.last_spoken = ""

if not st.session_state.in_call:
    st_autorefresh(interval=10000, key="call_check")

contacts = {
    "Barbara": "+13184263882",
    "Greg": "+12082469929",
    "Becky": "+1XXXXXXXXXX",
    "Alicia": "+1XXXXXXXXXX",
}

favorites = [
    "Hello this is Kathy",
    "Please be patient",
    "Just a Sec",
    "I'll find out and let you know",
    "I love you",
    "Yes",
    "No",
    "Sounds Good"
]

favorite_laml_urls = {
    "Sounds Good": "https://myvoiceaid.signalwire.com/laml-bins/7b6470b0-9a15-445f-a58a-5add02879cbb",
    "I'll find out and let you know": "https://myvoiceaid.signalwire.com/laml-bins/b94c7312-9aa6-4a52-a549-918fde3e99b3",
    "Just a Sec": "https://myvoiceaid.signalwire.com/laml-bins/b946d5e4-6b1e-4d6c-8890-f996dac62ec5",
    "Yes":  "https://myvoiceaid.signalwire.com/laml-bins/a368e8f1-10c4-4bb0-8de1-42d8725f2439",
    "No": "https://myvoiceaid.signalwire.com/laml-bins/02e864eb-0e76-42a8-a725-14b723b5e78f",
    "I love you": "https://myvoiceaid.signalwire.com/laml-bins/19e9cf92-5e2e-437c-b803-bee209fbd002",
    "Hello this is Kathy": "https://myvoiceaid.signalwire.com/laml-bins/ea131563-0bdc-439f-8850-67c7882536cd",
    "Please be patient": "https://myvoiceaid.signalwire.com/laml-bins/88b4a2b5-d946-4ade-a8ae-31d1af70ad38"

}

categories = {
    "Basic": ["Yes", "No", "I need help", "Give me a minute"],
    "Feelings": ["I'm okay", "I'm tired", "I'm frustrated"],
    "Family": ["I love you", "Thank you", "Come here please"],
    "Needs": ["Water please", "Bathroom please", "Please adjust me"]
}

emergency_phrases = [
    "I need help now",
    "Please come here now",
    "Call 911"
]

@st.cache_data
def generate_audio_cached(text):
    audio = client.text_to_speech.convert(
        voice_id=VOICE_ID,
        model_id="eleven_multilingual_v2",
        text=text,
        output_format="mp3_44100_128",
        voice_settings={
            "stability": 0.7,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True,
            "speed": 1.15
        }
    )
    return b"".join(audio)

def play_audio(audio_bytes):
    import time

    audio_base64 = base64.b64encode(audio_bytes).decode()
    player_id = int(time.time() * 1000)

    st.markdown(
        f"""
        <audio id="audio_{player_id}" autoplay>
            <source src="data:audio/mp3;base64,{audio_base64}#t={player_id}" type="audio/mp3">
        </audio>
        """,
        unsafe_allow_html=True
    )
def speak_text(text):
    st.session_state.last_spoken = text
    audio_bytes = generate_audio_cached(text)
    play_audio(audio_bytes)

def start_signalwire_call(to_number):
    url = f"{SIGNALWIRE_BASE_URL}/Calls.json"

    payload = {
        "From": SIGNALWIRE_FROM_NUMBER,
        "To": to_number,
        "Url": "https://myvoiceaid.signalwire.com/laml-bins/a7422232-1e29-46c1-921b-63a94a1c6b8e"
    }

    response = requests.post(
        url,
        data=payload,
        auth=HTTPBasicAuth(SIGNALWIRE_PROJECT_ID, SIGNALWIRE_API_TOKEN)
    )

    if response.status_code not in [200, 201]:
        st.error(f"SignalWire call error: {response.status_code} {response.text}")
        return None

    data = response.json()
    call_sid = data.get("sid") or data.get("Sid") or data.get("call_sid") or data.get("id")

    if call_sid:
        st.session_state.active_call_sid = call_sid
        st.session_state.in_call = True
        st.session_state.current_contact = to_number
        st.session_state.mode = "call"

    return call_sid

def play_laml_on_active_call(play_laml_url):
    if not st.session_state.active_call_sid:
        st.warning("No active call yet.")
        return

    call_sid = st.session_state.active_call_sid
    url = f"{SIGNALWIRE_BASE_URL}/Calls/{call_sid}.json"

    payload = {
        "Url": play_laml_url,
        "Method": "GET"
    }

    response = requests.post(
        url,
        data=payload,
        auth=HTTPBasicAuth(SIGNALWIRE_PROJECT_ID, SIGNALWIRE_API_TOKEN)
    )

    if response.status_code not in [200, 201]:
        st.error(f"SignalWire update error: {response.status_code} {response.text}")
    else:
        st.success("Sent audio to active call.")

def play_typed_text_on_active_call(text):
    if not st.session_state.active_call_sid:
        st.warning("No active call.")
        return

    audio_bytes = generate_audio_cached(text)

    with open(TYPED_AUDIO_FILE, "wb") as f:
        f.write(audio_bytes)

    upload_response = requests.post(
        "https://profound-vibrancy-production-48fe.up.railway.app/upload-typed-audio",
        data=audio_bytes,
        headers={"Content-Type": "audio/mpeg"}
    )

    if upload_response.status_code != 200:
        st.error(f"Could not upload typed audio: {upload_response.status_code} {upload_response.text}")
        return

    time.sleep(1)

    WEBHOOK_BASE_URL = "https://profound-vibrancy-production-48fe.up.railway.app"

    play_typed_message_cxml_url = f"{WEBHOOK_BASE_URL}/typed-message-cxml"

    call_sid = st.session_state.active_call_sid
    url = f"{SIGNALWIRE_BASE_URL}/Calls/{call_sid}.json"

    payload = {
        "Url": play_typed_message_cxml_url,
        "Method": "GET"
    }

    response = requests.post(
        url,
        data=payload,
        auth=HTTPBasicAuth(SIGNALWIRE_PROJECT_ID, SIGNALWIRE_API_TOKEN)
    )

    if response.status_code not in [200, 201]:
        st.error(f"SignalWire update error: {response.status_code} {response.text}")
    else:
        st.success("Typed message sent to active call.")
def get_latest_active_outbound_call(to_number):
    url = f"{SIGNALWIRE_BASE_URL}/Calls.json"

    response = requests.get(
        url,
        auth=HTTPBasicAuth(SIGNALWIRE_PROJECT_ID, SIGNALWIRE_API_TOKEN)
    )

    if response.status_code not in [200, 201]:
        st.error(f"Could not check outbound calls: {response.status_code} {response.text}")
        return None

    data = response.json()
    calls = data.get("calls", [])

    for call in calls:
        direction = call.get("direction", "").lower()
        status = call.get("status", "").lower()
        to_field = call.get("to", "") or call.get("To", "")

        if (
            "outbound" in direction
            and to_number in to_field
            and status in ["queued", "ringing", "in-progress", "answered"]
        ):
            return call.get("sid") or call.get("Sid")

    return None

CALL_STATE_FILE = r"C:\Users\Reuseum\Desktop\Voice App\call_state.json"

def load_call_state():
    if os.path.exists(CALL_STATE_FILE):
        with open(CALL_STATE_FILE, "r") as f:
            data = json.load(f)

        st.session_state.active_call_sid = data.get("active_call_sid", "")
        st.session_state.in_call = data.get("in_call", False)
        st.session_state.current_contact = data.get("caller_number", "Unknown Caller")

def save_call_state(call_sid, contact, direction="outbound"):
    with open(CALL_STATE_FILE, "w") as f:
        json.dump({
            "active_call_sid": call_sid,
            "in_call": False,
            "status": "active",
            "direction": direction,
            "caller_number": contact
        }, f)

def sync_call_state_from_file():
    try:
        with open("call_state.json", "r") as f:
            state = json.load(f)

        if state.get("in_call"):
            st.session_state.in_call = True
            st.session_state.active_call_sid = state.get("active_call_sid")
            st.session_state.caller_number = state.get("caller_number")
    except FileNotFoundError:
        pass
    except Exception as e:
        st.warning(f"Could not read call state: {e}")

def clear_call_state():
    if os.path.exists(CALL_STATE_FILE):
        os.remove(CALL_STATE_FILE)

    st.session_state.in_call = False
    st.session_state.active_call_sid = ""
    st.session_state.current_contact = ""

load_call_state()

sync_call_state_from_file()

check_for_active_webhook_call()

# ----------------------------
# CALL CONTROL
# ----------------------------

if True:
    st.subheader("Start a Call")

    selected_contact = st.selectbox(
        "Select Contact",
        [""] + list(contacts.keys())
    )

    manual_number = st.text_input(
        "Or Enter Phone Number",
        placeholder="+12085551234"
    )

    if st.button("📞 Start Call", use_container_width=True):
        if selected_contact:
            phone_number_to_call = contacts[selected_contact]
        elif manual_number:
            phone_number_to_call = manual_number
        else:
            st.warning("Select a contact or enter a phone number.")
            st.stop()

        call_sid = start_signalwire_call(phone_number_to_call)

        if not call_sid:
            call_sid = get_latest_active_outbound_call(phone_number_to_call)

        if call_sid:
            st.success(f"GOT CALL SID: {call_sid}")

    requests.post(
        "https://profound-vibrancy-production-48fe.up.railway.app/set-call-state",
        data={
            "call_sid": call_sid,
            "caller_number": phone_number_to_call
        }
    )

    st.session_state.active_call_sid = call_sid
    st.session_state.current_contact = phone_number_to_call
    st.session_state.in_call = True
    st.session_state.mode = "call"

    st.success("Outbound call connected.")
    st.rerun()
else:
    st.error("Call started, but I could not find the active outbound call SID.")
        else:
    current_contact = st.session_state.get("current_contact", "Unknown Caller")
    st.markdown(f"## 📞 On Call With: {current_contact}")

    if st.button("End Call", use_container_width=True):
        clear_call_state()
        st.success("Call session ended.")
        st.rerun()
    
st.markdown("---")

# ----------------------------
# SHARED COMMUNICATION SCREEN
# Works in person OR during call
# ----------------------------

if st.session_state.in_call:
    st.success("Call Mode Active")
else:
    st.info("In-Person Mode")

fav_cols = st.columns(3)

for i, phrase in enumerate(favorites):

    with fav_cols[i % 3]:

        if st.button(
            phrase,
            use_container_width=True,
            key=f"call_fav_{phrase}"
        ):

            if (
                st.session_state.in_call
                and phrase in favorite_laml_urls
            ):

                play_laml_on_active_call(
                    favorite_laml_urls[phrase]
                )

            else:

                speak_text(phrase)
st.markdown("---")

st.markdown("---")

st.subheader("Quick Phrases")
category = st.selectbox("Category", list(categories.keys()))
phrases = categories[category]

phrase_cols = st.columns(3)

for i, phrase in enumerate(phrases):
    with phrase_cols[i % 3]:
        if st.button(phrase, use_container_width=True, key=f"cat_{category}_{phrase}"):
            speak_text(phrase)

st.markdown("---")
st.subheader("Type Message")

if "text_box_counter" not in st.session_state:
    st.session_state.text_box_counter = 0

text_key = f"typed_message_box_{st.session_state.text_box_counter}"

typed_message = st.text_area(
    "Type here:",
    height=150,
    key=text_key
)

col_a, col_b = st.columns([3, 1])

with col_a:
    if st.button("Speak Typed Message", use_container_width=True):
        final_text = typed_message.strip()

        if final_text:
            if st.session_state.in_call:
                play_typed_text_on_active_call(final_text)
            else:
                speak_text(final_text)
        else:
            st.warning("Please type a message first.")

with col_b:
    if st.button("Clear Text", use_container_width=True):
        st.session_state.text_box_counter += 1
        st.rerun()
