from fastapi import APIRouter, HTTPException
from models import QAInfoModel, QAInfoUpdateModel
from db import qa_info_table

router = APIRouter()


# QAデータベースに手動追加する時に使用（デバック用）
@router.post("/qainfo")
def create_qa_info(info: QAInfoModel):
    qa_info_table.put_item(Item=info.dict())
    return {"message": "QAInfo created successfully"}

# QAデータベースのリストを返す部分
@router.get("/qainfo")
def get_all_qa_info():
    # テーブル全体をスキャン
    response = qa_info_table.scan()
    items = response.get('Items', [])

    # 各アイテムから id と title だけを取り出す
    result = [{"id": item["id"], "title": item["title"]} for item in items if "id" in item and "title" in item]

    return result

# QAデータベースのDetailの部分で使用
@router.get("/qainfo/{id}")
def get_qa_info(id: str):
    '''
    以下を返す
    {
        id: number;
        created_at: string;
        class: string;
        title: string;
        mode: string;
        questionCount: int
    }
    '''
    response = qa_info_table.get_item(Key={'id': id})
    item = response.get('Item')
    if not item:
        raise HTTPException(status_code=404, detail="QAInfo not found")
    

    # 必要な項目だけを抽出して返す
    filtered = {
        "id": item.get("id"),
        "created_at": item.get("created_at"),
        "className": item.get("className"),
        "title": item.get("title"),
        "mode": item.get("mode"),
        "questionCount": item.get("questionCount")
    }

    return filtered


# QAデータベースのEditの部分で使用
@router.patch("/qainfo/{id}")
def patch_qa_info(id: str, update_data: QAInfoUpdateModel):
    update_fields = update_data.dict(exclude_unset=True)
    if not update_fields:
        raise HTTPException(status_code=400, detail="No update fields provided.")

    # 存在確認
    if 'Item' not in qa_info_table.get_item(Key={"id": id}):
        raise HTTPException(status_code=404, detail="QAInfo not found.")

    update_expr_parts = []
    expr_values = {}
    expr_names = {}

    for k, v in update_fields.items():
        if k == "mode":  # 予約語の場合は置き換え
            update_expr_parts.append(f"#mode = :{k}")
            expr_values[f":{k}"] = v
            expr_names["#mode"] = "mode"
        else:
            update_expr_parts.append(f"{k} = :{k}")
            expr_values[f":{k}"] = v

    update_expr = "SET " + ", ".join(update_expr_parts)

    qa_info_table.update_item(
        Key={"id": id},
        UpdateExpression=update_expr,
        ExpressionAttributeValues=expr_values,
        ExpressionAttributeNames=expr_names if expr_names else None
    )

    return {"message": f"QAInfo with id {id} updated successfully."}

# QAデータベースのEditの部分で使用
@router.delete("/qainfo/{id}")
def delete_qa_info(id: str):
    # 存在確認
    response = qa_info_table.get_item(Key={"id": id})
    if 'Item' not in response:
        raise HTTPException(status_code=404, detail="QAInfo not found")

    # 削除処理
    qa_info_table.delete_item(Key={"id": id})
    return {"message": f"QAInfo with id {id} deleted successfully."}



@router.get("/check_status")
def check_status(id: str):
    try:
        response = qa_info_table.get_item(Key={'id': id})
        item = response.get('Item')
        if not item:
            raise HTTPException(status_code=404, detail="QAInfo not found")
        return {"status": "completed"}
    except HTTPException as e:
        raise e  # ← ここで 500 に上書きせず、そのまま返す
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DynamoDB error: {str(e)}")