from pydantic import BaseModel
from typing import List
from datetime import datetime

# このクラスをインスタンス化するのはask_llm_by_chunks.pyの中のみ
class QAItem(BaseModel):
    id: int  # 送信されたPDFごとに紐づけられるID・データベース管理用
    qa_id: int # 送信されたPDFの中で作成されたクイズの番号
    created_at: datetime # 作成時間
    question: str # 作成された問題文
    options: List[str] # 選択肢
    answer: str # 答え
    mode: str # クイズモード
    difficulty: str # 難易度 
    title: str # タイトル名