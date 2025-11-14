import os
import re
from difflib import SequenceMatcher

def preprocess(text):
    text = text.lower()
    replacements = {
        r'\b(oblique|by|slash)\b': '/',
        r'\b(dash|minus)\b': '-',
        r'\b(point)\b': '.',
        r'\b(versus|against)\b': 'vs'
    }
    for pattern, repl in replacements.items():
        text = re.sub(pattern, repl, text)
    text = re.sub(r'\s*/\s*', '/', text)  # normalize slash
    text = re.sub(r'\s*-\s*', '-', text)  # normalize dash
    text = re.sub(r'[.,()]+', '', text)   # remove punctuation
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def word_match_accuracy(original, transcribed, threshold=0.8):
    orig_words = original.split()
    trans_words = transcribed.split()
    matches = 0
    mismatches = []
    for t_word in trans_words:
        best_score = max((SequenceMatcher(None, t_word, o_word).ratio() for o_word in orig_words), default=0)
        if best_score >= threshold:
            matches += 1
        else:
            mismatches.append(t_word)
    if len(trans_words) == 0:
        return 0.0, []
    return (matches / len(trans_words)) * 100, mismatches

# ----------- CONFIG ----------
original_file = r"C:\Priyanka\judgement\judgement2\originalss\parts\1.txt"
transcribed_file = r"C:\Priyanka\judgement\judgement2\transcription\1.txt"
threshold = 0.8
# -----------------------------

if not os.path.exists(original_file) or not os.path.exists(transcribed_file):
    print("❌ Original or transcribed file not found!")
else:
    with open(original_file, "r", encoding="utf-8") as f:
        orig_text = f.read()
    with open(transcribed_file, "r", encoding="utf-8") as f:
        trans_text = f.read()

    orig_prep = preprocess(orig_text)
    trans_prep = preprocess(trans_text)

    acc, mismatches = word_match_accuracy(orig_prep, trans_prep, threshold=threshold)
    acc = round(acc, 2)

    print(f"✅ Accuracy: {acc}%")
    print(f"🔍 Mismatches sample: {mismatches[:10]}")
