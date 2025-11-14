import os
import re
from difflib import SequenceMatcher
import streamlit as st
import pandas as pd

# ---------- Text Preprocessing ----------
def preprocess(text):
    text = text.lower()
    text = re.sub(r'\b(oblique|by|slash)\b', '/', text)  # treat words as slash
    text = re.sub(r'[.,()]+', '', text)  # remove punctuation
    text = re.sub(r'\s+', ' ', text).strip()  # clean spaces
    return text

# ---------- Highlight Differences ----------
def highlight_differences(orig_words, trans_words, threshold=0.8):
    highlighted_orig = []
    highlighted_trans = []

    matched_indices = set()

    for t_idx, t_word in enumerate(trans_words):
        best_score = 0
        best_o_idx = None
        for o_idx, o_word in enumerate(orig_words):
            score = SequenceMatcher(None, t_word, o_word).ratio()
            if score > best_score:
                best_score = score
                best_o_idx = o_idx
        if best_score >= threshold:
            highlighted_trans.append(f"<span style='color:green'>{t_word}</span>")
            highlighted_orig.append(f"<span style='color:green'>{orig_words[best_o_idx]}</span>")
            matched_indices.add(best_o_idx)
        else:
            highlighted_trans.append(f"<span style='color:red'>{t_word}</span>")
            if best_o_idx is not None:
                highlighted_orig.append(f"<span style='color:red'>{orig_words[best_o_idx]}</span>")
            else:
                highlighted_orig.append(f"<span style='color:red'>[missing]</span>")

    return " ".join(highlighted_orig), " ".join(highlighted_trans)

# ---------- Accuracy Calculation ----------
def word_match_accuracy(original, transcribed, threshold=0.8):
    orig_words = original.split()
    trans_words = transcribed.split()

    matches = 0
    for t_word in trans_words:
        best_score = max((SequenceMatcher(None, t_word, o_word).ratio() for o_word in orig_words), default=0)
        if best_score >= threshold:
            matches += 1

    if len(trans_words) == 0:
        return 0.0
    return (matches / len(trans_words)) * 100

# ---------- Streamlit UI ----------
st.set_page_config(layout="wide")
st.title("🎯 Whisper Accuracy Checker with Highlights")

original_folder = st.sidebar.text_input("📂 Original Folder Path", "original")
transcribed_folder = st.sidebar.text_input("📂 Transcribed Folder Path", "transcribed")
threshold = st.sidebar.slider("Match Threshold", 0.5, 1.0, 0.8, 0.05)

if st.sidebar.button("Scan Folders"):
    if not os.path.exists(original_folder) or not os.path.exists(transcribed_folder):
        st.error("One or both folders do not exist!")
    else:
        results = []
        file_details = {}

        for filename in sorted(os.listdir(original_folder), key=lambda x: int(x.split('.')[0])):
            if filename.endswith(".txt"):
                orig_path = os.path.join(original_folder, filename)
                trans_path = os.path.join(transcribed_folder, filename)

                if not os.path.exists(trans_path):
                    st.warning(f"⚠ Missing transcription for {filename}")
                    continue

                with open(orig_path, "r", encoding="utf-8") as f:
                    orig_text = f.read()
                with open(trans_path, "r", encoding="utf-8") as f:
                    trans_text = f.read()

                orig_prep = preprocess(orig_text)
                trans_prep = preprocess(trans_text)

                acc = round(word_match_accuracy(orig_prep, trans_prep, threshold), 2)
                results.append({"File": filename, "Accuracy (%)": acc})

                orig_words = orig_prep.split()
                trans_words = trans_prep.split()
                highlighted_orig, highlighted_trans = highlight_differences(orig_words, trans_words, threshold)

                file_details[filename] = {
                    "orig_raw": orig_text,
                    "trans_raw": trans_text,
                    "orig_high": highlighted_orig,
                    "trans_high": highlighted_trans
                }

        # ✅ Save results in session_state so they persist
        st.session_state["results"] = results
        st.session_state["file_details"] = file_details

# ---------- Always Display if Available ----------
if "results" in st.session_state and st.session_state["results"]:
    df = pd.DataFrame(st.session_state["results"])
    avg_acc = round(df["Accuracy (%)"].mean(), 2)
    st.subheader(f"📊 Accuracy Summary (Average = {avg_acc}%)")
    st.dataframe(df)

    selected_file = st.selectbox("📄 View File Details", df["File"].tolist())
    if selected_file:
        details = st.session_state["file_details"][selected_file]
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Original (Highlighted)**", unsafe_allow_html=True)
            st.markdown(f"<div style='background:#f0f0f0;padding:10px'>{details['orig_high']}</div>", unsafe_allow_html=True)
            with st.expander("📜 Original (Raw)"):
                st.text(details["orig_raw"])

        with col2:
            st.markdown("**Transcribed (Highlighted)**", unsafe_allow_html=True)
            st.markdown(f"<div style='background:#f0f0f0;padding:10px'>{details['trans_high']}</div>", unsafe_allow_html=True)
            with st.expander("📜 Transcribed (Raw)"):
                st.text(details["trans_raw"])
