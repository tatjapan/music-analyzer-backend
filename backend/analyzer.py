import librosa
import numpy as np
import subprocess
import os
from collections import Counter

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
    # クロマベクトル最大値＋音階系列によるメジャー/マイナー推定

    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    chroma_avg = np.mean(chroma, axis=1)

    major_keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    minor_keys = ['Am', 'Bbm', 'Bm', 'Cm', 'C#m', 'Dm', 'Ebm', 'Em', 'Fm', 'F#m', 'Gm', 'G#m']

    # 例えばメジャーコードテンプレート（I, III, V強調: C, E, G → index 0, 4, 7）
    major_template = np.array([1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0])
    minor_template = np.array([1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0])  # C, D#, G

    # テンプレート生成（ローリング）: C→B, Am→G#m まで
    major_similarities = []
    minor_similarities = []

    # メジャーキーとマイナーキー比較
    for i in range(12):
        rolled_major = np.roll(major_template, i)
        rolled_minor = np.roll(minor_template, i)
        major_similarities.append(np.dot(chroma_avg, rolled_major))
        minor_similarities.append(np.dot(chroma_avg, rolled_minor))

    # 最高スコアを取ったキーが推定値
    max_major_idx = int(np.argmax(major_similarities))
    max_minor_idx = int(np.argmax(minor_similarities))

    # majorとminorどちらのスコアが高いか比べて採用値判定
    if major_similarities[max_major_idx] >= minor_similarities[max_minor_idx]:
        key = major_keys[max_major_idx]
    else:
        key = minor_keys[max_minor_idx]

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

    # ここから支配的Keyを推定するコード
    window_size_sec = 3 # ウィンドウ長（秒）
    hop_sec = 1          # スライド間隔（秒）
    duration = librosa.get_duration(y=y, sr=sr)
    key_results = []
    for start in np.arange(0, duration-window_size_sec, hop_sec):
        y_window = y[int(start*sr):int((start+window_size_sec)*sr)]
        if len(y_window) < int(0.5*sr): #0.5秒未満は無視
            continue
        key = estimate_key(y_window, sr)
        key_results.append(key)
    if key_results:
        key = Counter(key_results).most_common(1)[0][0]
    else:
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

