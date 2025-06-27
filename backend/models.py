from pydantic import BaseModel, Field
from typing import List, Union, Optional

class QAItemModel(BaseModel):
    id: str
    qa_id: int
    question: str
    options: List[str]
    answer: str

class QAItemUpdateModel(BaseModel):
    qa_id: int
    question: Optional[str] = None
    options: Optional[List[str]] = None
    answer: Optional[str] = None
    satisfaction: Optional[int] = None

class QAInfoModel(BaseModel):
    id: str
    title: str
    steam: int
    originText: str
    className: str
    created_at: str
    mode: str
    difficulty: str
    questionCount: int

    class Config:
        allow_population_by_field_name = True

class QAInfoUpdateModel(BaseModel):
    title: Optional[str] = None
    steam: Optional[int] = None
    originText: Optional[str] = None
    className: Optional[str] = None
    created_at: Optional[str] = None
    mode: Optional[str] = None
    difficulty: Optional[str] = None
    questionCount: Optional[int] = None

class QAResultModel(BaseModel):
    id_qaid: str
    u_id: str
    user_answer: str
    true: int




class AnswerResult(BaseModel):
    qa_id: int
    select: Union[str, List[str], None]  # 選択肢
    user_answer: Union[str, List[str]]
    correct: Optional[bool] = None
    satisfaction: int # 入力なし０、good１、bad-1

class Submission(BaseModel):
    uid: str
    qa_info_id: str
    results: List[AnswerResult]