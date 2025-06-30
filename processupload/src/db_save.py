from uuid import uuid4
from src.SourceData import SourceData
from models import QAInfoModel, QAItemModel

from datetime import datetime
from typing import List

from db import qa_item_table, qa_info_table



def db_save_to_QAinfo(s_data: SourceData):
    id = s_data.id

    if id == "":
        id = str(uuid4())

    # 各項目を個別に抽出して変数に代入
    title = s_data.filename
    steam = 0
    originText = s_data.texts
    class_name = "授業名を設定してください"
    created_at = datetime.now().strftime("%Y%m%d%H%M")
    mode = s_data.mode
    difficulty = s_data.difficulty
    question_count = s_data.questionCount

    # モデルに1つずつ渡す（明示的に）
    qa_info = QAInfoModel(
        id=id,
        title=title,
        steam=steam,
        originText=originText,
        className=class_name,
        created_at=created_at,
        mode=mode,
        difficulty=difficulty,
        questionCount=question_count
    )

    # 辞書に変換（DynamoDBに送る際、alias付きで）
    item = qa_info.dict(by_alias=True)

    # 保存（DynamoDBクライアントは事前に定義しておく）
    qa_info_table.put_item(Item=item)

    return id


def db_save_to_QAitem(id: str, result_question: List[QAItemModel]):

    for qa_item in result_question:
        # モデルに1つずつ渡す（明示的に）
        qa_item.id = id
        # 辞書に変換（DynamoDBに送る際、alias付きで）
        item = qa_item.dict(by_alias=True)

        # 保存（DynamoDBクライアントは事前に定義しておく）
        qa_item_table.put_item(Item=item)

    return id