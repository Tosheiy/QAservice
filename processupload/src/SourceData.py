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
        self.id = ""

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