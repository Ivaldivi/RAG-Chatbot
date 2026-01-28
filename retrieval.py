# 

import requests
from openai import OpenAI
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from pypdf import PdfReader

def ingest_context(file_paths, openai_client, max_chars=1000, overlap=200):
    """A function that reads in all the files from a list of paths. 
    It then chunks the information in each pdf and saves it to the chroma db.
    
    params: 
        file_paths (list): list containing paths to context files.
        max_chars (int): number of chars in each chunk of text. 
        overlap (int): number of chars allowed to overlap between chunks.
    """ 
    chroma_client = chromadb.Client(Settings(allow_reset=True))
    collection = chroma_client.get_or_create_collection("vashon_test")
    for file in file_paths: 
        file_name = file.split("/")[-1]
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()+"\n"
        chunks=chunk_text(text, max_chars, overlap)
        write_to_db(chunks, file_name, file, collection, openai_client)
    return collection

def chunk_text(text, max_chars=1000, overlap=200):
    """Break text block into equal-sized, overlapping chunks.

    params: 
        text (str): block of text to split
        max_chars (int): number of characters allowable for each chunk.
        overlap (int): number of chars allowed to overlap between chunks.
    returns: 
        chunks (list): list of chunks of text.
    """
    if max_chars <= overlap:
        raise ValueError("max_chars must be greater than overlap")

    chunks = []
    start = 0
    n = len(text)

    while start < n:
        end = min(n, start + max_chars)
        chunks.append(text[start:end])
        if end == n:
            break  # reached the end, avoid looping on same indices
        start = end - overlap

    return chunks

def write_to_db(chunks, file_name, file_path, collection, client): 
    """Funcion to write chunks of text to chroma db"""
    docs = [
        {
            "id": f"{file_name}_{i}",
            "text": chunk,
            "metadata": {"source": file_name, "chunk": i, "file_path": file_path},
        }
        for i, chunk in enumerate(chunks)
    ]

    emb_resp = client.embeddings.create(
        model="text-embedding-3-large",
        input=[d["text"] for d in docs],
    )

    for d, e in zip(docs, emb_resp.data):
        d["embedding"] = e.embedding

    collection.add(
        ids=[d["id"] for d in docs],
        embeddings=[d["embedding"] for d in docs],
        documents=[d["text"] for d in docs],
        metadatas=[d["metadata"] for d in docs],
    )

class Retriver:
    def __init__(self, collection, openai_client):
        self.collection = collection
        self.openai_client = openai_client

    def get_retrieval_results(self, input, k=5):
        # embed query manually (since collection already has doc embeddings)
        q_emb = self.openai_client.embeddings.create(
            model="text-embedding-3-large",
            input=[input],
        ).data[0].embedding

        results = self.collection.query(
        query_embeddings=[q_emb],
        n_results=k,
        include=["documents", "metadatas", "distances"],
        )
        combined = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            combined.append({
                "text": doc,
                "source": meta.get("source"),
                "file_path": meta.get("file_path"),
                "chunk": meta.get("chunk"),
                "score": dist,
            })

        return combined

class Generator:
    def __init__(self, openai_client,openai_model="gpt-5"):
        self.openai_model = openai_model
        self.openai_client = openai_client
        self.prompt_template = """
            You're a helpful assistant. Answer the question below. 
            If you don't know the answer, be honest and say you don't know.
            Question: {question}
            Context: {text}
        """


    def generate_response(self, retrieval_results, question):
        prompts = []
        for result in retrieval_results:
            prompt = self.prompt_template.format(text=result, question=question)
            prompts.append(prompt)
        prompts.reverse()

        response = self.openai_client.chat.completions.create(
            model=self.openai_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant trying to answer questions. "
                "Be honest about your limitations and don't be overly formal. "
                "Cite your sources."},
                {"role": "user", "content": prompts[-1]},
            ],
            temperature=0,
        )
        return response.choices[0].message.content

class Chatbot:
    def __init__(self, retriever, generator):
        self.retriver = retriever
        self.generator = generator
    
    def answer(self, question):
        retrieval_results = self.retriver.get_retrieval_results(question)
        return self.generator.generate_response(retrieval_results, question)
    

if __name__ == "__main__":
    file_paths = [
        'docs/Vashon_Washington.pdf', 
        'docs/Vashon-Maury-history.pdf'
        ]
    openai_client = OpenAI()
    collection = ingest_context(file_paths, openai_client, 1000,200)
       # Creating an instance of the Chatbot class
    retriever = Retriver(collection, openai_client)
    generator = Generator(openai_client, openai_model="gpt-4o")  # or gpt-4.1, etc.
    chatbot = Chatbot(retriever, generator)

    while True:
        user_input = input("You: ")  # Taking user input from the CLI
        print(f"User: {user_input}")
        if user_input =="Exit":
            break
        response = chatbot.answer(user_input)
        print(f"Chatbot: {response}")
