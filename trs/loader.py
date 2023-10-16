import os

from typing import List

from loguru import logger

from unstructured.partition.html import partition_html

from .schema import Document


class Loader:
    def url(self, source: str) -> Document:
        """Retrieve a URL and return a Document containing the text"""
        logger.info(f'loading url: {source}')

        try:
            elements = partition_html(url=source)
        except Exception as err:
            logger.error(f'error retrieving html: {source} - {err}')
            return None

        content = '\n'.join([elem.text for elem in elements])
        doc = Document(
            source=source,
            text=content,
            metadata={'type': 'url'}
        )
        return doc   

    def pdf(self, source: str) -> Document:
        """Parse a PDF file to text and return a documents"""

        if not os.path.exists(source):
            logger.error(f'file {source} does not exist')
            return None

        texts = []
        with open(source, 'rb') as fp:
            logger.info(f'loading pdf: {source}')

            pdf_reader = PyPDF2.PdfReader(fp)
            num_pages = len(pdf_reader.pages)

            for page_num in range(num_pages):
                # this could be done better by retaining the page number
                # from the pdf so it could be used for citations
                page = pdf_reader.pages[page_num]
                texts.append(page.extract_text())

        doc = Document(
            source=source,
            text='\n'.join(texts),
            metadata={'type': 'pdf'}
        )
        return docs