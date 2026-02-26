from sentence_transformers import SentenceTransformer
from threading import Lock

MODEL_NAME= "all-MiniLM-L6-v2"

class EmbeddingModel:

    _instance = None
    _lock = Lock()

    def __init__(self):
        self.model=None

    def load(self):
        if self.model is None:
            self.model=SentenceTransformer(MODEL_NAME)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance=cls()
                    cls._instance.load()
        return cls._instance


def embed_text(text:str):
    model= EmbeddingModel.get_instance()
    return model.model.encode(text).tolist()