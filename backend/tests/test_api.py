import os
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_analyze_api():
    # サンプル音楽ファイルのバス
    sample_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../sample_data/sample_data1.mp3"))

    with open(sample_path, "rb") as f:
        # multipart/form-dataとしてファイルを送信
        files = {"file": ("sample_data1.mp3", f, "audio/mpeg")}
        response = client.post("/analyze", files=files)

    # ステータスコード確認
    assert response.status_code == 200

    data = response.json()
    # keyの存在チェックと型のチェック
    assert "bpm" in data and isinstance(data["bpm"], float)
    assert "key" in data and isinstance(data["key"], str)
    assert "camelot" in data and isinstance(data["camelot"], str)

    print("API解析結果:", data)