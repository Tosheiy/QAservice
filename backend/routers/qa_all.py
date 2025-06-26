from fastapi import APIRouter, HTTPException
from models import QAItemModel, QAInfoModel, QAResultModel
from db import qa_item_table, qa_info_table, qa_result_table

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


@router.get("/qadetails/{id}")
def get_qa_detail(id: str):
    info_response = qa_info_table.get_item(Key={'id': id})
    info_item = info_response.get('Item')
    if not info_item:
        raise HTTPException(status_code=404, detail="QAInfo not found")
    
    item_response = qa_item_table.get_item(Key={'id': id})
    item = item_response.get('Item')
    if not item:
        raise HTTPException(status_code=404, detail="QAItem not found")
    
    result_response = qa_result_table.get_item(Key={'id': id})
    result_item = result_response.get('Item')
    if not result_item:
        raise HTTPException(status_code=404, detail="QAResult not found")
    

    


    return 