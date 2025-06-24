from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware

from src.ask_llm_by_chunks import ask_llm_by_chunks
from src.SourceData import SourceData

app = FastAPI()

# ここにCORS設定を追加
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # ReactアプリのURL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/upload_pdf/")
async def upload_pdf(    
    file: UploadFile = File(...),
    questionCount: int = Form(...),
    mode: str = Form(...),
    difficulty: str = Form(...)
):
    contents = await file.read()
    filename = file.filename
    s_data = SourceData(contents, questionCount, mode, difficulty, filename)
    texts = s_data.pdf2text()
    chunk_text = s_data.text2chunk()
    result_question = ask_llm_by_chunks(s_data)

    # デバック用
    with open("extracted_text.txt", "w", encoding="utf-8") as f:
        f.write(texts)

    return result_question