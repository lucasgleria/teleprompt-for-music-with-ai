import torch
import torchaudio
from pydub import AudioSegment, silence
import whisper
from thefuzz import fuzz
import tempfile
import os

def separate_vocals(audio_path):
    """
    Separates the vocals from an audio file using the Demucs model.
    Saves the output to a temporary file.
    """
    model = torchaudio.pipelines.HDEMUCS_HIGH_MUSDB.get_model()
    model.eval()

    waveform, sample_rate = torchaudio.load(audio_path)
    waveform = waveform.unsqueeze(0)
    sources = model(waveform)[0]
    vocals = sources[-1]

    fd, output_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    torchaudio.save(output_path, vocals, sample_rate)
    return output_path

def remove_silence(audio_path):
    """
    Removes silent segments from an audio file.
    Saves the output to a temporary file.
    """
    sound = AudioSegment.from_wav(audio_path)
    non_silent_chunks = silence.detect_nonsilent(
        sound, min_silence_len=1000, silence_thresh=-40
    )

    combined_audio = AudioSegment.empty()
    for start, end in non_silent_chunks:
        combined_audio += sound[start:end]

    fd, output_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    combined_audio.export(output_path, format="wav")
    return output_path

def transcribe_audio(audio_path):
    """
    Transcribes an audio file using Whisper.
    """
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, word_timestamps=True)
    return result

def align_lyrics(transcription, lyrics_path):
    """
    Aligns the transcribed text with the actual lyrics at the word level.
    """
    with open(lyrics_path, "r", encoding="utf-8") as f:
        lyrics = f.read()

    lyric_words = lyrics.split()
    aligned_lyrics = []

    transcribed_words = []
    for segment in transcription["segments"]:
        if "words" in segment:
            transcribed_words.extend(segment['words'])

    if not transcribed_words:
        return []

    for i, lyric_word in enumerate(lyric_words):
        best_match_info = None
        best_ratio = 0

        start_search = max(0, i - 15)
        end_search = min(len(transcribed_words), i + 15)

        for j in range(start_search, end_search):
            transcribed_word_info = transcribed_words[j]
            transcribed_word = transcribed_word_info["word"]

            ratio = fuzz.ratio(lyric_word.lower(), transcribed_word.lower().strip(".,!?"))

            if ratio > best_ratio:
                best_ratio = ratio
                best_match_info = transcribed_word_info

        if best_match_info and best_ratio > 70:
            aligned_lyrics.append({
                "start": best_match_info["start"],
                "end": best_match_info["end"],
                "text": lyric_word,
                "original_index": i
            })

    return aligned_lyrics
