from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"


model = SentenceTransformer(MODEL_NAME)


def create_embedding(text: str):
    """Convert text into a numerical embedding."""
    return model.encode(text)