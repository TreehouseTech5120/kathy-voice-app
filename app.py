import base64
import streamlit as st
from elevenlabs.client import ElevenLabs

st.set_page_config(page_title="Kathy Voice App", layout="wide")

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

if "current_contact" not in st.session_state:
    st.session_state.current_contact = ""

if "last_spoken" not in st.session_state:
    st.session_state.last_spoken = ""

contacts = {
    "Barbara": "+1XXXXXXXXXX",
    "Greg": "+1XXXXXXXXXX",
    "Becky": "+1XXXXXXXXXX",
    "Alicia": "+1XXXXXXXXXX",
}

favorites = [
    "Just a Sec",
    "I'll find out and let you know",
    "I love you",
    "Yep",
    "No",
    "Sounds Good"
]

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
    audio_base64 = base64.b64encode(audio_bytes).decode()
    st.markdown(
        f"""
        <audio autoplay>
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
        </audio>
        """,
        unsafe_allow_html=True
    )

def speak_text(text):
    st.session_state.last_spoken = text
    audio_bytes = generate_audio_cached(text)
    play_audio(audio_bytes)

# ----------------------------
# CALL CONTROL
# ----------------------------

if not st.session_state.in_call:
    st.subheader("Start a Call")

    selected_contact = st.selectbox(
        "Select Contact",
        [""] + list(contacts.keys())
    )

    manual_number = st.text_input(
        "Or Enter Phone Number",
        placeholder="+12085551234"
    )

    if st.button("Start Call", use_container_width=True):
        if selected_contact:
            st.session_state.current_contact = selected_contact
            st.session_state.in_call = True
            st.rerun()
        elif manual_number:
            st.session_state.current_contact = manual_number
            st.session_state.in_call = True
            st.rerun()
        else:
            st.warning("Select a contact or enter a phone number.")
else:
    st.markdown(f"## 📞 On Call With: {st.session_state.current_contact}")

    if st.button("End Call", use_container_width=True):
        st.session_state.in_call = False
        st.session_state.current_contact = ""
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

st.subheader("Emergency")
emergency_cols = st.columns(3)

for i, phrase in enumerate(emergency_phrases):
    with emergency_cols[i % 3]:
        if st.button(phrase, use_container_width=True, key=f"emergency_{phrase}"):
            speak_text(phrase)

st.markdown("---")

top_cols = st.columns([3, 1])

with top_cols[0]:
    st.subheader("Favorites")

with top_cols[1]:
    if st.session_state.last_spoken:
        if st.button("Repeat Last", use_container_width=True):
            speak_text(st.session_state.last_spoken)

fav_cols = st.columns(3)

for i, phrase in enumerate(favorites):
    with fav_cols[i % 3]:
        if st.button(phrase, use_container_width=True, key=f"fav_{phrase}"):
            speak_text(phrase)

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
text_input = st.text_area("Type here:", height=140, key="text_input")

col_a, col_b = st.columns([3, 1])

with col_a:
    if st.button("Speak", use_container_width=True):
        final_text = st.session_state.text_input.strip()
        if final_text:
            speak_text(final_text)
        else:
            st.warning("Please type something first.")

with col_b:
    if st.button("Clear", use_container_width=True):
        st.session_state.text_input = ""
        st.rerun()
