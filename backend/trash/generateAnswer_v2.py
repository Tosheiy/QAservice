import pickle

import numpy as np
import faiss
import pandas as pd

# 【1-1】必要なライブラリのインポート
from openai import AzureOpenAI  # Azure OpenAI Service を扱うためのクライアント
import pandas as pd  # CSVやテーブル形式のデータを扱うためのライブラリ
import numpy as np   # 数値演算ライブラリ（ベクトルや行列演算に使用）
from dotenv import load_dotenv
import os
import time
from tqdm import tqdm
import pickle
from natsort import natsorted
import re
import ast
from openai import OpenAI

MAX_RETRIES = 10
RETRY_DELAY = 0.2

def get_response_with_retry(client, system_text, send_text):
    for attempt in range(MAX_RETRIES):
        try:
            answer = client.chat.completions.create(
                model="gpt-4o",  #"gpt-4o-mini-2024-07-18",
                messages=[
                    {"role": "system", "content": system_text},
                    {"role": "user", "content": send_text},
                ],
                max_tokens=3000,     # 応答に使えるトークン数上限
                temperature=1.0,     # 創造性（0~1） 0.7:0.45 0.3:0.43 1.0:0.50
                top_p=0.95,          # nucleus sampling 0.95
                frequency_penalty=0, # 0
                presence_penalty=0, # 0
                stop=None,
                stream=False
            )

            # 空のレスポンスチェック
            if not answer or not answer.choices:
                print(f"❌ 空のレスポンスが返ってきました (Attempt {attempt + 1}/{MAX_RETRIES})")
                raise ValueError("空のレスポンス")
            
            return_text = answer.choices[0].message.content
            # タグの中身を抽出（re.DOTALL で改行を含める）
            answer_in = re.findall(r"<answer>(.*?)</answer>", return_text, re.DOTALL)
            # markdown が空のときのエラーハンドリング
            if not answer_in:
                print("❌ <answer>タグが見つかりませんでした。")
                raise ValueError("<answer>タグが空、または見つかりませんでした。")



            
            # print("✅ レスポンス:", response)
            return answer

        except ValueError as e:
            print(f"❌ エラーが発生しました: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                print(f"再送信を試みます... ({RETRY_DELAY}秒待機)")
                time.sleep(RETRY_DELAY)
            else:
                print("再送信の上限回数に達しました。処理を終了します。")
                raise



# 【1-3】AzureOpenAI のクライアントを初期化
client = OpenAI(api_key='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')


# ファイルから読み込む
with open("contents_2.pkl", "rb") as f:
    contents = pickle.load(f)

# ベクトルの次元数（例えば、3次元ベクトルの場合）
d = 3072

# FAISSインデックスの作成（L2距離を使用）
index = faiss.IndexFlatL2(d)

# ベクトルをインデックスに追加
vectors = np.array([content['vector'] for content in contents]).astype('float32')
index.add(vectors)

df = pd.read_csv(".\query_with_vectors.csv")
df_answer = pd.read_csv(r"C:\Users\asf72\Document\AI\SIGNATE\competition_finance\data\sample_submit\predictions.csv") 

df_ansamble = pd.DataFrame(columns=["problem", "model1"])

system_content = (
        "ステップバイステップで考えてください。"
        "回答を簡潔に40文字以内で改行も入れず<answer></answer>のタグの中に入れてください。"
        "【質問】と【質問】に関連する【コンテキスト】が10個与えられます。すべての【コンテキスト】を参考にして答えを出力してください。"
        "ユーザーが与えた情報だけをもとに回答してください。"
        "情報がコンテキストに含まれない場合は『わかりません』とだけ答えてください。"
    )
# 1行ずつループ
for idx, row in tqdm(df.iterrows()):
    query_problem = row['problem']
    query_vector = row['vector']

    # 文字列からリストに変換
    query_vector = ast.literal_eval(query_vector)
    # query_vector を NumPy 配列に変換
    query_vector = np.array(query_vector, dtype=np.float32)
    # query_vector を NumPy 配列に変換し、形状を (1, d) にリシェイプ
    query_vector = np.array(query_vector).reshape(1, -1)  # 1行、d列

    # 検索を実行（k=3は、最も類似した3つのベクトルを返す）
    k = 10
    distances, indices = index.search(query_vector, k)

    # ループを使用して、インデックスに対応するテキストを繰り返し追加
    content = ""
    for idx_2 in indices[0]:
        content += f"\n---\n{contents[idx_2]['text']}"

    user_content = (
        "【質問】\n"
        f"{query_problem}\n\n"
        "【コンテキスト】\n"
        f"{content}"
    )

    # ファイルに書き込む
    with open(f'./outputs/output_{idx}.txt', 'w', encoding='utf-8') as f:
        f.write(user_content)  # テキストをそのまま保存

    response = get_response_with_retry(client, system_content, user_content).choices[0].message.content

    answer = re.findall(r"<answer>(.*?)</answer>", response, re.DOTALL)

    df_answer.at[idx, "value"] = answer[0]

    idx_ansamble = len(df_ansamble)
    df_ansamble.loc[idx_ansamble] = [query_problem, response]




df_answer.to_csv("predictions.csv", header=False, index=False)
df_ansamble.to_csv("./model/model3.csv")
exit()