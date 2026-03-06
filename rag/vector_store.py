import faiss
import numpy as np

class VectorStore:
    def __init__(self):
        self.index = faiss.IndexFlatL2(384)
        self.texts = []

    def embed(self, text):
        return np.random.rand(384).astype("float32")

    def add(self, text):
        vector = self.embed(text)
        self.index.add(np.array([vector]))
        self.texts.append(text)

    def search(self, query):
        vector = self.embed(query)
        _, idx = self.index.search(np.array([vector]), 1)
        return self.texts[idx[0][0]]
