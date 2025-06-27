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

@router.post("/submit")
def submit_answers(submission: Submission):

    # クイズ全体に対して一括取得（そのinfo_idの全qa_id分）
    response = qa_item_table.query(
        KeyConditionExpression=Key("id").eq(submission.qa_info_id)
    )
    correct_map = {
        int(item["qa_id"]): item["answer"] for item in response.get("Items", [])
    }

    for result in submission.results:
        # ここでクイズが合ってるか確認してcorrectに入れる
        correct_answer = correct_map.get(result.qa_id)


        normalized_answer = normalize(correct_answer)
        normalized_user = normalize(result.user_answer)

        print('normalized_answer:', normalized_answer)
        print('normalized_user:', normalized_user)

        # 回答が順不同で正解かどうか
        result.correct = set(normalized_answer) == set(normalized_user)


        print(f"正解: {repr(correct_answer)} / 回答: {repr(result.user_answer)}")
        print(f"等しいか？: {normalize(correct_answer) == normalize(result.user_answer)}")

        print(result.satisfaction)
        
        item = {
            "id_qaid": f"{submission.qa_info_id}-{result.qa_id}",  # パーティションキー
            "u_id": submission.uid,                                 # ソートキー
            "select": result.select,
            "user_answer": result.user_answer,
            "satisfaction": result.satisfaction,
            "correct": result.correct
        }
        qa_result_table.put_item(Item=item)

    return {"message": "解答が保存されました"}


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