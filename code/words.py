import os
import re
from difflib import SequenceMatcher
from collections import defaultdict

def preprocess(text):
    text = text.lower()
    text = re.sub(r'\b(oblique|by|slash)\b', '/', text)  # treat as slash
    text = re.sub(r'[.,()]+', '', text)  # remove punctuation
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def analyze_file(orig_text, trans_text, threshold=0.8):
    orig_words = preprocess(orig_text).split()
    trans_words = preprocess(trans_text).split()

    total_words = len(trans_words)
    errors = []
    matches = 0

    for t_word in trans_words:
        best_score = 0
        best_o_word = None
        for o_word in orig_words:
            score = SequenceMatcher(None, t_word, o_word).ratio()
            if score > best_score:
                best_score = score
                best_o_word = o_word
        if best_score >= threshold:
            matches += 1
        else:
            errors.append((t_word, best_o_word if best_o_word else ""))

    error_count = total_words - matches

    # Count all errors (wrong_word → right_word)
    error_stats = defaultdict(int)
    for wrong, right in errors:
        error_stats[(wrong, right)] += 1

    return total_words, error_count, error_stats

# ----------------- MAIN -----------------
original_folder = r"C:\Priyanka\judgement\retransrcribe\krati\j2\o"
transcribed_folder = r"C:\Priyanka\judgement\retransrcribe\krati\j2\t"

for filename in sorted(os.listdir(original_folder), key=lambda x: int(x.split('.')[0])):
    if filename.endswith(".txt"):
        orig_path = os.path.join(original_folder, filename)
        trans_path = os.path.join(transcribed_folder, filename)

        if not os.path.exists(trans_path):
            print(f"⚠ Missing transcription for {filename}")
            continue

        with open(orig_path, "r", encoding="utf-8") as f:
            orig_text = f.read()
        with open(trans_path, "r", encoding="utf-8") as f:
            trans_text = f.read()

        total, errors, error_stats = analyze_file(orig_text, trans_text)

        print(f"\n📄 File: {filename}")
        print(f"   Total Words: {total}")
        print(f"   Errors: {errors}")
        if error_stats:
            print("   🔁 Errors Detail:")
            for (wrong, right), count in sorted(error_stats.items(), key=lambda x: -x[1]):
                if right:
                    print(f"      {wrong} → instead of {right} → {count} time(s)")
                else:
                    print(f"      {wrong} → no match → {count} time(s)")
        else:
            print("   ✅ No errors found")
