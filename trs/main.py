import os
import json
from typing import Tuple
from loguru import logger

from .llm import LLM
from .loader import Loader
from .schema import Document, Indicators
from .iocs import extract_iocs
from .chunker import TextSplitter
from .vectordb import VectorDB


class TRS:
    def __init__(self, openai_key: str):
        self.vdb_dir = os.path.abspath(
            os.path.join(os.path.abspath('.'), 'data')
        )
        self.urls_path = os.path.abspath(
            os.path.join(os.path.abspath('.'), 'data', 'urls.json')
        )

        try:
            with open(self.urls_path, 'r') as fp:
                data = fp.read()
                if data:
                    self.previous_urls = set(json.loads(data))
                else:
                    self.previous_urls = set()
        except FileNotFoundError:
            self.previous_urls = set()

        self.splitter = TextSplitter(chunk_size=1024, overlap=200)
        self.loader = Loader()
        self.llm = LLM(openai_api_key=openai_key)
        self.vdb = VectorDB(
            collection_name='trs',
            db_dir=self.vdb_dir,
            n_results=3,
            openai_key=openai_key
        )
    
    def save_processed_urls(self) -> None:
        logger.info('saving processed URLs')
        try:
            with open(self.urls_path, 'w') as fp:
                json.dump(list(self.previous_urls), fp)
        except Exception as err:
            logger.error(f'Error saving processed URLs: {err}')

    def process_document(self, source: str, load_func) -> Document:
        logger.info(f'processing: {source}')
        doc = load_func(source=source)
        if doc is None:
            logger.error(f'Error retrieving Document: {source}')
            return None

        if source not in self.previous_urls:
            doc_chunks = self.splitter.split(doc.text)
            self.vdb.add_texts(
                texts=doc_chunks,
                metadatas=[{'source': source} for _ in range(len(doc_chunks))]
            )
            self.previous_urls.add(source)
            self.save_processed_urls()
        else:
            logger.info(f'Source already processed; skipping db insert: {source}')

        return doc

    def pdf_to_doc(self, file_path: str) -> Document:
        return self.process_document(file_path, self.loader.pdf)

    def url_to_doc(self, url: str) -> Document:
        return self.process_document(url, self.loader.url)
    
    def qna(self, prompt: str) -> str:
        logger.info(f'processing: {prompt}')
        response = self.vdb.query(prompt)
        texts = '\n'.join([item['text'] for item in response])
        qna_answer = self.llm.qna(question=prompt, docs=texts)
        return qna_answer

    def detections(self, url: str) -> str:
        logger.info(f'processing: {url}')
        doc = self.url_to_doc(url=url)
        detections = self.llm.detect(doc=doc)
        return detections

    def custom(self, url: str, prompt_name: str) -> str:
        logger.info(f'processing: {url}')
        doc = self.url_to_doc(url=url)
        custom = self.llm.custom(prompt_name=prompt_name, doc=doc)
        return custom

    def summarize(self, url: str) -> Tuple[str, str, Indicators]:
        logger.info(f'processing: {url}')
        doc = self.url_to_doc(url=url)

        summ = self.llm.summarize(doc=doc)

        if url not in self.previous_urls:
            # dont need to add the url to the previous
            # urls list because thats already done in the summarizer
            self.vdb.add_texts(
                texts=[summ.summary],
                metadatas=[
                    {
                        'source': url,
                        'type': 'summary'
                    }
                ]
            )

        mindmap = self.llm.mindmap(doc=doc)

        logger.info('extracting indicators')
        iocs = extract_iocs(doc.text)

        return summ.summary, mindmap, iocs
