from fastapi import APIRouter, HTTPException, Query
from models import QAResultModel, Submission
from boto3.dynamodb.conditions import Key
from db import qa_result_table, qa_item_table

router = APIRouter()

import unicodedata
import re

import unicodedata

import unicodedata

def normalize(text) -> list[str]:
    """
    文字列またはリストを受け取り、正規化された文字列のリストに変換
    """
    if isinstance(text, list):
        items = text
    # こちら側に入るのは望ましくない
    elif isinstance(text, str):
        text = text.strip()
        # カンマや改行で分割
        items = [s for s in text.replace('\n', '').split('、') if s.strip()]
    else:
        return []

    # 各要素を正規化して整形
    return [unicodedata.normalize('NFKC', item.strip()) for item in items]






@router.post("/qaresult/")
def create_qa_result(result: QAResultModel):
    qa_result_table.put_item(Item=result.dict())
    return {"message": "QAResult created successfully"}

@router.get("/qaresult/{id_qaid}/{u_id}")
def get_qa_result(id_qaid: str, u_id: str):
    response = qa_result_table.get_item(Key={'id_qaid': id_qaid, 'u_id': u_id})
    item = response.get('Item')
    if not item:
        raise HTTPException(status_code=404, detail="QAResult not found")
    return item




@router.get("/qaresult/{id}")
def check_is_solved(id: str, u_id: str = Query(...)):
    """
    指定された id_qaid と u_id の組み合わせが存在するかを確認。
    """
    id = id + '-0'
    response = qa_result_table.query(
        KeyConditionExpression=Key("id_qaid").eq(id) & Key("u_id").eq(u_id)
    )

    is_solved = 1 if response.get("Count", 0) > 0 else 0
    return {"is_solved": is_solved}