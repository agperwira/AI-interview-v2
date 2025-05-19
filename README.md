# 🤖 AI Interview Assistant with Streamlit

This project is a **Streamlit-based AI Interview Assistant** designed to conduct interviews, transcribe speech, analyze responses using a Large Language Model (LLM), and export structured results.

---

## 🚀 Features

- 📋 Candidate personal information form
- 🎤 Audio-based answers using microphone input
- 🔊 Text-to-Speech (TTS) for questions
- 🎥 Optional interview videos for each question
- 🧠 Response analysis using OpenRouter LLM API
- 📁 Downloadable results in JSON format

---

## 📁 Project Structure

/n├── app.py # Main Streamlit app
/n├── system_prompt.txt # LLM system prompt instructions
/n├── requirements.txt # Python dependencies
/n├── videos/ # q1.mp4, q2.mp4, etc.

## Create Virtual Environment and Install Dependencies

```python3 -m venv venv```
```source venv/bin/activate```

##📦 Dependencies

The following libraries are required and already listed in requirements.txt:
```pip install -r requirements.txt```

##▶️ Run the App

After setting up the environment and secrets, launch the app:
```streamlit run app.py```

##👨‍💻 Author

Made with ❤️ by Aga
