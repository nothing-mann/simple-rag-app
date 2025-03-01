import chromadb
import os
# setup Chroma in-memory, for easy prototyping. Can add persistence easily!
client = chromadb.Client()

# Create collection. get_collection, get_or_create_collection, delete_collection also available!
collection = client.create_collection("cultural-heritage-information")

# Add docs to the collection. Can also update and delete. Row-based API coming soon!
# Directory path containing your text files
documents_dir = "/data/heritage_sites"  # Update this path
documents = []
metadatas = []
ids = []

# Read all text files in the directory
for i, filename in enumerate(os.listdir(documents_dir)):
    if filename.endswith('.txt'):
        file_path = os.path.join(documents_dir, filename)
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read().strip()
            documents.append(content)
            metadatas.append({"source": file_path})
            ids.append(f"doc{i+1}")

# Add documents to collection
collection.add(
    documents=documents,
    metadatas=metadatas,
    ids=ids,
)

# Query/search 2 most similar results. You can also .get by id
results = collection.query(
    query_texts=["This is a query document"],
    n_results=2,
    # where={"metadata_field": "is_equal_to_this"}, # optional filter
    # where_document={"$contains":"search_string"}  # optional filter
)

print(results)