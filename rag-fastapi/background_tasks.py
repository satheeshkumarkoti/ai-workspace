import os
import logging
import nltk
from openai import OpenAI
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from db import FileChunk

load_dotenv("/usercode/.env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Download NLTK sentence tokenizer data
nltk.download("punkt")
nltk.download("punkt_tab")


class EmbedProcessor:
    """
    Handles chunking and embedding of a file's content.
    Runs as a background task so it doesn't block the API response.
    """
    def __init__(self, db: Session, file_id: int, content: str):
        self.db      = db
        self.file_id = file_id
        self.content = content

    def chunk_and_embed(self):
        """
        Step 1: Split text into sentences using NLTK
        Step 2: Generate embedding for each sentence using OpenAI
        Step 3: Store each chunk + embedding in file_chunks table
        """
        try:
            # Step 1: Split into sentences
            sentences = nltk.sent_tokenize(self.content)
            logger.info(f"File {self.file_id}: {len(sentences)} sentences found.")

            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue

                # Step 2: Generate embedding
                response = client.embeddings.create(
                    input=sentence,
                    model="text-embedding-ada-002"
                )
                embedding = response.data[0].embedding

                # Step 3: Store in DB
                chunk = FileChunk(
                    file_id=self.file_id,
                    chunk_text=sentence,
                    chunk_embedding=embedding
                )
                self.db.add(chunk)

            self.db.commit()
            logger.info(f"File {self.file_id}: chunks and embeddings saved.")

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to chunk and embed file {self.file_id}: {e}")
            raise