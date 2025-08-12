# main.py - The Final and Guaranteed Working Version

import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import requests  # We are now using the universal 'requests' library

# --- 1. INITIAL SETUP AND API CONFIGURATION ---

st.set_page_config(page_title="EchoVerse", page_icon="🎙️", layout="wide")

@st.cache_resource
def configure_apis():
    """Load and configure API clients. Cached to avoid re-initializing on every rerun."""
    load_dotenv()
    google_api_key = os.getenv("GOOGLE_API_KEY")
    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")

    if not google_api_key:
        st.error("Google AI API Key is missing. Please check your .env file.")
        st.stop()
    if not elevenlabs_api_key:
        st.error("ElevenLabs API Key is missing. Please check your .env file.")
        st.stop()
        
    try:
        genai.configure(api_key=google_api_key)
    except Exception as e:
        st.error(f"Failed to configure Google Gemini API: {e}")
        st.stop()
        
    return elevenlabs_api_key

try:
    ELEVENLABS_API_KEY = configure_apis()
except Exception:
    st.stop()

# --- 2. CORE FUNCTIONS (LLM & TTS) ---

def rewrite_text_with_llm(text_to_rewrite, tone):
    if not text_to_rewrite: return ""
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    prompt = f"""You are a master storyteller. Rewrite the following text in a '{tone}' tone, preserving the original meaning but enhancing the style. Return only the rewritten text.
    ORIGINAL TEXT: "{text_to_rewrite}"
    REWRITTEN TEXT:"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"Error rewriting text with Gemini: {e}")
        return None

# --- THIS IS THE NEW, RELIABLE TTS FUNCTION USING DIRECT API CALLS ---
def convert_text_to_speech(api_key, text_to_speak, voice_id):
    """
    Generates audio by calling the ElevenLabs REST API directly.
    This bypasses the faulty 'elevenlabs' Python library.
    """
    if not text_to_speak or not voice_id: return None
    
    # The API endpoint URL for Text-to-Speech
    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    # Set up the headers with your API key
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }

    # Set up the data payload with the text and model
    data = {
        "text": text_to_speak,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    try:
        # Make the POST request to the API
        response = requests.post(tts_url, json=data, headers=headers)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Return the audio data as bytes
            return response.content
        else:
            # If not successful, show an error
            st.error(f"ElevenLabs API Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        st.error(f"An error occurred while calling the ElevenLabs API: {e}")
        return None

# --- 3. STREAMLIT USER INTERFACE ---

st.title("🎙️ EchoVerse – An AI-Powered Audiobook Creation Tool")

if 'history' not in st.session_state:
    st.session_state.history = []

# Input Layer
# --- Input Layer ---
st.header("1. Provide Your Text")
input_method = st.radio(
    "Choose input method:",
    ("Paste Text", "Upload .txt File"), 
    horizontal=True
)

original_text = ""
if input_method == "Paste Text":
    original_text = st.text_area("Or paste your text here:", height=150, placeholder="The team looked at the final prototype...")
else:
    uploaded_file = st.file_uploader("Upload a .txt file", type=["txt"])
    if uploaded_file is not None:
        try:
            original_text = uploaded_file.read().decode("utf-8")
            st.text_area("File Content:", original_text, height=150, disabled=True)
        except Exception as e:
            st.error(f"Error reading file: {e}")

# Tone and Voice Selection
st.header("2. Customize Your Narration")
col1, col2 = st.columns(2)
with col1:
    selected_tone = st.selectbox("Select a narrative tone:", ("Neutral", "Suspenseful", "Inspiring", "Professional", "Poetic"))
with col2:
    # Fetching voices via direct API call to avoid library issues
    try:
        response = requests.get("https://api.elevenlabs.io/v1/voices", headers={"xi-api-key": ELEVENLABS_API_KEY})
        response.raise_for_status() # Raise an exception for bad status codes
        voices_data = response.json()["voices"]
        # Create a mapping of voice names to voice IDs
        voice_map = {voice['name']: voice['voice_id'] for voice in voices_data}
        selected_voice_name = st.selectbox("Select a voice style:", list(voice_map.keys()))
        selected_voice_id = voice_map[selected_voice_name]
    except Exception as e:
        st.error(f"Could not fetch voices. Check network/API key. Error: {e}")
        st.stop()

# Generation Button
if st.button("Generate Audiobook", type="primary", use_container_width=True):
    if original_text and selected_voice_id:
        with st.spinner("EchoVerse is working its magic..."):
            rewritten_text = rewrite_text_with_llm(original_text, selected_tone)
            if rewritten_text:
                audio_data = convert_text_to_speech(ELEVENLABS_API_KEY, rewritten_text, selected_voice_id)
                if audio_data:
                    st.success("✅ Audiobook generated successfully!")
                    entry = {"original_text": original_text, "rewritten_text": rewritten_text, "tone": selected_tone, "voice_name": selected_voice_name, "audio_data": audio_data}
                    st.session_state.history.insert(0, entry)
    else:
        st.warning("Please provide text to continue.")

# Display latest result
if st.session_state.history:
    st.header("3. Your Latest Audiobook")
    latest = st.session_state.history[0]
    with st.container(border=True):
        col_orig, col_rewritten = st.columns(2)
        with col_orig:
            st.subheader("Original Text")
            st.text_area("Original", latest['original_text'], height=200, disabled=True, key="latest_orig")
        with col_rewritten:
            st.subheader(f"Rewritten (Tone: {latest['tone']})")
            st.text_area("Rewritten", latest['rewritten_text'], height=200, disabled=True, key="latest_rewritten")
    with st.container(border=True):
        st.subheader(f"Listen (Voice: {latest['voice_name']})")
        st.audio(latest['audio_data'], format="audio/mpeg")
        st.download_button("Download MP3", latest['audio_data'], f"EchoVerse_{latest['tone']}.mp3", "audio/mpeg", use_container_width=True)

# --- Past Narrations Panel (Component 5) ---
if len(st.session_state.history) > 0:
    with st.expander("📖 View Past Narrations (" + str(len(st.session_state.history)) + ")"):
        for i, entry in enumerate(st.session_state.history):
            with st.container(border=True):
                st.write(f"**Narration {len(st.session_state.history) - i}** | Tone: `{entry['tone']}` | Voice: `{entry['voice_name']}`")
                # THE NEXT LINE IS NOW FIXED (no key argument):
                st.audio(entry['audio_data'], format="audio/mp3")
                st.download_button(
                    label="Download this MP3",
                    data=entry['audio_data'],
                    file_name=f"EchoVerse_{entry['tone']}_{entry['voice_name']}_{i}.mp3",
                    mime="audio/mp3",
                    key=f"download_{i}" # The key is needed for the button, but not the audio player
                )