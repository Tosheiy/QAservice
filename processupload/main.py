import boto3
import os
import traceback

from src.ask_llm_by_chunks import ask_llm_by_chunks
from src.SourceData import SourceData
from src.db_save import db_save_to_QAinfo, db_save_to_QAitem
import time
from urllib.parse import unquote_plus

s3_client = boto3.client("s3")


def lambda_handler(event, context):
    print("✅ Lambda Triggered with event:", event)

    try:
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        key = unquote_plus(key)
        print(f"📄 ファイルがアップロードされました: {bucket}/{key}")

        # 🔁 リトライ付き head_object
        max_retries = 20
        wait_seconds = 3
        for attempt in range(max_retries):
            try:
                s3_object = s3_client.head_object(Bucket=bucket, Key=key)
                break
            except s3_client.exceptions.ClientError as e:
                if e.response['Error']['Code'] == "404":
                    print(f"[{attempt+1}/{max_retries}] オブジェクトがまだ見つかりません: {key}")
                    if attempt < max_retries - 1:
                        time.sleep(wait_seconds)
                    else:
                        print("❌ 最大リトライ回数に達しました")
                        return {"status": "not_found", "key": key}
                else:
                    raise

        metadata = s3_object.get("Metadata", {})
        question_count = int(metadata.get("questioncount", 3))  # デフォルト3
        mode = metadata.get("mode", "multiple-choice")
        difficulty = metadata.get("difficulty", "middle")
        uuid = metadata.get("uuid", "")

        mode_map = {
            "three": "３択問題",
            "four": "４択問題",
            "multi": "４択複数選択問題",
            "script": "記述式問題"
        }

        mode = mode_map.get(mode, "４択問題")

        # S3からコンテンツ取得
        response = s3_client.get_object(Bucket=bucket, Key=key)
        contents = response["Body"].read()
        filename = os.path.basename(key)
        print(f"✅ 取得成功: {filename}（{len(contents)}バイト）")

        _, ext = os.path.splitext(filename)
        ext = ext.lower()

        if ext == ".pdf":
            s_data = SourceData(contents, question_count, mode, difficulty, filename)
            texts = s_data.pdf2text()
        elif ext == ".txt":
            texts = contents.decode("utf-8")
            s_data = SourceData(contents, question_count, mode, difficulty, filename)
            s_data.texts = texts
        else:
            raise Exception("対応していないファイル形式です")
        
        s_data.id = uuid

        text_chunk = s_data.text2chunk()
        result_question = ask_llm_by_chunks(s_data)

        id = db_save_to_QAinfo(s_data)
        id = db_save_to_QAitem(id, result_question)

        print("✅ 成功: id =", id)
        return {"status": "success", "id": id}

    except s3_client.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print(f"オブジェクトが見つかりません: {key}")
            return  # またはリトライ待ち処理
        else:
            raise  # その他のエラーはそのまま上げる
