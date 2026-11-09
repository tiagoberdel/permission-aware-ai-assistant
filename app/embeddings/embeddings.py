from langchain_huggingface import HuggingFaceEmbeddings

def get_embeddings(
    model_name: str = "sentence-transformers/multilingual-e5-base"
):
    return HuggingFaceEmbeddings(
        model_name=model_name,
        encode_kwargs={
            "prompt": "passage: ",
            "normalize_embeddings": True,
        },
        query_encode_kwargs={
            "prompt": "query: ",
            "normalize_embeddings": True,
        },
    )