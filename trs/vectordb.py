from typing import List, Tuple, Union, Dict
from chromadb import PersistentClient, Settings
from chromadb.utils import embedding_functions
from loguru import logger

from uuid import uuid4


class VectorDB:
    def __init__(self, collection_name: str, db_dir: str, n_results: int = 5, openai_key: str = None) -> None:
        self.embed_fn = embedding_functions.OpenAIEmbeddingFunction(
            api_key=openai_key,
            model_name='text-embedding-ada-002'
        )
        self.collection_name = collection_name
        self.db_dir = db_dir
        self.n_results = n_results

        self.client: PersistentClient = PersistentClient(
            path=self.db_dir,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            ),
        )
        self.collection = self.get_or_create_collection(self.collection_name)
        logger.success('Loaded database')

    def get_or_create_collection(self, name: str) -> 'Collection':  # Assuming `Collection` is the return type
        logger.info(f'Using collection: {name}')
        self.collection = self.client.get_or_create_collection(
            name=name,
            embedding_function=self.embed_fn,
            metadata={'hnsw:space': 'cosine'}
        )
        return self.collection

    def count(self) -> int:
        return self.collection.count()

    def get(self) -> Dict[str, List[Union[str, List[float], dict]]]:
        logger.info('Getting all documents')
        return self.collection.get()

    def add_texts(self, texts: List[str], metadatas: List[dict]) -> Tuple[bool, List[str]]:
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

    def add_embeddings(self, texts: List[str], embeddings: List[List[float]], metadatas: List[dict]) -> Tuple[bool, List[str]]:
        success = False
        logger.info(f'Adding {len(texts)} embeddings')
        ids = [str(uuid4()) for _ in range(len(texts))]

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

    def query(self, text: str) -> List[dict]:
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
            return []
