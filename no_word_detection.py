import streamlit as st
import speech_recognition as sr
import requests
import pickle
import json
import time

SYNONYMS_NEGATION = [
    # Formal Indonesian
    "tidak", "belum", "bukan", "tak", "ndak", "enggak", "nggak", "gak",

    # Formal English
    "no", "not", "never", "none", "unfinished", "incomplete", "uncompleted", "pending", "in progress",
    
    # Informal Indonesian
    "ga", "kaga", "blm", "tdk",

    # Indonesian phrases indicating something is not finished
    "masih", "proses", "revisi", "mengulang", "perlu diperbaiki", "belum siap", "belum final", "belum dikumpulkan",
    "masih berlangsung", "belum rampung", "belum dikerjakan", "masih revisi", "belum beres", "perlu revisi", "masih dikerjakan",
    "butuh waktu", "belum tuntas", "belum komplit", "sedang berjalan", "belum kelar",


    # Informal English
    "haven't", "hasn't", "didn't", "won't", "don't", "ain't", "still working", "still in progress", "not done",
    "not finished", "not yet", "almost done", "working on it", "not ready", "need more time", "not submitted",

    # Mixed phrases
    "belum selesai", "tidak selesai", "belum dikirim", "belum dikerjakan", "masih dikerjakan", "masih dalam proses",
    "still revising", "need revision", "waiting for review", "still editing", "still revising", "needs correction",
    "needs to be fixed", "needs improvement",

    # Additional expression words
    "kurang", "perbaikan", "butuh revisi", "belum submit", "masih belum", "tidak tuntas",
    "processing", "awaiting submission", "awaiting review"
]

# ====== OpenRouter API Configuration ======
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = "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"  # Replace with your API key

# ====== Load Naive Bayes Model ======
with open(r"ML/naive_bayes_no_word_detector.pkl", "rb") as f:
    model = pickle.load(f)

# ====== Functions ======

def recognize_speech():
    """Record speech and convert it to text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        with st.spinner("🎙️ Recording... Please speak.") :
            audio = recognizer.listen(source)
    try:
        text = recognizer.recognize_google(audio, language='en-US')
        return text
    except sr.UnknownValueError:
        st.error("❌ Sorry, the speech could not be recognized.")
        return None
    except sr.RequestError as e:
        st.error(f"❌ Error from Google Speech Recognition service: {e}")
        return None

def detect_negation_local(text, synonyms):
    """Detect negation using local word matching."""
    text = text.lower()
    return any(word in text for word in synonyms)

def detect_answer_classification_using_openrouter(text):
    """Detect classification using OpenRouter API."""
    headers = {
        'Authorization': f'Bearer {OPENROUTER_API_KEY}',
        'Content-Type': 'application/json',
    }

    prompt = f"""
Question: Are you done?

Your task is to classify the following answer as either 'done' or 'not done'.
If the answer indicates that the user is finished or agrees, classify it as 'done'.
If the answer indicates that the user is not done or still working on something, classify it as 'not done'.

User's answer: {text}

Provide output as either 'done' or 'not done' only. Do not give any explanation.
Make sure the answer is only 'done' or 'not done' without any additions or explanations.
    """.strip()

    data = {
        "model": "deepseek/deepseek-chat:free",
        "messages": [
            {"role": "system", "content": "Answer only with 'done' or 'not done'."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            response_data = response.json()
            classification = response_data['choices'][0]['message']['content'].strip().lower()
            if classification == "not done":
                return True
            elif classification == "done":
                return False
            else:
                return None
        else:
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

# ====== Streamlit App ======
st.title("🎙️ Detect 'Done' or 'Not Done' Answer from Voice")
st.write("Use your voice to detect whether you're done or not using three different methods.")

if st.button("🎤 Record and Detect"):
    # --- 1. Record voice and convert to text
    text_input = recognize_speech()

    if text_input:
        st.success(f"📝 Recognized Text: {text_input}")

        # --- 2. Detection with 3 methods

        # Local method
        start_time_local = time.time()
        local_result = detect_negation_local(text_input, SYNONYMS_NEGATION)
        end_time_local = time.time()

        # OpenRouter method
        start_time_openrouter = time.time()
        openrouter_result = detect_answer_classification_using_openrouter(text_input)
        end_time_openrouter = time.time()

        # Naive Bayes method
        start_time_nb = time.time()
        nb_result = model.predict([text_input])[0]
        end_time_nb = time.time()

        # Convert Naive Bayes result to True/False
        nb_result_boolean = True if nb_result == "belum" else False

        # --- 3. Display results
        st.subheader("🔍 Detection Results:")
        
        st.write(f"**Local Detection:** {local_result} (Duration: {end_time_local - start_time_local:.6f} seconds)")
        st.write(f"**OpenRouter Detection:** {openrouter_result} (Duration: {end_time_openrouter - start_time_openrouter:.6f} seconds)")
        st.write(f"**Naive Bayes Detection:** {nb_result_boolean} (Duration: {end_time_nb - start_time_nb:.6f} seconds)")
