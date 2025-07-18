import streamlit as st
import requests
import mimetypes
import tempfile
import os
import base64
from litellm import completion
from dotenv import load_dotenv

load_dotenv() 

# Set your API keys here
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LITELLM_MODEL = "gemini/gemini-2.0-flash-lite"



col1, col2, col3 = st.columns([6, 1, 2])

with col2:
    st.write("Powered by")
with col3:
    st.image("image.png", width=200)

 
st.title("Audio Translator & LLM Chatbot")

st.write("Upload an audio file or record audio. The app will transcribe and translate it, then send the result to an LLM for a response.")

# Audio input
uploaded_file = st.file_uploader("Upload an audio file", type=["wav", "mp3", "m4a", "ogg"])
mic_audio = st.audio_input("Or record audio using your mic")

audio_source = uploaded_file if uploaded_file is not None else mic_audio

def sarvam(file_path):
    # Call Sarvam API
    mime_type = mimetypes.guess_type(file_path)[0] or "audio/wav"
    st.write("Transcribing and translating audio...")
    with open(tmp_file_path, "rb") as f:
        response = requests.post(
            "https://api.sarvam.ai/speech-to-text-translate",
            headers={
                "api-subscription-key": SARVAM_API_KEY,
            },
            files={"file": (file_path, f, mime_type)}
        )
    os.remove(tmp_file_path)

    if response.status_code == 200:
        data = response.json()
        transcript = data.get("transcript", "")
        language_code = data.get("language_code","")
        print(response.json())
        print(language_code)
        st.success(f"Transcript: {transcript}")

        # Send transcript to LLM
        llm_response = completion(
                model=LITELLM_MODEL,
                messages=[
                    {"role": "system", "content": "Answer in plain text without any markdowns or emojis. Give response in under 2000 characters"},
                    {"role": "user", "content": transcript}]
            )
        llm_message = llm_response['choices'][0]['message']['content']
        st.info(f"LLM Response: {llm_message}")
        st.write("Translating LLM response to target language...")
        translation_payload = {
            "input": llm_message,
            "source_language_code": "auto",
            "target_language_code": language_code
        }
        translation_response = requests.post(
            "https://api.sarvam.ai/translate",
            headers={
                "api-subscription-key": SARVAM_API_KEY,
                "Content-Type": "application/json"
            },
            json=translation_payload
        )
        if translation_response.status_code == 200:
            translated_text = translation_response.json().get("translated_text", "")
            st.info(f"Translated Text: {translated_text}")

            # Send translated text to Sarvam TTS API
            st.write("Converting translated text to speech...")
            tts_payload = {
                "text": translated_text,
                "target_language_code": language_code
            }
            tts_response = requests.post(
                "https://api.sarvam.ai/text-to-speech",
                headers={
                    "api-subscription-key": SARVAM_API_KEY,
                    "Content-Type": "application/json"
                },
                json=tts_payload
            )
            if tts_response.status_code == 200:
                tts_data = tts_response.json()
                audios = tts_data.get("audios", [])
                if audios:
                    audio_data = audios[0]
                    if audio_data.startswith("http"):
                        st.audio(audio_data)
                    else:
                        audio_bytes = base64.b64decode(audio_data)
                        st.audio(audio_bytes, format="audio/wav")
                else:
                    st.warning("No audio returned from TTS API.")
            else:
                st.error(f"TTS API error: {tts_response.status_code} {tts_response.text}")
        else:
            st.error(f"Translation API error: {translation_response.status_code} {translation_response.text}")
    else:
        st.error(f"Sarvam API error: {response.status_code} {response.text}")


if audio_source is not None:
    # Save audio to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
        tmp_file.write(audio_source.read())
        tmp_file_path = tmp_file.name

    st.audio(tmp_file_path)
    sarvam(tmp_file_path)

elif uploaded_file is not None:
    # Save uploaded file to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_file_path = tmp_file.name

    st.audio(tmp_file_path)
    sarvam(tmp_file_path)

    
else:
    st.info("Please upload an audio file to begin.")
