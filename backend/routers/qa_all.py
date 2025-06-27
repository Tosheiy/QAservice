from fastapi import APIRouter, HTTPException, File, Form, UploadFile
from models import QAItemModel, QAInfoModel, QAResultModel, Submission
from db import qa_item_table, qa_info_table, qa_result_table
from src.SourceData import SourceData
from collections import defaultdict, Counter
from boto3.dynamodb.conditions import Key
from routers.qa_result import normalize
import csv
import io
from typing import List, Dict, Optional
import os
from src.ask_llm_by_chunks import ask_llm_by_chunks
from src.db_save import db_save_to_QAinfo, db_save_to_QAitem


router = APIRouter()

'''
interface QAItem {
    qa_id: number;
    id: number;
    question: string;
    options: string[];
    answer: string;
    mode: string;
    created_at: string;
    class: string;
    title: string;
    satisfaction: number;
}
'''






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



@router.get("/qaanalysis/{id}")
def get_qa_detail(id: str):
    # QA Info を取得（単一）
    info_response = qa_info_table.get_item(Key={'id': id})
    info_item = info_response.get('Item')
    if not info_item:
        raise HTTPException(status_code=404, detail="QAInfo not found")

    # QAの各問題を取得（複数）
    item_response = qa_item_table.query(
        KeyConditionExpression=Key('id').eq(id)
    )
    items = item_response.get('Items', [])
    if not items:
        raise HTTPException(status_code=404, detail="No QA Items found")

    # 集計変数
    total_answers = 0
    total_correct = 0
    user_scores = defaultdict(int)
    quiz_data = []

    for item in items:
        qa_id = item["qa_id"]
        options = item.get("options", [])
        norm_options = normalize(options)

        # クイズ結果取得
        result_response = qa_result_table.query(
            KeyConditionExpression=Key("id_qaid").eq(f"{id}-{qa_id}")
        )
        results = result_response.get("Items", [])

        correct_count = 0
        option_count = Counter()
        user_set = set()

        good_count = 0
        neutral_count = 0
        bad_count = 0

        for r in results:
            selected = r.get("select")
            uid = r.get("u_id")
            is_correct = r.get("correct")
            satisfaction = r.get("satisfaction")


            if satisfaction is not None:
                if int(satisfaction) == 1:
                    good_count += 1
                elif int(satisfaction) == 0:
                    neutral_count += 1
                elif int(satisfaction) == -1:
                    bad_count += 1


            if uid:
                user_set.add(uid)
                if is_correct:
                    user_scores[uid] += 1

            if is_correct:
                correct_count += 1

            try:
                for sel in normalize(selected):

                    if sel in norm_options:
                        index = norm_options.index(sel)
                        print(f"{sel} found at index {index}")
                        option_count[index] += 1
            except ValueError:
                print(f"[WARNING] 選択肢に一致しない回答: {selected}")

        num_answers = len(results)
        total_answers += num_answers
        total_correct += correct_count

        # 分布
        option_distribution = {
            options[i]: option_count[i] / num_answers if num_answers else 0.0
            for i in range(len(options))
        }


        quiz_data.append({
            "qa_id": qa_id,
            "correct_rate": correct_count / num_answers if num_answers else None,
            "option_distribution": option_distribution,
            "total_answers": num_answers,
            "satisfaction_summary": {
                "good": good_count,
                "neutral": neutral_count,
                "bad": bad_count
            }
        })

    # 最終集計
    score_distribution = Counter(user_scores.values())


    return {
        "summary": {
            "total_answers": total_answers,
            "total_correct": total_correct,
            "overall_accuracy": total_correct / total_answers if total_answers else None
        },
        "score_distribution": dict(score_distribution),
        "per_quiz_analysis": quiz_data
    }



@router.post("/upload_csv/")
async def upload_pdf(    
    file: Optional[UploadFile] = File(None),  # ← ファイルを任意に
    questionCount: int = Form(...),
    mode: str = Form(...),
    difficulty: str = Form(...),
    id: str = Form(...),
):
    response = qa_info_table.get_item(Key={'id': id})
    item = response.get('Item')
    if not item:
        raise HTTPException(status_code=404, detail="QAInfo not found")

    s_data = SourceData(None, questionCount, mode, difficulty, item.get("title"), className=item.get("className"))
    s_data.texts = item.get("originText")
    chunk_text = s_data.text2chunk()
    
    if file:
        filename = file.filename
        contents = await file.read()
        s_data.row_file = contents

        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        if ext != ".csv":
            raise HTTPException(status_code=400, detail="対応していないファイル形式です")
        
        # CSV を辞書として読み込む
        try:
            text_stream = io.StringIO(contents.decode("utf-8"))
            reader = csv.DictReader(text_stream)
            csv_data: List[Dict[str, str]] = list(reader)
            s_data.user_qa = csv_data
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"CSVの読み込みに失敗しました: {str(e)}")
    else:
        print("ファイルはアップロードされていません。")

    result_question = ask_llm_by_chunks(s_data)
    id = db_save_to_QAinfo(s_data, id=id)
    id = db_save_to_QAitem(id, result_question)

    # ここに通常の処理を追加可能（s_data作成など）
    return {"message": "アップロード処理完了（CSVは" + ("あり" if file else "なし") + "）"}