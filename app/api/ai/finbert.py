from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F
from threading import Lock


MODEL_NAME = "ProsusAI/finbert"
labels = ["negative", "neutral", "positive"]


class FinBERTModel:

    _instance = None
    _lock = Lock()

    def __init__(self):
        self.tokenizer = None
        self.model = None

    def load(self):
        """Load model only once."""
        if self.model is None:
            print("Loading FinBERT model... (first use only)")
            self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            self.model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
            self.model.eval()

    @classmethod
    def get_instance(cls):
        """Singleton access."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    cls._instance.load()
        return cls._instance


def analyze_sentiment(text: str):

    finbert = FinBERTModel.get_instance()

    inputs = finbert.tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=256
    )

    with torch.no_grad():
        outputs = finbert.model(**inputs)

    probs = F.softmax(outputs.logits, dim=1)
    score, idx = torch.max(probs, dim=1)

    return labels[idx], float(score)