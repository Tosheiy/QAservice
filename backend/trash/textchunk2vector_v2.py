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

# Load environment variables from .env file
load_dotenv()
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
API_VERSION = os.getenv("API_VERSION")
DEPLOYMENT_ID_FOR_CHAT_COMPLETION = os.getenv("DEPLOYMENT_ID_FOR_CHAT_COMPLETION")
DEPLOYMENT_ID_FOR_EMBEDDING = os.getenv("DEPLOYMENT_ID_FOR_EMBEDDING")
# 【1-3】AzureOpenAI のクライアントを初期化
client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version=API_VERSION
)
print("Azure OpenAI Service の設定が完了しました。")


def get_embedding_vector(text):
    # --- ユーザークエリをEmbedding ---
    response = client.embeddings.create(
        input=text,
        model=DEPLOYMENT_ID_FOR_EMBEDDING
    )
    query_vector = response.data[0].embedding

    return query_vector
    

contents = []
for file_num in range(1, 20):
    folder_path = f".\documents_formatted_divid_md_2\{str(file_num)}"
    page_list = os.listdir(folder_path)
    # 自然順序でソート
    page_list = natsorted(page_list)

    for page_name in tqdm(page_list):
        target_file = os.path.join(folder_path, page_name)

        with open(target_file, 'r', encoding='utf-8') as f:
            target_text = f.read()  # ファイルのすべての行をリストとして取得
 
            vector = get_embedding_vector(target_text)
            contents.append({"text": target_text, "vector": vector})


# ファイルに保存
with open("contents_2.pkl", "wb") as f:
    pickle.dump(contents, f)
# ファイルから読み込む
with open("contents_2.pkl", "rb") as f:
    contents = pickle.load(f)










## 評価
import faiss

# ベクトルの次元数（例えば、3次元ベクトルの場合）
d = 3072

# FAISSインデックスの作成（L2距離を使用）
index = faiss.IndexFlatL2(d)

# ベクトルをインデックスに追加
vectors = np.array([content['vector'] for content in contents]).astype('float32')
index.add(vectors)

# 検索クエリのベクトル（例として3次元ベクトルを使用）
query_text = "メディアドゥが取引する出版社は何社以上？"
query_vector = get_embedding_vector(query_text)
# query_vector を NumPy 配列に変換
query_vector = np.array(query_vector)
# query_vector を NumPy 配列に変換し、形状を (1, d) にリシェイプ
query_vector = np.array(query_vector).reshape(1, -1)  # 1行、d列

# 検索を実行（k=3は、最も類似した3つのベクトルを返す）
k = 3
distances, indices = index.search(query_vector, k)

# 結果を表示
print("Distances:", distances)
print("Indices:", indices)

# 最も類似したテキストを表示
for idx in indices[0]:
    print(contents[idx]['text'])


exit()