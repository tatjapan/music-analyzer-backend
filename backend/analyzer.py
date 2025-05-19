import librosa
import numpy as np
import subprocess
import os

SHARP_TO_FLAT = {
    "C#": "Db", "D#": "Eb", "F#": "Gb", "G#": "Ab", "A#": "Bb"
}

# Major & minor両方のCamelot表記対応
KEY_TO_CAMELOT = {
    # Major
    "C": "8B",  "Db": "3B", "D": "10B", "Eb": "5B", "E": "12B",
    "F": "7B",  "Gb": "2B", "G": "9B",  "Ab": "4B", "A": "11B",
    "Bb": "6B", "B": "1B",
    # Minor
    "Am": "8A",  "Bbm": "3A", "Bm": "10A", "Cm": "5A", "C#m": "12A",
    "Dm": "7A",  "Ebm": "2A", "Em": "9A",  "Fm": "4A", "F#m": "11A",
    "Gm": "6A",  "G#m": "1A",
}

def sharp_to_flat(key: str) -> str:
    # C#, D# などシャープ表記ならフラットに変換
    return SHARP_TO_FLAT.get(key, key)

def convert_to_wav(src_path: str) -> str:
    if src_path.lower().endswith(".wav"):
        return src_path
    wav_path = src_path + ".wav"
    subprocess.run(
        ["ffmpeg", "-y", "-i", src_path, wav_path],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    return wav_path

def estimate_key(y, sr) -> str:
    # クロマベクトル最大値＋音階系列によるメジャー/マイナー推定（簡易版）
    # 精度向上には専用のキー推定ライブラリを利用

    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    chroma_avg = np.mean(chroma, axis=1)
    major_keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    minor_keys = ['Am', 'Bbm', 'Bm', 'Cm', 'C#m', 'Dm', 'Ebm', 'Em', 'Fm', 'F#m', 'Gm', 'G#m']

    # クロマベクトルの最大値でメジャー or マイナーどちらかの系列を採用（超簡易判定）
    key_idx = np.argmax(chroma_avg)
    # このサンプルでは常にメジャー判定
    key = major_keys[key_idx]

    # フラット表記化
    key = sharp_to_flat(key)

    # 本格的な判定にはml-key-finderやessentia、mirdata等の導入を検討
    return key

def analyze_file(filepath:str) -> dict:
    wav_path = convert_to_wav(filepath)
    y, sr = librosa.load(filepath, sr=None, mono=True)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    # tempoが配列の場合はfloat値として取り出す
    if isinstance(tempo, np.ndarray):
        tempo_value = float(tempo[0]) if len(tempo) > 0 else 0.0
    else:
        tempo_value = float(tempo)
    # TODO: マイナー判定実装是非検討
    key = estimate_key(y, sr)
    camelot = KEY_TO_CAMELOT.get(key, "")

    if wav_path != filepath and os.path.exists(wav_path):
        os.remove(wav_path)

    # BPMとKey, Camelotを返す
    return {
        "bpm": round(tempo_value, 2),
        "key": key,
        "camelot": camelot
    }

