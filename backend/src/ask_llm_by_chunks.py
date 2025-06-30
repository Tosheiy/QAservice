from openai import OpenAI
import time
from datetime import datetime
import re
import os
from dotenv import load_dotenv

from src.SourceData import SourceData

from models import QAItemModel
import boto3
import json
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import urllib.request


load_dotenv()
OPENAI_APIKEY = os.getenv("OPENAI_API_KEY")

# 再送回数の制限
MAX_RETRIES = 5
# 再送間隔（秒）
RETRY_DELAY = 2
MAX_TOKEN = 10000

bedrock = boto3.client("bedrock-runtime", region_name="ap-northeast-1")

def get_response_with_retry_bedrock(system_text, send_text, mode):
    prompt = f"""
    <system>
    {system_text}
    </system>

    <user>
    {send_text}
    </user>
    """

    body_data = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "temperature": 0.7,
        "messages": [{"role": "user", "content": prompt}]
    }

    # --- ここで推論プロファイルの ARN を設定 ---
    inference_profile_arn = "arn:aws:bedrock:ap-northeast-1:753695775301:inference-profile/apac.anthropic.claude-3-sonnet-20240229-v1:0"

    # --- URLとヘッダの準備 ---
    region = "ap-northeast-1"
    service = "bedrock"
    model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
    endpoint = f"https://bedrock-runtime.{region}.amazonaws.com/model/{model_id}/invoke"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-amzn-bedrock-inference-config": json.dumps({
            "inferenceProfileArn": inference_profile_arn
        })
    }

    # --- SigV4署名付きHTTPリクエスト作成 ---
    session = boto3.Session()
    credentials = session.get_credentials().get_frozen_credentials()
    request = AWSRequest(method="POST", url=endpoint, data=json.dumps(body_data).encode("utf-8"), headers=headers)
    SigV4Auth(credentials, service, region).add_auth(request)
    signed_headers = dict(request.headers)

    # --- 実リクエスト ---
    req = urllib.request.Request(endpoint, data=json.dumps(body_data).encode("utf-8"), headers=signed_headers)
    with urllib.request.urlopen(req, timeout=60) as response:
        response_body = json.loads(response.read())
        response_text = response_body["content"][0]["text"]

    # --- タグ抽出処理（元の処理を流用） ---
    import re
    options = []

    # タグの中身を抽出
    question = re.findall(r"<question>(.*?)</question>", response_text, re.DOTALL)
    # question が空のときのエラーハンドリング
    if not question:
        print("❌ <question>タグが見つかりませんでした。")
        raise ValueError("<question>タグが空、または見つかりませんでした。")
    if mode != "記述式問題":
        # タグの中身を抽出
        options_bandles = re.findall(r"<options>(.*?)</options>", response_text, re.DOTALL)
        if not options_bandles:
            print("❌ <options>タグが見つかりませんでした。")
            raise ValueError("<options>タグが空、または見つかりませんでした。")
        # タグの中身を抽出
        for options_bandle in options_bandles:
            options = re.findall(r"<li>(.*?)</li>", options_bandle, re.DOTALL)
            if not options:
                print("❌ <li>タグが見つかりませんでした。")
                raise ValueError("<li>タグが空、または見つかりませんでした。")
            
    if mode == "４択複数選択問題":
        # タグの中身を抽出
        answer_bandles = re.findall(r"<answer>(.*?)</answer>", response_text, re.DOTALL)
        if not answer_bandles:
            print("❌ <answer>タグが見つかりませんでした。")
            raise ValueError("<answer>タグが空、または見つかりませんでした。")
        # タグの中身を抽出
        for answer_bandle in answer_bandles:
            answer = re.findall(r"<li>(.*?)</li>", answer_bandle, re.DOTALL)
            if not answer:
                print("❌ <li>タグが見つかりませんでした。")
                raise ValueError("<li>タグが空、または見つかりませんでした。")
    else:
        # タグの中身を抽出
        answer = re.findall(r"<answer>(.*?)</answer>", response_text, re.DOTALL)
        if not answer:
            print("❌ <answer>タグが見つかりませんでした。")
            raise ValueError("<answer>タグが空、または見つかりませんでした。")


    return question, options, answer



            
def get_response_with_retry(client, system_text, send_text, mode):
    for attempt in range(MAX_RETRIES):
        try:
            # APIリクエスト
            response = client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {"role": "system", "content": system_text},
                    {"role": "user", "content": send_text},
                ],
                stream=False
            )

            # 空のレスポンスチェック
            if not response or not response.choices:
                print(f"❌ 空のレスポンスが返ってきました (Attempt {attempt + 1}/{MAX_RETRIES})")
                raise ValueError("空のレスポンス")
            
            response_text = response.choices[0].message.content
            options = []

            # タグの中身を抽出
            question = re.findall(r"<question>(.*?)</question>", response_text, re.DOTALL)
            # question が空のときのエラーハンドリング
            if not question:
                print("❌ <question>タグが見つかりませんでした。")
                raise ValueError("<question>タグが空、または見つかりませんでした。")
            if mode != "記述式問題":
                # タグの中身を抽出
                options_bandles = re.findall(r"<options>(.*?)</options>", response_text, re.DOTALL)
                if not options_bandles:
                    print("❌ <options>タグが見つかりませんでした。")
                    raise ValueError("<options>タグが空、または見つかりませんでした。")
                # タグの中身を抽出
                for options_bandle in options_bandles:
                    options = re.findall(r"<li>(.*?)</li>", options_bandle, re.DOTALL)
                    if not options:
                        print("❌ <li>タグが見つかりませんでした。")
                        raise ValueError("<li>タグが空、または見つかりませんでした。")
                    
            if mode == "４択複数選択問題":
                # タグの中身を抽出
                answer_bandles = re.findall(r"<answer>(.*?)</answer>", response_text, re.DOTALL)
                if not answer_bandles:
                    print("❌ <answer>タグが見つかりませんでした。")
                    raise ValueError("<answer>タグが空、または見つかりませんでした。")
                # タグの中身を抽出
                for answer_bandle in answer_bandles:
                    answer = re.findall(r"<li>(.*?)</li>", answer_bandle, re.DOTALL)
                    if not answer:
                        print("❌ <li>タグが見つかりませんでした。")
                        raise ValueError("<li>タグが空、または見つかりませんでした。")
            else:
                # タグの中身を抽出
                answer = re.findall(r"<answer>(.*?)</answer>", response_text, re.DOTALL)
                if not answer:
                    print("❌ <answer>タグが見つかりませんでした。")
                    raise ValueError("<answer>タグが空、または見つかりませんでした。")


            return question, options, answer
        
        except ValueError as e:
            print(f"❌ エラーが発生しました: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                print(f"再送信を試みます... ({RETRY_DELAY}秒待機)")
                time.sleep(RETRY_DELAY)
            else:
                print("再送信の上限回数に達しました。処理を終了します。")
                raise




def ask_llm_by_chunks(s_data: SourceData):
    client = OpenAI(api_key=OPENAI_APIKEY)

    csv_system_prompt = ""
    csv_user_prompt = ""
    if s_data.user_qa != []:
        csv_system_prompt, csv_user_prompt = make_csv_prompt(s_data)

    options_text = ""
    options_ex = ""
    if s_data.mode != '記述式問題':
        options_text = '''
        ・作成した選択肢を<options></options>の中に入れてください。それぞれの選択肢を<li></li>の中に入れてください。\n 
        '''
        options_ex = '''
        <options>
            <li>札幌市</li>
            <li>会津若松市</li>
            <li>長浜市</li>
            <li>神栖市</li>
        </options>
        \n
        '''
    answers_text = "・作成した問題に対する答えを<answer></answer>に記載してください。"
    answers_ex = '''
    <answer>
    東京
    </answer>
    '''
    if s_data.mode == '４択複数選択問題':
        answers_text = '''
        ・作成した問題に対する答えを<answer></answer>の中に入れてください。それぞれの答えを<li></li>の中に入れてください。\n 
        '''
        answers_ex = '''
        <answer>
            <li>札幌市</li>
            <li>京都市</li>
            <li>長浜市</li>
            <li>広島市</li>
        </answer>
        \n
        '''
    system_text = f'''
    あなたは、[テキスト]から{s_data.mode}クイズを難易度[{s_data.difficulty}]で作成する優秀なアシスタントです。\n
    【ルール】
    ・作成した問題を<question></question>タグを用いてその中に記載してください。
    {options_text}
    {answers_text}
    【例】
    <question>
    日本の政令指定都市はどこですか
    </question>
    {options_ex}
    {answers_ex}
    {csv_system_prompt}
    '''

    qa_list = []
    qa_id = 0
    id = "hoge"
    created_at = datetime.now().strftime("%Y%m%d%H%M")
    for text in s_data.chunk_text:

        text = "[テキスト]\n" + text

        text += csv_user_prompt

        question, options, answer = get_response_with_retry(client, system_text=system_text, send_text=text, mode=s_data.mode)
        # question, options, answer = get_response_with_retry_bedrock(system_text=system_text, send_text=text, mode=s_data.mode)
        
        qaitem = QAItemModel(
            id=id,
            qa_id=qa_id,
            question=question[0],
            options=options,
            answer=answer,
        )
        qa_id += 1
        qa_list.append(qaitem)



    return qa_list



def make_csv_prompt(s_data, max_token=4000):
    csv_system_prompt = (
        "[追加資料]は過去の質問とその解答です。この情報も参考にしてQAを生成してください。\n"
    )
    
    csv_user_prompt = "\n\n[追加資料]\n"
    total_tokens = 0

    for i, row in enumerate(s_data.user_qa):
        question = row.get("質問") or row.get("question") or ""
        answer = row.get("回答") or row.get("answer") or ""

        entry = f"Q {i+1}: {question}\nA {i+1}: {answer}\n\n"
        entry_tokens = len(entry)

        if total_tokens + entry_tokens > max_token:
            break

        csv_user_prompt += entry
        total_tokens += entry_tokens

    return csv_system_prompt, csv_user_prompt