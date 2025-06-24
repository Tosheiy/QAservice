import fitz  # pymupdf4llmはPyMuPDFに依存

class SourceData:
    def __init__(self, row_file, questionCount, mode, difficulty, filename):
        self.row_file = row_file
        self.questionCount = questionCount
        self.mode = mode
        self.difficulty = difficulty
        self.filename = filename
        self.texts = ""
        self.chunk_text = []

    def pdf2text(self):
        pdf = fitz.open(stream=self.row_file, filetype="pdf")
        
        for page in pdf:
            self.texts += page.get_text()
        pdf.close()

        return self.texts

    def text2chunk(self):
        length = len(self.texts)
        q_num = self.questionCount
        chunk_size = (length + q_num - 1) // q_num
        self.chunk_text = [self.texts[i * chunk_size: (i + 1) * chunk_size] for i in range(q_num)]
        
        return self.chunk_text