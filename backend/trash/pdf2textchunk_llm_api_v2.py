import pymupdf4llm
from langchain.text_splitter import MarkdownHeaderTextSplitter
import pickle

from openai import OpenAI
from tqdm import tqdm
import time
from natsort import natsorted

import re
import os

# 再送回数の制限
MAX_RETRIES = 5
# 再送間隔（秒）
RETRY_DELAY = 2

def split_markdown(text, max_length=1500, overlap=300):
    chunks = []
    i = 0
    while i < len(text):
        chunks.append(text[i:i + max_length])
        i += max_length - overlap  # オーバーラップ分を調整
    return chunks

def get_response_with_retry(client, system_text, send_text):
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
            
            formatted_text = response.choices[0].message.content
            # タグの中身を抽出（re.DOTALL で改行を含める）
            markdowns_in = re.findall(r"<markdown>(.*?)</markdown>", formatted_text, re.DOTALL)
            # markdown が空のときのエラーハンドリング
            if not markdowns_in:
                print("❌ <markdown>タグが見つかりませんでした。")
                raise ValueError("<markdown>タグが空、または見つかりませんでした。")

            for markdown in markdowns_in:
                # タグの中身を抽出（re.DOTALL で改行を含める）
                title = re.findall(r"<title>(.*?)</title>", markdown, re.DOTALL)
                # title が空のときのエラーハンドリング
                if not title:
                    print("❌ <title>タグが見つかりませんでした。")
                    raise ValueError("<title>タグが空、または見つかりませんでした。")



            
            # print("✅ レスポンス:", response)
            return response

        except ValueError as e:
            print(f"❌ エラーが発生しました: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                print(f"再送信を試みます... ({RETRY_DELAY}秒待機)")
                time.sleep(RETRY_DELAY)
            else:
                print("再送信の上限回数に達しました。処理を終了します。")
                raise


title_list = [
    "4℃ホールディングレポート2024",
    "IHI統合報告書2024",
    "NISSAN(日産)サステナビリティデータブック",
    "KAGOME統合報告書",
    "KITZ(キッツ)コーポレートレポート",
    "株式会社クレハサステナビリティレポート",
    "GLORY統合報告書",
    "サントリーグループレポート",
    "ハウス食品グループ統合レポート",
    "パナソニックグループレポート",
    "Media Do(メディアドゥ)レポート",
    "モスグループ統合レポート",
    "ライフ統合レポート",
    "高松コンストラクショングループ統合報告書",
    "全国保証株式会社統合報告書",
    "東急不動産ホールディングス統合報告書",
    "TOYO ENGINEERING統合報告書",
    "日清食品ホールディングス統合報告書",
    "明治ホールディングス株式会社(meiji)統合報告書"
]
title_list_valid = [
    "ウエルシアホールディングス株式会社(welcia)統合報告書",
    "エクシオグループ株式会社(exeo)統合報告書2024",
    "ダイドーグループホールディングス(DyDo)統合報告書2024",
    "花王統合レポート2024",
    "太陽誘電株式会社統合報告書2024",
    "大成温調株式会社統合報告書2024",
    "大和ハウスサステナビリティレポート",
    "株式会社電通グループ統合レポート2024",
    "東洋紡グループ統合報告書2024",
    "日本化薬グループサステナビリティレポート"
]

exception_list = []
client = OpenAI(api_key='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')
# 一つのPDFをチャンク毎に分けてそれぞれのテキストをリストに保存（.pkl）
for file_num in range(1, 20):
    folder_path = f".\documents_divid\{str(file_num)}"
    page_list = os.listdir(folder_path)
    # 自然順序でソート
    page_list = natsorted(page_list)
    page_num = 0
    os.makedirs(f".\documents_divid_md_2\{str(file_num)}", exist_ok=True)

    for page_name in page_list:
        page_num += 1
        target_file = os.path.join(folder_path, page_name)
        md_text = pymupdf4llm.to_markdown(target_file)


        with open(f".\documents_divid_md_2\{str(file_num)}\{str(page_num)}.md", 'w', encoding='utf-8') as output_file:
            output_file.write(md_text)
        with open(f".\documents_divid_md_2\{str(file_num)}\{str(page_num)}.md", 'r', encoding='utf-8') as f:
            markdown_text = f.read()


        os.makedirs(f".\documents_formatted_divid_md_2\{str(file_num)}", exist_ok=True)

        formatted_text_list = []
        cnt_send = 0
        system_text = '''
                あなたはRAGのデータベースを作成する優秀なアシスタントです。markdownテキストを成形し、内容の区切りごとに分けてください。\n
                【ルール】
                ・文章の意味の区切り（チャンク）ごとに<markdown></markdown>タグを用いて分けてください。
                ・話題が変わったりしたときに区切ってください。大体１チャンク250から500文字を目安にし、すべての内容を区切るようにしてください。
                ・各内容の区切り（チャンク）のタイトルを推測して、<markdown></markdown>の中の<title></title>のタグの中に書いてください。
                ・成形ができないほど崩れているときは、意味を推測して補完してください。
                ・無駄な改行は少なくしてください。
                ・図や表、グラフ（---などのmarkdown式の表など）はリスト形式のようなわかりやすい文字ベースに変換してください。
                【例】
                <markdown>
                <title>これは例です。</title>
                これは例です。
                </markdown>
                <markdown>
                <title>これは例2です。</title>
                これは例2です。
                </markdown>   
                ...    
        '''
        
        # 使用例

        response = get_response_with_retry(client, system_text, markdown_text)

        formatted_text = response.choices[0].message.content
        markdowns = re.findall(r"<markdown>(.*?)</markdown>", formatted_text, re.DOTALL)

        for markdown in markdowns:
            cnt_send += 1
            # タグの中身を抽出（re.DOTALL で改行を含める）
            title = re.findall(r"<title>(.*?)</title>", markdown, re.DOTALL)
            input_text_main = f"# {title_list[int(file_num)-1]}\n"
            input_text_page = f"## {title[0]}\n"
            clean_text = re.sub(r"<title>.*?</title>\s*", "", markdown)
        
            complete_markdown = input_text_main + input_text_page + clean_text

            # Markdownファイルとして保存
            with open(f".\documents_formatted_divid_md_2\{file_num}\{page_num}-{cnt_send}.md", "w", encoding="utf-8") as f:
                f.write(complete_markdown)

print(exception_list)