from fastapi import APIRouter, HTTPException
from models import QAItemModel, QAInfoModel, QAResultModel, Submission
from db import qa_item_table, qa_info_table, qa_result_table
from collections import defaultdict, Counter
from boto3.dynamodb.conditions import Key
from routers.qa_result import normalize


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
