import os
from analyzer import analyze_file

def test_analyze_sample_mp3():
    # サンプルファイルのパス
    sample_path = os.path.join(os.path.dirname(__file__), "../sample_data/sample_data1.mp3")
    sample_path = os.path.abspath(sample_path)

    # ファイルが存在することを確認
    assert os.path.exists(sample_path), "sample dataが見つかりません"

    # 解析処理の呼び出し
    result = analyze_file(sample_path)

    # BPM、Key、Camelotが返っているか簡易検証
    assert "bpm" in result and isinstance(result["bpm"], float)
    assert "key" in result and isinstance(result["key"], str)
    assert "camelot" in result and isinstance(result["camelot"], str)

    # 必要に応じて値範囲を追加チェック
    assert 30 <= result["bpm"] <= 300, f"BPM値が異常: {result['bpm']}"

    print("解析結果:", result)
