from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import logging
import re
import os
import json
import requests

# Firebase
import firebase_admin
from firebase_admin import credentials, firestore

# RAG
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from auth import auth_routes

# ==========================================
# INIT
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("PoliXBackend")

app = Flask(__name__)

FRONTEND_DIR = os.path.join(
    os.path.dirname(BASE_DIR),
    "frontend"
)

CORS(app)

# ==========================================
# LANGUAGE DETECTION
# ==========================================
# Albanian function words and common patterns that
# reliably distinguish it from English.
ALBANIAN_MARKERS = [
    "ku ", "si ", "cfare", "çfare", "cilat", "cili", "cila",
    "jane", "eshte", "ndodhet", "ofron", "kushton", "ka ",
    "ne ", "per ", "dhe ", "te ", "me ", "nga ", "se ",
    "mund", "dua", "duhet", "kam", "keni", "jeni",
    "tarifat", "tarifa", "cmimi", "pagesa", "leke",
    "dege", "studim", "studime", "program", "universitet",
    "apliko", "aplikim", "regjistrim", "pranim",
    "telefon", "email", "adrese", "faqe", "kontakt",
]

def detect_language(text: str) -> str:
    """
    Return 'sq' for Albanian or 'en' for English.
    Strategy: count Albanian marker hits on the
    normalized text. If any are found, treat it as
    Albanian — English questions will contain none of them.
    """
    normalized = text.lower()
    for marker in ALBANIAN_MARKERS:
        if marker in normalized:
            return "sq"
    return "en"

# ==========================================
# NORMALIZE
# ==========================================
def normalize(text):

    text = text.lower().strip()

    replacements = {
        "ë": "e",
        "ç": "c",
        "ä": "a",
        "ö": "o",
        "ü": "u",
        "é": "e",
        "è": "e",
        "à": "a",
        "â": "a",
        "î": "i",
        "û": "u",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # remove extra spaces
    text = re.sub(r"\s+", " ", text)

    # remove punctuation except & (for "Software Engineering & AI")
    text = re.sub(r"[^\w\s&]", "", text)

    return text

# ==========================================
# FIREBASE
# ==========================================
try:

    if not firebase_admin._apps:

        cred = credentials.Certificate(
            "serviceAccountKey.json"
        )

        firebase_admin.initialize_app(cred)

        logger.info("Firebase initialized")

    db = firestore.client()

except Exception as e:

    logger.error(f"Firebase error: {e}")

# auth routes
app.register_blueprint(
    auth_routes,
    url_prefix="/api/auth"
)

# ==========================================
# LOAD JSON DATASET
# ==========================================
def load_dataset(path):

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ==========================================
# LOAD DATA
# ==========================================
logger.info("Loading JSON dataset...")

dataset_path = os.path.join(
    BASE_DIR,
    "polis_data.json"
)

dataset = load_dataset(dataset_path)

logger.info(f"Loaded {len(dataset)} entries")

# ==========================================
# BUILD DOCUMENTS
# ==========================================
# Each entry produces MULTIPLE indexed documents:
# one per question variant + the combined keywords doc.
# We track which answer each document maps to.
# answer_index stores the position in `dataset` so we
# can look up both answer and answer_en at query time.

documents = []
answer_indices = []   # index into dataset[]
metadata = []

for pos, item in enumerate(dataset):

    questions = item.get("questions", [])
    keywords = item.get("keywords", [])
    topic = item.get("topic", "")
    category = item.get("category", "")

    # Index each question variant separately so the
    # embedding stays focused on one phrasing at a time.
    for q in questions:
        doc = normalize(q)
        documents.append(doc)
        answer_indices.append(pos)
        metadata.append({
            "topic": topic,
            "category": category
        })

    # Also index the keyword bag as a fallback document.
    if keywords:
        keyword_doc = normalize(" ".join(keywords))
        documents.append(keyword_doc)
        answer_indices.append(pos)
        metadata.append({
            "topic": topic,
            "category": category
        })

logger.info(f"Built {len(documents)} indexed documents from {len(dataset)} entries")

# ==========================================
# EMBEDDING MODEL
# ==========================================
logger.info("Loading embedding model...")

embedding_model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# ==========================================
# CREATE EMBEDDINGS
# ==========================================
logger.info("Creating embeddings...")

embeddings = embedding_model.encode(
    documents,
    convert_to_numpy=True,
    batch_size=64,
    show_progress_bar=False
).astype("float32")

# normalize for cosine similarity via inner product
faiss.normalize_L2(embeddings)

# ==========================================
# FAISS
# ==========================================
dimension = embeddings.shape[1]

# cosine similarity via inner product on normalized vecs
index = faiss.IndexFlatIP(dimension)

index.add(embeddings)

logger.info(f"FAISS ready — {index.ntotal} vectors indexed")

# ==========================================
# SETTINGS
# ==========================================
# Lower threshold: multilingual MiniLM cosine sims
# rarely reach 0.70 even for correct matches.
SIMILARITY_THRESHOLD = 0.35

# How many candidates to retrieve before re-ranking
TOP_K = 10

OLLAMA_MODEL = "llama3.2"

# ==========================================
# KEYWORD BOOSTING
# ==========================================
CATEGORY_KEYWORDS = {
    "tuition": [
        "kushton",
        "tarife",
        "cmim",
        "price",
        "fee",
        "tuition",
        "pagese",
        "pageses",
        "leke",
        "cost"
    ],

    "programs": [
        "program",
        "dege",
        "bachelor",
        "master",
        "study",
        "studim",
        "studime",
        "ofron",
        "ofrohen",
        "integru"
    ],

    "contact": [
        "telefon",
        "email",
        "kontakt",
        "adrese",
        "website",
        "faqe",
        "postare",
        "zip",
        "postal"
    ],

    "admissions": [
        "aplikim",
        "admission",
        "pranim",
        "regjistrim",
        "apliko",
        "regjistro"
    ]
}

# ==========================================
# CATEGORY DETECTION
# ==========================================
def detect_category(normalized_question):
    """Return the best-matching category or None."""

    for category, words in CATEGORY_KEYWORDS.items():

        for word in words:

            if word in normalized_question:
                return category

    return None

# ==========================================
# RETRIEVE ANSWER
# Returns (answer_index, score) or (None, 0)
# ==========================================
def retrieve_answer(question, k=TOP_K):

    normalized_question = normalize(question)

    # detect category for boosting
    detected_category = detect_category(normalized_question)

    logger.info(f"Question (raw): {question}")
    logger.info(f"Question (normalized): {normalized_question}")
    logger.info(f"Detected category: {detected_category}")

    # embed the normalized query
    query_embedding = embedding_model.encode(
        [normalized_question],
        convert_to_numpy=True
    ).astype("float32")

    faiss.normalize_L2(query_embedding)

    # retrieve top-k candidates
    similarities, indices = index.search(query_embedding, k)

    logger.info(f"Raw top similarities: {similarities[0]}")

    # ======================================
    # RE-RANK CANDIDATES
    # ======================================
    # Deduplicate by dataset position and keep best score.
    scored = {}   # dataset_pos -> best_score

    for similarity, idx in zip(similarities[0], indices[0]):

        if idx < 0 or idx >= len(answer_indices):
            continue

        dataset_pos = answer_indices[idx]
        item_category = metadata[idx]["category"]
        score = float(similarity)

        # category bonus — small and capped so it
        # doesn't override a clearly better match
        if detected_category and detected_category == item_category:
            score = min(score + 0.06, 0.99)

        if dataset_pos not in scored or score > scored[dataset_pos]:
            scored[dataset_pos] = score

        logger.info(
            f"  idx={idx} score={score:.4f} cat={item_category} | {documents[idx][:60]}"
        )

    if not scored:
        return None, 0.0

    best_pos, best_score = max(scored.items(), key=lambda x: x[1])

    logger.info(f"Best score: {best_score:.4f}")

    if best_score < SIMILARITY_THRESHOLD:
        logger.info("No relevant match found (below threshold)")
        return None, 0.0

    return best_pos, best_score

# ==========================================
# CLEAN OUTPUT
# ==========================================
def clean_answer(text):

    if not text:
        return ""

    text = text.strip()

    # remove separators
    text = text.replace("-----------------------------------", "")

    # collapse whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()

# ==========================================
# OLLAMA FALLBACK
# ==========================================
def ask_ai(question):

    # Detect the language of the incoming question
    lang = detect_language(question)
    logger.info(f"Detected language: {lang}")

    # ======================================
    # FIRST: DIRECT RETRIEVAL
    # ======================================
    best_pos, best_score = retrieve_answer(question)

    if best_pos is not None:
        entry = dataset[best_pos]

        if lang == "en":
            # Prefer the English answer; fall back to Albanian
            # if answer_en is missing (shouldn't happen with
            # the updated dataset but safe to guard).
            raw = entry.get("answer_en") or entry.get("answer", "")
        else:
            raw = entry.get("answer", "")

        return clean_answer(raw)

    # ======================================
    # FALLBACK: LOCAL LLM
    # ======================================
    if lang == "en":
        prompt = f"""You are the virtual assistant of POLIS University in Tirana, Albania.

If you do not have accurate information about the question,
reply only with: "I don't have information about that."

Question: {question}

Reply:
- only in English
- briefly and clearly
- do not invent information"""
    else:
        prompt = f"""Ti je asistenti virtual i Universitetit POLIS ne Tirane, Shqiperi.

Nese nuk ke informacion te sakte per pyetjen,
thuaj vetem: "Nuk kam informacion per kete pyetje."

Pyetja: {question}

Pergjigju:
- vetem ne shqip
- shkurt dhe qarte
- pa shpikur informacione"""

    try:

        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 120
                }
            },
            timeout=20
        )

        if response.status_code != 200:
            logger.error(f"Ollama HTTP {response.status_code}: {response.text}")
            fallback = "I don't have information about that." if lang == "en" \
                       else "Nuk kam informacion per kete pyetje."
            return fallback

        data = response.json()
        answer = data.get("response", "")
        cleaned = clean_answer(answer)

        if not cleaned:
            return "I don't have information about that." if lang == "en" \
                   else "Nuk kam informacion per kete pyetje."

        return cleaned

    except requests.exceptions.Timeout:
        logger.error("Ollama timeout")
        return "I don't have information about that." if lang == "en" \
               else "Nuk kam informacion per kete pyetje."

    except Exception as e:
        logger.error(f"Ollama error: {e}")
        return "I don't have information about that." if lang == "en" \
               else "Nuk kam informacion per kete pyetje."

# ==========================================
# ASK ROUTE
# ==========================================
@app.route("/ask", methods=["POST"])
def ask():

    try:

        data = request.get_json()

        if not data:
            return jsonify({"error": "Invalid JSON body"}), 400

        question = data.get("question", "").strip()

        if not question:
            return jsonify({"error": "Shkruaj nje pyetje"}), 400

        answer = ask_ai(question)

        return jsonify({
            "question": question,
            "answer": answer
        })

    except Exception as e:
        logger.error(f"Route error: {e}")
        return jsonify({"error": "Gabim ne server"}), 500
    

@app.route("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>")
def frontend_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)

# ==========================================
# ADMIN DATASET MANAGEMENT
# ==========================================

@app.route("/api/dataset", methods=["GET"])
def get_dataset():

    try:
        data = load_dataset(dataset_path)
        return jsonify(data)

    except Exception as e:
        logger.error(f"Dataset fetch error: {e}")
        return jsonify({
            "error": "Could not load dataset"
        }), 500


@app.route("/api/dataset/add", methods=["POST"])
def add_dataset_entry():

    try:

        new_entry = request.get_json()

        if not new_entry:
            return jsonify({
                "error": "No data provided"
            }), 400

        data = load_dataset(dataset_path)

        data.append(new_entry)

        with open(dataset_path, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                indent=2,
                ensure_ascii=False
            )

        return jsonify({
            "message": "Entry added successfully"
        })

    except Exception as e:
        logger.error(f"Add dataset entry error: {e}")

        return jsonify({
            "error": "Failed to add entry"
        }), 500


@app.route("/api/dataset/delete/<int:index>", methods=["DELETE"])
def delete_dataset_entry(index):

    try:

        data = load_dataset(dataset_path)

        if index < 0 or index >= len(data):

            return jsonify({
                "error": "Invalid index"
            }), 400

        deleted_entry = data.pop(index)

        with open(dataset_path, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                indent=2,
                ensure_ascii=False
            )

        return jsonify({
            "message": "Entry deleted successfully",
            "deleted": deleted_entry
        })

    except Exception as e:

        logger.error(f"Delete dataset entry error: {e}")

        return jsonify({
            "error": "Failed to delete entry"
        }), 500


@app.route("/api/dataset/update/<int:index>", methods=["PUT"])
def update_dataset_entry(index):

    try:

        updated_entry = request.get_json()

        if not updated_entry:

            return jsonify({
                "error": "No updated data provided"
            }), 400

        data = load_dataset(dataset_path)

        if index < 0 or index >= len(data):

            return jsonify({
                "error": "Invalid index"
            }), 400

        data[index] = updated_entry

        with open(dataset_path, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                indent=2,
                ensure_ascii=False
            )

        return jsonify({
            "message": "Entry updated successfully"
        })

    except Exception as e:

        logger.error(f"Update dataset entry error: {e}")

        return jsonify({
            "error": "Failed to update entry"
        }), 500    

# ==========================================
# USERS API
# ==========================================

@app.route("/api/users", methods=["GET"])
def get_users():

    try:

        users_ref = db.collection("users")

        docs = users_ref.stream()

        users = []

        for doc in docs:

            data = doc.to_dict()

            users.append(data)

        return jsonify(users)

    except Exception as e:

        logger.error(f"Users fetch error: {e}")

        return jsonify({
            "error": "Could not fetch users"
        }), 500

# ==========================================
# HEALTH
# ==========================================
@app.route("/health")
def health():

    return jsonify({
        "status": "OK",
        "entries": len(dataset),
        "documents_indexed": len(documents),
        "faiss_vectors": index.ntotal,
        "threshold": SIMILARITY_THRESHOLD,
        "model": OLLAMA_MODEL
    })

# ==========================================
# START
# ==========================================
if __name__ == "__main__":

    logger.info("PoliX RAG STARTED")

    app.run(
    host="0.0.0.0",
    port=5000,
    debug=True
)