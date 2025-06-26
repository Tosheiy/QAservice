from fastapi import APIRouter, HTTPException
from models import QAItemModel, QAItemUpdateModel
from db import qa_item_table
from boto3.dynamodb.conditions import Key
from typing import List


router = APIRouter()

# QAデータベースに手動追加する時に使用（デバック用）
@router.post("/qaitem/")
def create_qa_item(item: QAItemModel):
    qa_item_table.put_item(Item=item.dict())
    return {"message": "QAItem created successfully"}

# 特に使用用途を決めてない
@router.get("/qaitem/{id}/{qa_id}")
def get_qa_item(id: str, qa_id: int):
    response = qa_item_table.get_item(Key={'id': id, 'qa_id': qa_id})
    item = response.get('Item')
    if not item:
        raise HTTPException(status_code=404, detail="QAItem not found")
    return item


# QAデータベースのDetailに使用
@router.get("/qaitem/{id}")
def get_qa_items_by_id(id: str):
    # id に一致する全アイテムを取得（QueryではなくScan + Filterを避けるため Query）
    response = qa_item_table.query(
        KeyConditionExpression=Key('id').eq(id)
    )
    items = response.get('Items', [])

    # 必要なフィールドだけに整形
    result = [
        {
            "qa_id": item.get("qa_id"),
            "question": item.get("question"),
            "options": item.get("options"),  # DynamoDB側で `options` というキーなら
            "answer": item.get("answer"),
            "satisfaction": item.get("satisfaction", 0)  # デフォルト0
        }
        for item in items
        if all(k in item for k in ("qa_id", "question", "options", "answer"))
    ]

    return result


# QAデータベースのEditに使用
@router.patch("/qaitem/{id}")
def patch_qa_items(id: str, items: List[QAItemUpdateModel]):
    if not items:
        raise HTTPException(status_code=400, detail="No update items provided.")

    updated = []

    for item in items:
        update_fields = item.dict(exclude_unset=True)
        qa_id_val = update_fields.pop("qa_id", None)


        if qa_id_val is None or not update_fields:
            continue

        # UpdateExpression 構築
        update_expr = "SET " + ", ".join(f"{k}=:{k}" for k in update_fields)
        expr_values = {f":{k}": v for k, v in update_fields.items()}

        try:
            # 存在確認
            resp = qa_item_table.get_item(Key={"id": id, "qa_id": qa_id_val})
            if "Item" not in resp:
                continue

            # 更新実行
            qa_item_table.update_item(
                Key={"id": id, "qa_id": qa_id_val},
                UpdateExpression=update_expr,
                ExpressionAttributeValues=expr_values
            )
            updated.append({"id": id, "qa_id": qa_id_val})

        except Exception as e:
            continue  # 一部失敗しても残りは処理する

    return {"updated_items": updated, "count": len(updated)}


# QAデータベースのEditに使用
@router.delete("/qaitem/{id}")
def delete_qa_info_all(id: str):
    # 1. Query: 指定idに紐づく全アイテムを取得（パーティションキーがid）
    response = qa_item_table.query(
        KeyConditionExpression=Key('id').eq(id)
    )
    items = response.get('Items', [])

    if not items:
        raise HTTPException(status_code=404, detail=f"No items found with id {id}")

    # 2. 削除ループ
    for item in items:
        key = {k: item[k] for k in ('id', 'qa_id')}  # ← ソートキー名に合わせて変更
        qa_item_table.delete_item(Key=key)

    return {"message": f"Deleted {len(items)} items with id={id}."}