import os
import re
from difflib import SequenceMatcher
from typing import List, Tuple

import pandas as pd
import streamlit as st

# -------------------- Text Processing -------------------- #
DEFAULT_REPLACEMENTS = {
    r"\b(oblique|by|slash)\b": "/",
    r"\b(dash|minus)\b": "-",
    r"\b(point)\b": ".",
    r"\b(versus|against)\b": "vs",
}

EXTRA_REPLACEMENTS = {
    # common Indian legal narration variants
    r"\bsection\b": "s",
    r"\bsub\s*section\b": "subsection",
    r"\barticle\b": "art",
}


def preprocess(text: str, use_extra: bool = False) -> str:
    text = text.lower()
    replacements = DEFAULT_REPLACEMENTS.copy()
    if use_extra:
        replacements.update(EXTRA_REPLACEMENTS)
    for pattern, repl in replacements.items():
        text = re.sub(pattern, repl, text)
    # normalize separators and spacing
    text = re.sub(r"\s*/\s*", "/", text)
    text = re.sub(r"\s*-\s*", "-", text)
    text = re.sub(r"[.,()]+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# -------------------- Matching & Highlighting -------------------- #

def best_similarity(word: str, candidates: List[str]) -> float:
    # quick exact check first
    if word in candidates_set_cache.get(id(candidates), set()):
        return 1.0
    # fallback to fuzzy
    return max((SequenceMatcher(None, word, ow).ratio() for ow in candidates), default=0.0)


def word_match_accuracy(original: str, transcribed: str, threshold: float = 0.8) -> Tuple[float, List[str]]:
    orig_words = original.split()
    trans_words = transcribed.split()

    # cache set for exact lookup speed
    candidates_set_cache[id(orig_words)] = set(orig_words)

    matches = 0
    mismatches: List[str] = []
    for t in trans_words:
        score = best_similarity(t, orig_words)
        if score >= threshold:
            matches += 1
        else:
            mismatches.append(t)
    acc = (matches / len(trans_words) * 100.0) if trans_words else 0.0
    return acc, mismatches


def highlight_transcribed(transcribed: str, original: str, threshold: float = 0.8) -> str:
    """Return HTML for transcribed text with mismatches highlighted."""
    orig_words = original.split()
    candidates_set_cache[id(orig_words)] = set(orig_words)

    parts = []
    for t in transcribed.split():
        score = best_similarity(t, orig_words)
        if score >= threshold:
            parts.append(f"<span>{t}</span>")
        else:
            parts.append(
                f"<span style='background-color:#ffd6d6;color:#b00000;"
                f"border-radius:4px;padding:1px 3px'>{t}</span>"
            )
    html = " ".join(parts)
    return f"<div style='white-space:pre-wrap; line-height:1.6'>{html}</div>"


# global tiny cache used inside helper functions
candidates_set_cache = {}

# -------------------- UI -------------------- #
st.set_page_config(page_title="Whisper Accuracy Checker", layout="wide")
st.title("🎧 Whisper Accuracy Checker — Folder Compare + Highlights")

with st.sidebar:
    st.header("⚙️ Settings")
    original_folder = st.text_input("Original folder path", value="original")
    transcribed_folder = st.text_input("Transcribed folder path", value="transcribed")
    threshold = st.slider("Fuzzy match threshold", 0.50, 0.99, 0.80, 0.01,
                          help="Higher = stricter match. 0.8 is a good default.")
    use_extra = st.checkbox("Extra legal-normalization (section→s, article→art, etc.)", value=False)
    run_btn = st.button("Scan Folders")

# -------------------- Run on Button -------------------- #
if run_btn:
    if not os.path.isdir(original_folder):
        st.error(f"Original folder not found: {original_folder}")
        st.stop()
    if not os.path.isdir(transcribed_folder):
        st.error(f"Transcribed folder not found: {transcribed_folder}")
        st.stop()

    orig_files = sorted([f for f in os.listdir(original_folder) if f.lower().endswith(".txt")])
    rows = []
    per_file_data = {}

    for fname in orig_files:
        o_path = os.path.join(original_folder, fname)
        t_path = os.path.join(transcribed_folder, fname)

        status = "OK"
        if not os.path.exists(t_path):
            status = "MISSING TRANSCRIPTION"
            with open(o_path, "r", encoding="utf-8") as f:
                o_raw = f.read()
            o_prep = preprocess(o_raw, use_extra)
            acc = 0.0
            rows.append({"file": fname, "status": status, "accuracy_%": acc})
            per_file_data[fname] = {
                "original_raw": o_raw,
                "trans_raw": "",
                "original_prep": o_prep,
                "trans_prep": "",
                "accuracy": acc,
                "highlight_html": "",
            }
            continue

        with open(o_path, "r", encoding="utf-8") as f:
            o_raw = f.read()
        with open(t_path, "r", encoding="utf-8") as f:
            t_raw = f.read()

        o_prep = preprocess(o_raw, use_extra)
        t_prep = preprocess(t_raw, use_extra)
        acc, _ = word_match_accuracy(o_prep, t_prep, threshold)
        highlight_html = highlight_transcribed(t_prep, o_prep, threshold)

        rows.append({"file": fname, "status": status, "accuracy_%": round(acc, 2)})
        per_file_data[fname] = {
            "original_raw": o_raw,
            "trans_raw": t_raw,
            "original_prep": o_prep,
            "trans_prep": t_prep,
            "accuracy": acc,
            "highlight_html": highlight_html,
        }

    # ✅ Save in session_state for persistence
    st.session_state["df"] = pd.DataFrame(rows)
    st.session_state["per_file_data"] = per_file_data

# -------------------- Always Display if Data Available -------------------- #
if "df" in st.session_state and not st.session_state["df"].empty:
    df = st.session_state["df"]
    per_file_data = st.session_state["per_file_data"]

    # Summary
    st.subheader("📊 Summary")
    avg = df.loc[df["status"] == "OK", "accuracy_%"].mean() if "accuracy_%" in df else float('nan')
    st.metric("Average Accuracy (OK files)", f"{(avg if pd.notna(avg) else 0):.2f}%")
    st.dataframe(df, use_container_width=True)

    # CSV download
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV", data=csv, file_name="whisper_accuracy.csv", mime="text/csv")

    # Detailed viewer
    st.subheader("🔎 Detailed Viewer")
    selected = st.selectbox("Select a file", options=df["file"].tolist())
    data = per_file_data[selected]

    col1, col2 = st.columns(2)
    with col1:
        st.caption("Original (preprocessed)")
        st.text_area("", value=data["original_prep"], height=300)
        with st.expander("Show original raw text"):
            st.text_area("", value=data["original_raw"], height=250)
    with col2:
        st.caption(f"Transcribed (highlighted) — Accuracy: {data['accuracy']:.2f}%")
        st.markdown(data["highlight_html"], unsafe_allow_html=True)
        with st.expander("Show transcribed raw text"):
            st.text_area("", value=data["trans_raw"], height=250)
else:
    st.info("👉 Click 'Scan Folders' to load data.")
