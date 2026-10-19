from app.data.chunker import load_processed_document, create_chunks

chunks = create_chunks(load_processed_document())

keywords = [
    "convulsions",
    "dizziness",
    "emergency patient",
    "emergency child",
    "cough",
]

for chunk in chunks:
    if any(word in chunk["content"].lower() for word in keywords):
        print(
            f"ID={chunk['id']} | "
            f"Population={chunk['population']} | "
            f"Page={chunk['page']} | "
            f"Topic={chunk['topic']}"
        )
        print(chunk["content"][:160])
        print("-" * 50)
