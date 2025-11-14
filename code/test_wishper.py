import whisper
import os
import re

# Load model once
model = whisper.load_model("large-v2")

folder_path = "C:\Priyanka\judgement\judgement1\audio"  

def extract_number(filename):
    match = re.search(r'\((\d+ )\)', filename)
    return int(match.group(1)) if match else 99999  

# Get audio files sorted numerically by number in parentheses
audio_files = sorted(
    [f for f in os.listdir(folder_path) if f.lower().endswith((".mp3", ".wav", ".m4a"))],
    key=extract_number
)

for filename in audio_files:
    file_path = os.path.join(folder_path, filename)
    print(f"🔊 Processing: {filename}")
    
    try:
        result = model.transcribe(file_path)
        transcript = result['text'].strip()
        print(f"📝 Transcription for {filename}:\n{transcript}\n")

        # Save transcript to txt file with same base name
        base_name = os.path.splitext(filename)[0]
        with open(os.path.join(folder_path, base_name + ".txt"), "w", encoding="utf-8") as f:
            f.write(transcript)

    except Exception as e:
        print(f"❌ Error processing {filename}: {e}")
