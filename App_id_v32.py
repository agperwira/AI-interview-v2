import streamlit as st
import json
import requests
from gtts import gTTS
from io import BytesIO
import speech_recognition as sr
from fpdf import FPDF
import re
import os

# ----------------------
# Konfigurasi API LLM
API_KEY = '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'
API_URL = 'https://openrouter.ai/api/v1/chat/completions'
headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

# ----------------------
# Modul Eksternal: Speech to Text dan Text to Speech

def generate_tts(text: str, lang: str = 'id') -> BytesIO:
    tts = gTTS(text, lang=lang)
    buf = BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf

def recognize_speech(audio_file) -> str:
    recognizer = sr.Recognizer()
    try:
        audio_bytes = BytesIO(audio_file.read())
        audio_bytes.seek(0)
        if audio_bytes.getbuffer().nbytes == 0:
            return "[STT Error] File audio kosong atau belum tersedia"
        with sr.AudioFile(audio_bytes) as source:
            audio_data = recognizer.record(source)
            return recognizer.recognize_google(audio_data, language="id-ID")
    except Exception as e:
        return f"[STT Error] {e}"

def extract_json(text: str) -> dict:
    try:
        if "```json" in text:
            match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
            if match:
                text = match.group(1)
        text = text.strip()
        return json.loads(text)
    except Exception as e:
        raise ValueError(f"Error parsing JSON: {e}")

# ----------------------
# Fungsi PDF dari data

def create_pdf_from_json(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Gunakan font Unicode
    font_path = r"Avatar Chatbot\V3\fonts\DejaVuSans-Bold.ttf"  # Pastikan font ini ada
    pdf.add_font("DejaVu", "", font_path, uni=True)
    pdf.set_font("DejaVu", size=12)

    # Judul
    pdf.cell(0, 10, "Resume Wawancara Kandidat", ln=True, align='C')
    pdf.ln(10)

    # Profil Kandidat
    pdf.set_font("DejaVu",  size=12)
    pdf.cell(0, 10, "Profil Kandidat:", ln=True)
    pdf.set_font("DejaVu", size=12)
    pdf.cell(0, 10, f"- Nama: {data['candidate_name']}", ln=True)
    
    pdf.ln(5)
    
    # Jawaban Kandidat
    pdf.set_font("DejaVu",  size=12)
    pdf.cell(0, 10, "Jawaban Kandidat:", ln=True)
    pdf.set_font("DejaVu", size=12)
    for response in data['responses']:
        pdf.multi_cell(0, 10, f"Pertanyaan {response['question_number']}:\n{response['summary']}\n")
        if response['observed_traits']:
            pdf.cell(0, 10, f"Observed Traits: {', '.join(response['observed_traits'])}", ln=True)
        pdf.ln(2)

    # Analisis
    pdf.set_font("DejaVu",  size=12)
    pdf.cell(0, 10, "Analisis:", ln=True)
    pdf.set_font("DejaVu", size=12)
    
    if data['analysis']['key_strengths']:
        pdf.cell(0, 10, f"Key Strengths: {', '.join(data['analysis']['key_strengths'])}", ln=True)
    if data['analysis']['areas_for_improvement']:
        pdf.cell(0, 10, f"Areas for Improvement: {', '.join(data['analysis']['areas_for_improvement'])}", ln=True)
    if data['analysis']['inconsistencies']:
        pdf.cell(0, 10, f"Inconsistencies: {', '.join(data['analysis']['inconsistencies'])}", ln=True)
    
    pdf.ln(5)
    
    # Kesimpulan
    pdf.set_font("DejaVu",  size=12)
    pdf.cell(0, 10, "Kesimpulan:", ln=True)
    pdf.set_font("DejaVu", size=12)
    pdf.multi_cell(0, 10, data['conclusion'])

    # Kembalikan PDF dalam format byte untuk diunduh
    return pdf.output(dest='S').encode('utf-8')

# ----------------------
# Inisialisasi session state
def init_session():
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    if 'answers' not in st.session_state:
        st.session_state.answers = {}
    if 'profile' not in st.session_state:
        st.session_state.profile = {}
    if 'result_json' not in st.session_state:
        st.session_state.result_json = None

# ----------------------
# Formulir Data Pribadi

def personal_form():
    st.title("📄 Data Pribadi Kandidat")
    with st.form(key="form_data_pribadi"):
        nama = st.text_input("Nama Lengkap:")
        usia = st.text_input("Usia:")
        gender = st.radio("Jenis Kelamin:", ("Laki-laki", "Perempuan"))
        submit_profile = st.form_submit_button("▶️ Mulai Wawancara")

        if submit_profile and nama and usia and gender:
            st.session_state.profile = {'nama': nama, 'usia': usia, 'jenis_kelamin': gender}
            st.session_state.current_question = 1
            st.rerun()

# ----------------------
# Proses Wawancara

def interview_process(questions):
    idx = st.session_state.current_question - 1
    question = questions[idx]

    st.subheader(f"❓ Pertanyaan {idx+1}")
    # st.markdown(f"**{question}**")

    # Putar video jika tersedia
    video_path = os.path.join("videos", f"q{idx+1}.mp4")
    if os.path.exists(video_path):
        with open(video_path, 'rb') as f:
            st.video(f.read())

    buf = generate_tts(question)
    # st.audio(buf, format='audio/mp3') 

    if f"audio_count_{idx}" not in st.session_state:
        st.session_state[f"audio_count_{idx}"] = 0

    audio = st.audio_input("🎙️ Jawaban Suara", key=f"audio_{idx}")
    text_answer = ""

    if audio:
        st.session_state[f"audio_count_{idx}"] += 1
        result = recognize_speech(audio)
        text_answer = result
        if not result.startswith("[STT Error]"):
            st.success(f"Hasil STT: {text_answer}")
        else:
            st.warning(result)

    answer_input = st.text_area("📝 Jawaban Teks:", value=text_answer, key=f"text_{idx}")

    if st.button("➡️ Lanjut"):
        st.session_state.answers[question] = {
            "answer": answer_input or text_answer or "-",
            "audio_attempts": st.session_state.get(f"audio_count_{idx}", 0)
        }
        st.session_state.current_question += 1
        st.rerun()

# ----------------------
# Kirim ke LLM

def submit_to_llm(questions):
    st.success("✅ Semua pertanyaan selesai dijawab.")
    if st.button("📤 Kirim Jawaban ke LLM"):
        profil = st.session_state.profile
        jawaban = st.session_state.answers
        user_input = f"Nama: {profil['nama']}, Usia: {profil['usia']}, Gender: {profil['jenis_kelamin']}. Jawaban saya: " + \
                     " ".join([f"{i+1}. {q} - {a['answer']} (audio_attempts: {a['audio_attempts']})" for i, (q, a) in enumerate(jawaban.items())])

        data = {
            "model": "deepseek/deepseek-chat:free",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ]
        }

        res = requests.post(API_URL, headers=headers, json=data)
        if res.status_code == 200:
            try:
                content = res.json()['choices'][0]['message']['content']
                content = content.strip().split('```json')[-1].split('```')[0].strip() if '```json' in content else content.strip()
                # st.session_state.result_json = json.loads(content)
                parsed = extract_json(content)
                st.session_state.result_json = parsed
                st.success("✅ JSON berhasil di-parse")
                st.json(parsed)
            except Exception as e:
                st.error(f"❌ Gagal mem-parse JSON: {e}")
                st.code(content)
        else:
            st.error(f"Gagal dari API LLM: {res.status_code}")

# ----------------------
# Download JSON

def download_json_files():
    st.markdown("### 📥 Unduh Data Wawancara")
    
    # Download JSON files
    if st.session_state.profile:
        profile_json = json.dumps(st.session_state.profile, indent=2)
        st.download_button("⬇️ Unduh Profil Kandidat", profile_json, file_name="profile.json", mime="application/json")
    if st.session_state.answers:
        answers_json = json.dumps(st.session_state.answers, indent=2)
        st.download_button("⬇️ Unduh Jawaban Kandidat", answers_json, file_name="answers.json", mime="application/json")
    if st.session_state.result_json:
        result_json = json.dumps(st.session_state.result_json, indent=2)
        st.download_button("⬇️ Unduh Hasil Analisis LLM", result_json, file_name="llm_result.json", mime="application/json")

    # # Download PDF
    # if st.session_state.profile and st.session_state.answers and st.session_state.result_json:
    #     pdf_bytes = create_pdf_from_json({
    #         'candidate_name': st.session_state.profile['nama'],
    #         'responses': [{'question_number': i+1, 'summary': st.session_state.answers[q]['answer'], 'observed_traits': []} for i, q in enumerate(st.session_state.answers)],
    #         'analysis': {
    #             'key_strengths': [],
    #             'areas_for_improvement': ["Lack of detailed responses to interview questions."],
    #             'inconsistencies': ["Consistent absence of responses across all questions."]
    #         },
    #         'conclusion': "The candidate did not provide any responses to the interview questions."
    #     })
    #     st.download_button("📄 Unduh Semua dalam Format PDF", data=pdf_bytes, file_name="resume_wawancara.pdf", mime="application/pdf")

# ----------------------
# Reset Session

def reset_all():
    if st.button("🔁 Ulangi Proses"):
        for k in ['current_question', 'answers', 'profile', 'result_json']:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()

# ----------------------
# Constants
questions = [
    "Ceritakan saat Anda harus mengatakan tidak pada permintaan yang bertentangan dengan prioritas Anda dari seseorang yang dekat dengan anda. Bagaimana cara Anda menanganinya",
    "Ceritakan tentang sebuah proyek di mana Anda harus memilih antara deadline atau hasil ideal anda",
    "Bagaimana Anda tetap termotivasi ketika kontribusi Anda kurang mendapat perhatian atau apresiasi",
    "Ceritakan situasi di mana Anda harus memimpin atau mempengaruhi orang lain tanpa memiliki wewenang formal. Apa yang Anda lakukan",
    "Ceritakan pengalaman saat anda mengambil keputusan yang berisiko baik di dunia kerja maupun di kehidupan pribadi, bagaimana Anda menimbang untung-ruginya",
    "Bagaimana respon anda ketika anggota tim mengajukan ide yang cukup radikal namun bisa mempengaruhi proses kerja saat ini",
    "Ceritakan bagaimana anda mengembangkan strategi untuk proyek jangka panjang. Langkah-langkah apa yang anda prioritaskan terlebih dahulu",
    "Ceritakan saat anda harus beradaptasi pada sebuah lingkungan atau proses yang baru. Bagaimana anda menghadapinya",
    "Ceritakan saat anda mendapatkan kritik yang tidak terduga atau cukup keras? Bagaimana anda menggunakannya untuk berkembang atau mengubah cara kerja anda"
]

with open('system_prompt.txt', 'r') as f:
    SYSTEM_PROMPT = f.read()

# ----------------------
# Main Execution Flow
init_session()
if st.session_state.current_question == 0:
    personal_form()
elif 1 <= st.session_state.current_question <= len(questions):
    interview_process(questions)
elif st.session_state.current_question > len(questions):
    submit_to_llm(questions)
    download_json_files()

reset_all()