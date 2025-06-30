from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from mangum import Mangum  # ← Lambda用追加
import mimetypes
import re

from src.ask_llm_by_chunks import ask_llm_by_chunks
from src.SourceData import SourceData
from routers import qa_item, qa_info, qa_result, qa_all
from src.db_save import db_save_to_QAinfo, db_save_to_QAitem

import boto3
from uuid import uuid4

app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}



# @app.post("/upload_pdf/")
# async def upload_pdf(    
#     file: UploadFile = File(...),
#     questionCount: int = Form(...),
#     mode: str = Form(...),
#     difficulty: str = Form(...)
# ):
#     contents = file.file.read()  # ← await しない。直接読み込み
#     # contents = await file.read()
#     filename = file.filename

#     # PDFとTXTで処理を分ける
#     _, ext = os.path.splitext(filename)
#     ext = ext.lower()
#     if ext == ".pdf":
#         s_data = SourceData(contents, questionCount, mode, difficulty, filename)
#         texts = s_data.pdf2text()
#     elif ext == ".txt":
#         # TXTファイルの処理
#         texts = contents.decode("utf-8")  # bytes → str
#         s_data = SourceData(contents, questionCount, mode, difficulty, filename)
#         s_data.texts = texts
#     else:
#         raise HTTPException(status_code=400, detail="対応していないファイル形式です")
    
#     print("=== 生テキスト ===")
#     print(texts)

#     chunk_text = s_data.text2chunk()
#     result_question = ask_llm_by_chunks(s_data)

#     print("=== チャンクテキスト ===")
#     print(chunk_text)

#     id = db_save_to_QAinfo(s_data)
#     id = db_save_to_QAitem(id, result_question)

#     return {"id": id}


# S3クライアントの初期化（バケット名は必要に応じて）
s3_client = boto3.client('s3')
S3_BUCKET_NAME = "qaservice-upload-bucket"
from routers.qa_result import normalize

@app.get("/generate_presigned_url")
def get_presigned_url(
    filename: str = Query(...),
    questioncount: str = Query(...),
    mode: str = Query(...),
    difficulty: str = Query(...)
):
    # 拡張子からContent-Typeを推定（例: .pdf → application/pdf）
    content_type, _ = mimetypes.guess_type(filename)
    if content_type is None:
        content_type = "application/octet-stream"  # fallback

    filename = re.sub(r"\s+", "_", filename.strip())  # 前後の空白除去 + 中の空白をアンダースコアに

    key = f"uploads/{filename}"
    print("=== コンテンツタイプ確認 ===")
    print(f"コンテンツタイプ: {content_type}")
    print(f"キー: {key}")
    print(f"コンテンツタイプ: {questioncount}")
    print(f"キー: {mode}")
    print(f"コンテンツタイプ: {difficulty}")
    uuid = str(uuid4())

    try:
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod='put_object',
            Params={
                'Bucket': S3_BUCKET_NAME,
                'Key': key,
                'ContentType': content_type,
                'Metadata': {
                    'questioncount': questioncount,
                    'mode': mode,
                    'difficulty': difficulty,
                    'uuid': uuid
                }
            },
            ExpiresIn=3600
        )

        return JSONResponse(content={"url": presigned_url, "key": key, "uuid": uuid})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/analyze_pdf_from_s3/")
async def analyze_pdf_from_s3(
    s3_key: str = Form(...),
    questionCount: str = Form(...),
    mode: str = Form(...),
    difficulty: str = Form(...)
):
    try:
        questionCount = int(questionCount)
        # === S3からファイルをダウンロード ===
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
        contents = response["Body"].read()
        filename = os.path.basename(s3_key)
        print(f"取得成功: {filename}（{len(contents)}バイト）")

    except Exception as e:
        print("❌ S3からの取得失敗")
        print(f"エラー内容: {str(e)}")
        raise HTTPException(status_code=500, detail=f"S3からの取得に失敗しました: {str(e)}")

    # === PDF or TXT処理 ===
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    if ext == ".pdf":
        s_data = SourceData(contents, questionCount, mode, difficulty, filename)
        texts = s_data.pdf2text()
    elif ext == ".txt":
        texts = contents.decode("utf-8")
        s_data = SourceData(contents, questionCount, mode, difficulty, filename)
        s_data.texts = texts
    else:
        raise HTTPException(status_code=400, detail="対応していないファイル形式です")

    chunk_text = s_data.text2chunk()
    result_question = ask_llm_by_chunks(s_data)

    id = db_save_to_QAinfo(s_data)
    id = db_save_to_QAitem(id, result_question)

    return {"id": id}


# データベース用
app.include_router(qa_item.router)
app.include_router(qa_info.router)
app.include_router(qa_result.router)
app.include_router(qa_all.router)

# Lambda 対応ハンドラ（必須！）
lambda_handler = Mangum(app)





