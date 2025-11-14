import whisper

model = whisper.load_model("large-v2")
result = model.transcribe(r"C:\Priyanka\judgement\Recording (6).m4a")
print("Transcription:\n", result["text"])
