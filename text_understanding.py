import streamlit as st
from langdetect import detect
from googletrans import Translator
from gtts import gTTS
import pyttsx3
import tempfile
import os
import PyPDF2
import nltk_download
import re
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer
import nltk
from nltk import sent_tokenize, word_tokenize, pos_tag
import random

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

# --- SETUP ---
st.set_page_config(page_title="Smart Text App", layout="centered")
st.title("🌐 Advanced Smart Text Understanding App")

translator = Translator()

# --- Theme Switch ---
theme = st.sidebar.radio("Choose Theme", ["Light", "Dark"])
if theme == "Dark":
    st.markdown("""
        <style>
        body, .stApp { background-color: #1e1e1e; color: white; }
        </style>
    """, unsafe_allow_html=True)

# --- Language Options ---
language_map = {
    "English": "en",
    "Hindi": "hi",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Chinese": "zh-cn",
    "Japanese": "ja",
    "Russian": "ru",
    "Arabic": "ar",
    "Bengali": "bn",
    "Tamil": "ta",
    "Telugu": "te",
    "Kannada": "kn",
    "Malayalam": "ml"
}
selected_lang_name = st.selectbox("🌍 Output Language (Text & Voice)", list(language_map.keys()))
selected_lang_code = language_map[selected_lang_name]

# --- TTS Mode ---
tts_mode = st.radio("TTS Mode", ["Online (gTTS)", "Offline (pyttsx3 - English only)"])
voice_enabled = st.checkbox("Enable voice output")

# --- File Upload / Input Text ---
uploaded_file = st.file_uploader("📌 Upload PDF or .txt", type=["pdf", "txt"])
text_input = st.text_area("📄 Or paste your text here:", height=250)

# --- Utilities ---
def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    return "".join(page.extract_text() or "" for page in reader.pages)

def summarize_text(text, num_sentences=5):
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LexRankSummarizer()
    summary = summarizer(parser.document, num_sentences)
    return " ".join(str(sentence) for sentence in summary)

def find_answer(text, question):
    sentences = re.split(r'(?<=[.!?]) +', text)
    keywords = [w.lower() for w in question.split() if len(w) > 2]
    best = max(sentences, key=lambda s: sum(k in s.lower() for k in keywords), default="Sorry, I couldn't find an answer.")
    return best

def speak_text(text, lang):
    if tts_mode.startswith("Online"):
        tts = gTTS(text, lang=lang)
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(temp.name)
        return temp.name
    else:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
        engine.save_to_file(text, temp_path)
        engine.runAndWait()
        return temp_path

def generate_quiz_questions(text, num_questions=5):
    sentences = sent_tokenize(text)
    questions = []

    for sentence in sentences:
        words = word_tokenize(sentence)
        tagged = pos_tag(words)
        nouns = [word for word, tag in tagged if tag.startswith('NN') and len(word) > 3]

        if nouns:
            chosen_noun = random.choice(nouns)
            question = sentence.replace(chosen_noun, "")
            correct_answer = chosen_noun
            questions.append((question, correct_answer))

        if len(questions) >= num_questions:
            break

    return questions

# --- Load Text ---
main_text = ""
if uploaded_file:
    if uploaded_file.type == "application/pdf":
        main_text = extract_text_from_pdf(uploaded_file)
    elif uploaded_file.type == "text/plain":
        main_text = uploaded_file.read().decode("utf-8")
elif text_input:
    main_text = text_input

if main_text:
    st.subheader("📃 Loaded Text Preview")
    st.text(main_text[:800] + ("..." if len(main_text) > 800 else ""))

    question = st.text_input("❓ Ask a question from the text:")

    if st.button("Get Answer") and question:
        detected_lang = detect(main_text)
        main_text_en = translator.translate(main_text, dest="en").text if detected_lang != 'en' else main_text

        answer_en = find_answer(main_text_en, question)
        answer_translated = translator.translate(answer_en, dest=selected_lang_code).text if selected_lang_code != "en" else answer_en

        st.subheader("✅ Answer:")
        st.success(answer_translated)

        if voice_enabled:
            st.subheader("🔊 Listen to Answer")
            audio_file = speak_text(answer_translated, selected_lang_code)
            st.audio(audio_file)
            with open(audio_file, "rb") as af:
                st.download_button("📅 Download Answer Audio", af, file_name="answer.mp3")

        st.download_button("📄 Download Answer as Text", answer_translated, file_name="answer.txt")

    if st.button("Summarize Text"):
        detected_lang = detect(main_text)
        main_text_en = translator.translate(main_text, dest="en").text if detected_lang != 'en' else main_text
        summary_en = summarize_text(main_text_en)
        summary_translated = translator.translate(summary_en, dest=selected_lang_code).text if selected_lang_code != "en" else summary_en

        st.subheader("📝 Summary")
        st.info(summary_translated)

        if voice_enabled:
            st.subheader("🔊 Listen to Summary")
            audio_file = speak_text(summary_translated, selected_lang_code)
            st.audio(audio_file)
            with open(audio_file, "rb") as af:
                st.download_button("📅 Download Summary Audio", af, file_name="summary.mp3")

        st.download_button("📄 Download Summary as Text", summary_translated, file_name="summary.txt")

    if st.button("Generate Quiz Questions"):
        detected_lang = detect(main_text)
        main_text_en = translator.translate(main_text, dest="en").text if detected_lang != 'en' else main_text

        questions = generate_quiz_questions(main_text_en)
        st.subheader("🧠 Quiz Questions")

        for i, (q, ans) in enumerate(questions, 1):
            translated_q = translator.translate(q, dest=selected_lang_code).text if selected_lang_code != 'en' else q
            translated_ans = translator.translate(ans, dest=selected_lang_code).text if selected_lang_code != 'en' else ans

            st.markdown(f"*Q{i}:* {translated_q}")
            with st.expander("Show Answer"):
                st.write(f"✅ {translated_ans}")

            if voice_enabled:
                audio_file = speak_text(translated_q, selected_lang_code)
                st.audio(audio_file)

        st.download_button("📄 Download Quiz as Text", "\n\n".join([f"Q{i}: {q}\nA: {a}" for i, (q, a) in enumerate(questions, 1)]), file_name="quiz.txt")

else:
    st.info("Upload a file or paste some text to start.")