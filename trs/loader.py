import os
import PyPDF2

from typing import List

from loguru import logger

from unstructured.partition.html import partition_html

from .schema import Document


class Loader:
    def url(self, url: str) -> Document:
        """Retrieve a URL and return a Document containing the text"""
        logger.info(f'loading url: {url}')

        try:
            elements = partition_html(url=url)
        except Exception as err:
            logger.error(f'error retrieving html: {url} - {err}')
            return None

        content = '\n'.join([elem.text for elem in elements])
        doc = Document(source=url, text=content)
        return doc   

    def pdf(self, file_path: str) -> List[Document]:
        """Parse a PDF file to text and return a list of Documents"""
        docs: List[Document] = []

        if not os.path.exists(file_path):
            logger.error(f'file {file_path} does not exist')
            return None

        with open(file_path, 'rb') as fp:
            logger.info(f'loading pdf: {file_path}')

            pdf_reader = PyPDF2.PdfReader(fp)
            num_pages = len(pdf_reader.pages)

            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                source = file_path
                doc_page = Document(
                    text=text,
                    source=source,
                    metadata={'page': page_num}
                )
                docs.append(doc_page)
        
        return docs
    
    def text(self, file_path: str) -> List[Document]:
        """Load a text file and return a list of Documents"""
        docs: List[Document] = []

        if not os.path.exists(file_path):
            logger.error(f'file {file_path} does not exist')
            return None

        with open(file_path, 'r') as fp:
            logger.info(f'loading text: {file_path}')

            text = fp.read()
            source = file_path
            doc = Document(text=text, source=source)
            docs.append(doc)
        
        return docs