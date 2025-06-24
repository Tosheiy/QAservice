from openai import OpenAI
import time
from datetime import datetime
import re
import os
from dotenv import load_dotenv


from src.QAModel import QAItem
from src.SourceData import SourceData

load_dotenv()
OPENAI_APIKEY = os.getenv("OPENAI_API_KEY")

# 再送回数の制限
MAX_RETRIES = 5
# 再送間隔（秒）
RETRY_DELAY = 2

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

            # タグの中身を抽出（re.DOTALL で改行を含める）
            question = re.findall(r"<question>(.*?)</question>", response_text, re.DOTALL)
            # question が空のときのエラーハンドリング
            if not question:
                print("❌ <question>タグが見つかりませんでした。")
                raise ValueError("<question>タグが空、または見つかりませんでした。")
            if mode != "記述式問題":
                # タグの中身を抽出（re.DOTALL で改行を含める）
                options_bandles = re.findall(r"<options>(.*?)</options>", response_text, re.DOTALL)
                # question が空のときのエラーハンドリング
                if not options_bandles:
                    print("❌ <options>タグが見つかりませんでした。")
                    raise ValueError("<options>タグが空、または見つかりませんでした。")
                # タグの中身を抽出（re.DOTALL で改行を含める）
                for options_bandle in options_bandles:
                    options = re.findall(r"<li>(.*?)</li>", options_bandle, re.DOTALL)
                    if not options:
                        print("❌ <li>タグが見つかりませんでした。")
                        raise ValueError("<li>タグが空、または見つかりませんでした。")
            # タグの中身を抽出（re.DOTALL で改行を含める）
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

    options_text = ""
    options_ex = ""
    if s_data.mode != '記述式問題':
        options_text = '''
        ・作成した選択肢を<options></options>の中に入れてください。それぞれの選択肢を<li></li>の中に入れてください。\n 
        '''
        options_ex = '''
        【例】
        <options>
            <li>東京</li>
            <li>ロンドン</li>
            <li>パリ</li>
            <li>カリフォルニア</li>
        </options>
        \n
        '''
    system_text = f'''
    あなたは、テキストから{s_data.mode}クイズを難易度{s_data.difficulty}で作成する優秀なアシスタントです。\n
    【ルール】
    ・作成した問題を<question></question>タグを用いてその中に記載してください。
    {options_text}
    ・作成した問題に対する答えを<answer></answer>に記載してください。
    【例】
    <question>
    日本の首都はどこですか
    </question>
    {options_ex}
    <answer>
    東京
    </answer>

    '''

    qa_list = []
    qa_id = 0
    id_num = 0
    created_at = datetime.now().strftime("%Y%m%d%H%M")
    for text in s_data.chunk_text:
        
        question, options, answer = get_response_with_retry(client, system_text=system_text, send_text=text, mode=s_data.mode)
        
        qaitem = QAItem(
            id=id_num,
            qa_id=qa_id,
            created_at=created_at,
            question=question[0],
            options=options,
            answer=answer[0],
            mode=s_data.mode,
            difficulty=s_data.difficulty,
            title=s_data.filename
        )
        qa_id += 1
        qa_list.append(qaitem)

    return qa_list