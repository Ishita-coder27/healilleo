from rag.vector_store import VectorStore

class RAGRetriever:
    def __init__(self):
        self.store = VectorStore()
        self.store.add("High HbA1c requires low sugar diet and regular cardio exercise.")
        self.store.add("High blood pressure requires low salt intake and daily walking.")
        self.store.add("High BMI requires calorie deficit and strength training.")

    def retrieve(self, query):
        return self.store.search(query)
