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
        doc = Document(source=url, text=content)
        return doc   

