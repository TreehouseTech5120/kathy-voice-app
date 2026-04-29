import streamlit as st
from elevenlabs.client import ElevenLabs

st.set_page_config(page_title="Kathy Voice App", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    button {
        height: 100px !important;
        font-size: 24px !important;
        border-radius: 15px !important;
    }

    textarea {
        font-size: 22px !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Kathy Voice App")

VOICE_ID = "s0WKCJa7Iu1nqq9ODx2e"
api_key = "PASTE_YOUR_NEW_API_KEY_HERE"

client = ElevenLabs(api_key=api_key)

if "last_spoken" not in st.session_state:
    st.session_state.last_spoken = ""

favorites = [
    "Just a Sec",
    "I'll find out and let you know",
    "I love you",
    "Yep",
    "Nope",
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
        output_format="mp3_44100_128"
    )
    return b"".join(audio)

def speak_text(text):
    st.session_state.last_spoken = text
    audio_bytes = generate_audio_cached(text)
    st.audio(audio_bytes, format="audio/mp3")

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
        if st.button("Repeat Last Message", use_container_width=True):
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
        if st.button(phrase, use_container_width=True, key=f"cat_{phrase}"):
            speak_text(phrase)

st.markdown("---")

st.subheader("Type Message")
text_input = st.text_area("Type here:", height=150, key="text_input")

col_a, col_b = st.columns([3, 1])

with col_a:
    if st.button("Speak Typed Message", use_container_width=True):
        final_text = st.session_state.text_input.strip()
        if final_text:
            speak_text(final_text)
        else:
            st.warning("Please type a message first.")

with col_b:
    if st.button("Clear Text", use_container_width=True):
        st.session_state.text_input = ""
        st.rerun()