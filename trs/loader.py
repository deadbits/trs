import os

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
        doc = Document(
            source=url,
            text=content,
            metadata={'type': 'url'}
        )
        return doc   

    def pdf(self, file_path: str) -> Document:
        """Parse a PDF file to text and return a documents"""

        if not os.path.exists(file_path):
            logger.error(f'file {file_path} does not exist')
            return None

        texts = []
        with open(file_path, 'rb') as fp:
            logger.info(f'loading pdf: {file_path}')

            pdf_reader = PyPDF2.PdfReader(fp)
            num_pages = len(pdf_reader.pages)

            for page_num in range(num_pages):
                # this could be done better by retaining the page number
                # from the pdf so it could be used for citations
                page = pdf_reader.pages[page_num]
                texts.append(page.extract_text())

        doc = Document(
            source=file_path,
            text='\n'.join(texts),
            metadata={'type': 'pdf'}
        )
        return docs