# 🛠️ 音楽解析アプリ バックエンド基本設計書（FastAPI）

## 1. 概要

本システムは、ユーザーがアップロードした音楽ファイル（またはブラウザで録音した音楽）をもとに、楽曲のBPMとKey（およびCamelot表記）を解析し、JSONで返却するAPIバックエンドです。

---

## 2. 技術構成

| 項目 | 内容 |
|------|------|
| フレームワーク | FastAPI (Python 3.12) |
| デプロイ先 | AWS Lambda（Mangumを使用） |
| 一時ファイル処理 | Python `tempfile` モジュール |
| 音楽解析 | `librosa`, `ffmpeg-python`, `numpy` |
| ファイル保存（仮） | Amazon S3（署名付きURL経由でアップロード） |
| アクセス制限 | Redis（ElastiCache）または DynamoDB（TTL付） |
| API連携 | API Gateway 経由のHTTPアクセス |

---

## 3. API仕様

### 📥 `POST /analyze`

| 内容 | 値 |
|------|----|
| 概要 | 音楽ファイルを受け取り、BPMとKeyを解析 |
| メソッド | POST |
| リクエスト形式 | `multipart/form-data`（`file` フィールドに音楽ファイル） |
| レスポンス | JSON形式（解析結果） |
| ステータスコード | `200 OK`, `400 Bad Request`, `429 Too Many Requests` |

#### 📤 レスポンス例

```json
{
  "bpm": 123.45,
  "key": "D#",
  "camelot": "5A"
}
````

---

## 4. 音楽解析処理概要

1. 音楽ファイル（WAV/MP3）を一時ファイルとして保存
2. `ffmpeg` により WAV形式に変換（必要に応じて）
3. `librosa.load()` にて波形とサンプルレートを取得
4. `librosa.beat.beat_track()` によりBPM算出
5. `librosa.feature.chroma_stft()` → 平均ベクトルから最大成分のインデックス取得 → Key特定
6. KeyからCamelot表記へ変換（辞書変換方式）
7. JSONで返却し、音楽ファイルは削除

---

## 5. レート制限仕様（IP単位）

| 項目       | 内容                                |
| -------- | --------------------------------- |
| 制限単位     | クライアントIPアドレス                      |
| リセット周期   | UTC日単位（`%Y-%m-%d`）でキー管理           |
| 最大アクセス数  | 1日30回まで                           |
| 超過時レスポンス | `429 Too Many Requests` とエラーメッセージ |
| 実装候補     | Redis（高速アクセス）または DynamoDB（サーバーレス特化）  |

---

## 6. ディレクトリ構成（ローカル開発時）

```
backend/
├── main.py
├── analyzer.py
├── rate_limit.py
├── config.py               
├── requirements.txt
├── .env                    
├── s3_utils.py
├── routers/                
│   └── audio_router.py
├── utils/                  
│   └── camelot.py
├── tests/                  
│   └── test_analyzer.py
├── sample_data/            # .gitignore
│   └── test_audio.wav

```

---

## 7. デプロイ設定（Lambda）

### 7.1 Mangumラッパー追加

```python
# main.py
from mangum import Mangum
handler = Mangum(app)
```

### 7.2 Serverless Framework 設定例（仮）

```yaml
functions:
  app:
    handler: main.handler
    events:
      - http:
          path: /{proxy+}
          method: any
```

---

## 8. セキュリティ・制限事項

* アップロードファイルは30MBまでを許容
* 処理時間は20秒以内（ファイルサイズ・長さで制限）
* `/tmp`使用上限：Lambdaでは最大512MB
* クライアントは正しい `Content-Type` を送信すること（例：`audio/webm`）

---

## 9. 今後の拡張（仮）

* OpenAI APIを用いた「曲の雰囲気自動生成」
* DB保存型のユーザー履歴管理
* 一括音楽解析（CSV出力）
