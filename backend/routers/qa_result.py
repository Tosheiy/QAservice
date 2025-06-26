from fastapi import APIRouter, HTTPException
from models import QAResultModel
from db import qa_result_table

router = APIRouter()

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