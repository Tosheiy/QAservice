import io 
from PyPDF2 import PdfReader

class SourceData:
    def __init__(self, row_file, questionCount, mode, difficulty, filename, className="授業名を設定してください", steam=0):
        self.row_file = row_file
        self.questionCount = questionCount
        self.mode = mode
        self.difficulty = difficulty
        self.filename = filename
        self.texts = ""
        self.chunk_text = []
        self.user_qa = []
        self.className = className
        self.steam = steam

    # def pdf2text(self):
    #     pdf = fitz.open(stream=self.row_file, filetype="pdf")
        
    #     for page in pdf:
    #         self.texts += page.get_text()

    #     pdf.close()

    #     return self.texts

    # def pdf2text(self):

    #     # バイトデータをファイルのように扱うために BytesIO に包む
    #     with pdfplumber.open(io.BytesIO(self.row_file)) as pdf:
    #         for i, page in enumerate(pdf.pages):
    #             page_text = page.extract_text() or ""  # None の可能性があるため fallback
    #             print(f"[ページ {i+1}] の抽出テキスト:\n{page_text[:300]}")  # 先頭300文字だけ表示
    #             self.texts += page_text + "\n"

    #     return self.texts

    # def pdf2text(self):
    #     pdf_file = io.BytesIO(self.row_file)
    #     text = extract_text(pdf_file)
    #     print("[抽出されたテキスト]", text[:300])
    #     return text

    def pdf2text(self):
        self.texts = ""


        # self.row_file は bytes であることを想定
        pdf_stream = io.BytesIO(self.row_file)
        reader = PdfReader(pdf_stream)

        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            self.texts += text + "\n"

        return self.texts

    def text2chunk(self):
        length = len(self.texts)
        q_num = self.questionCount
        chunk_size = (length + q_num - 1) // q_num
        self.chunk_text = [self.texts[i * chunk_size: (i + 1) * chunk_size] for i in range(q_num)]
        
        return self.chunk_text