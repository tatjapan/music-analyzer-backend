from fastapi import APIRouter, UploadFile, File, HTTPException
import tempfile
import shutil
import os
from analyzer import analyze_file

router = APIRouter()

@router.post("/analyze")
async def analyze_audio(file: UploadFile = File(...)):
    print(f"[DEBUG] Received file content_type: {file.content_type}")
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")
    # if file.content_type not in ["audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp3"]:
    #     raise HTTPException(status_code=400, detail="Unsupported file type")

    tmp_path = None
    print(f"[DEBUG] Temporary file saved to: {tmp_path}")
    try:
        # 一時ファイルとして保存
        suffix = os.path.splitext(file.filename)[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
            print(f"[DEBUG] Temporary file saved to: {tmp_path}")

        # 解析ロジックへ一時ファイルパスを渡す
        result = analyze_file(tmp_path)
        print(f"[DEBUG] Temporary file saved to: {tmp_path}")

    except Exception as e:
        # エラー時は500を返す
        raise HTTPException(status_code=500, detail=f"解析中にエラーが発生しました: {str(e)}")
    finally:
        file.file.close()
        # 解析が終わったら必ず削除
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    return result
