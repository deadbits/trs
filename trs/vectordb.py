# https://github.com/deadbits/trs
import chromadb

from uuid import uuid4

from loguru import logger

from typing import List

from chromadb.config import Settings
from chromadb.utils import embedding_functions


class VectorDB:
    def __init__(self, collection_name: str, db_dir: str, n_results: int = 5, openai_key: str = None):
        self.embed_fn = embedding_functions.OpenAIEmbeddingFunction(
            api_key=openai_key,
            model_name='text-embedding-ada-002'
        )

        self.collection_name = collection_name
        self.db_dir = db_dir
        self.n_results = int(n_results)

        self.client = chromadb.PersistentClient(
            path=self.db_dir,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            ),
        )
        self.collection = self.get_or_create_collection(self.collection_name)
        logger.success('Loaded database')

    def get_or_create_collection(self, name: str):
        logger.info(f'Using collection: {name}')
        self.collection = self.client.get_or_create_collection(
            name=name,
            embedding_function=self.embed_fn,
            metadata={'hnsw:space': 'cosine'}
        )
        return self.collection

    def add_texts(self, texts: List[str], metadatas: List[dict]):
        success = False

        logger.info(f'Adding {len(texts)} texts')
        ids = [str(uuid4()) for _ in range(len(texts))]

        try:
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            success = True
        except Exception as err:
            logger.error(f'Failed to add texts to collection: {err}')

        return (success, ids)

    def add_embeddings(self, texts: List[str], embeddings: List[List], metadatas: List[dict]):
        success = False

        logger.info(f'Adding {len(texts)} embeddings')
        ids = [uuid4_str() for _ in range(len(texts))]

        try:
            self.collection.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            success = True
        except Exception as err:
            logger.error(f'Failed to add texts to collection: {err}')

        return (success, ids)

    def query(self, text: str):
        flattened = []

        logger.info(f'Querying database for: {text}')
        try:
            results = self.collection.query(
                query_texts=[text],
                n_results=self.n_results)

            logger.info(f'Found {len(results["ids"][0])} results')

            for node_id, text, metadata, distance in zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                flattened.append({
                    'id': node_id,
                    'text': text,
                    'metadata': metadata,
                    'distance': distance
                })

            return flattened

        except Exception as err:
            logger.error(f'Failed to query database: {err}')
