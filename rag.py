import json
import numpy as np


from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# Load the knowledge base from a JSON file
with open("knowledge_base.json", "r") as file:
    knowledge_base = json.load(file)

# print(knowledge_base)

chunks = [item["text"] for item in knowledge_base]

#print("\nCHUNKS:")

#extract the chunks from the knowledge base and print them
#for chunk in chunks:
    #  print(chunk)

#load an embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")


#Generate embeddings for the business information
chunk_embeddings = model.encode(chunks)

#print("\nNUMBER OF CHUNKS:")
#print(len(chunk_embeddings))

#print("\nFIRST CHUNK VECTOR:")
#print(chunk_embeddings[0])


# Turn retrieval into a reusable function

def retrieve(question, threshold=0.30):

    # Convert the customer's question into an embedding
    question_embedding = model.encode([question])

    # Compare the question embedding with all chunk embeddings
    similarities = cosine_similarity(
        question_embedding,
        chunk_embeddings
    )[0]

    # Find the chunk with the highest similarity score
    best_match_index = np.argmax(similarities)

    # Get the best matching item
    best_item = knowledge_base[best_match_index]

    # Get its similarity score
    score = similarities[best_match_index]

    # If the score is too low, treat it as no relevant information
    if score < threshold:
        return None, score

    return best_item, score


if __name__ == "__main__":

    test_questions = [
    "What does Virgocreativo do?",
    "Can you help us improve our CRM?",
    "Can you set up a CRM for my company?",
    "We use spreadsheets and WhatsApp and information keeps getting lost.",
    "Our business uses too many disconnected tools.",
    "Can you automate repetitive tasks?",
    "Can you connect Monday.com to our CRM?",
    "Can you integrate our different business tools?",
    "Can you build an AI agent for our company?",
    "How can AI help our operations?",
    "How much does a project cost?",
    "How do I get started with Virgocreativo?",

    # Questions the knowledge base should reject
    "What is the CEO's salary?",
    "Who won the football match yesterday?",
    "What is the weather today?",
    "Can you help me buy a car?",
    "What is the capital of France?"
]

    for question in test_questions:

        result, score = retrieve(question)

        print("\n-------------------------")
        print("QUESTION:", question)
        print("SIMILARITY SCORE:", score)

        if result is None:

            print("RETRIEVED: No relevant information")

        else:

            print("RETRIEVED CATEGORY:", result["category"])
            print("RETRIEVED TEXT:", result["text"])