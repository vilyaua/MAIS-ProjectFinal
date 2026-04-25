"""Document ingestion pipeline: PDF/MD/TXT -> chunks -> FAISS index + BM25 pickle.

Usage: python ingest.py
"""

import logging
import pickle
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import Settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ingest")


def ingest():
    settings = Settings()
    data_dir = Path(settings.data_dir)
    index_dir = Path(settings.index_dir)

    if not data_dir.exists():
        logger.error("Data directory '%s' does not exist. Add documents first.", data_dir)
        return

    # Load documents
    docs = []
    for pdf_file in data_dir.glob("*.pdf"):
        logger.info("Loading PDF: %s", pdf_file.name)
        loader = PyPDFLoader(str(pdf_file))
        docs.extend(loader.load())

    for txt_file in list(data_dir.glob("*.txt")) + list(data_dir.glob("*.md")):
        logger.info("Loading text: %s", txt_file.name)
        loader = TextLoader(str(txt_file), encoding="utf-8")
        docs.extend(loader.load())

    if not docs:
        logger.error("No documents found in '%s'. Add .pdf, .txt, or .md files.", data_dir)
        return

    logger.info("Loaded %d document pages/sections", len(docs))

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    chunks = splitter.split_documents(docs)
    logger.info("Split into %d chunks (size=%d, overlap=%d)",
                len(chunks), settings.chunk_size, settings.chunk_overlap)

    # Build FAISS index
    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key.get_secret_value(),
    )
    vectorstore = FAISS.from_documents(chunks, embeddings)

    index_dir.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(index_dir))
    logger.info("FAISS index saved to '%s'", index_dir)

    # Save chunks for BM25
    bm25_path = index_dir / "bm25_chunks.pkl"
    with open(bm25_path, "wb") as f:
        pickle.dump(chunks, f)
    logger.info("BM25 chunks saved to '%s'", bm25_path)

    logger.info("Ingestion complete: %d chunks indexed.", len(chunks))


if __name__ == "__main__":
    ingest()
