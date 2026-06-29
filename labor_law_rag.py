import fitz
import re
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils import embedding_functions

class LaborLawRAG:
    def __init__(self):
        self.embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.client = chromadb.PersistentClient(path="./fuehrer_data/labor_law_db")
        self.collection = self.client.get_or_create_collection(
            name="labor_law",
            embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="paraphrase-multilingual-MiniLM-L12-v2"
            )
        )

    def parse_pdf(self, pdf_bytes):
        """استخراج النصوص من PDF وتقسيمها إلى مواد"""
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        # تقسيم النص إلى مواد (حسب نظام العمل)
        articles = re.split(r'(المادة\s+[\u0600-\u06ff\d]+)', full_text)
        return articles

    def index_articles(self, articles):
        """فهرسة المواد في قاعدة المتجهات"""
        texts = []
        metadatas = []
        ids = []
        for i in range(0, len(articles)-1, 2):
            if i+1 < len(articles):
                title = articles[i].strip()
                content = articles[i+1].strip()
                texts.append(content)
                metadatas.append({"title": title})
                ids.append(f"article_{i//2}")
        self.collection.add(documents=texts, metadatas=metadatas, ids=ids)
        return len(texts)

    def search(self, query, top_k=5):
        """البحث عن المواد الأكثر صلة بالسؤال"""
        results = self.collection.query(query_texts=[query], n_results=top_k)
        return list(zip(results['documents'][0], results['metadatas'][0]))