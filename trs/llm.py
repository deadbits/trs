import openai
import tiktoken

from loguru import logger

from .schema import Document, Summary


from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Dict, List


class Document(BaseModel):
    text: str
    source: str
    metadata: Optional[Dict[str, str]] = Field(
        None,
        description="Optional metadata for the document"
    )


class Summary(BaseModel):
    summary: str
    source: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, str]] = Field(
        None,
        description="Optional metadata for the document"
    )


intel_summary_prompt = open('prompts/summary.txt', 'r').read()
mindmap_prompt_template = open('prompts/mindmap.txt', 'r').read()


class Summarizer:
    def __init__(self, openai_api_key: str) -> None:
        openai.api_key = openai_api_key
        self.encoding_name = 'cl100k_base'
        self.token_limit = 8192

        try:
            openai.Model.list()
        except Exception as err:
            logger.error(f'error connecting to openai: {err}')
            raise err

    def num_tokens(self, text: str) -> int:
        try:
            encoding = tiktoken.get_encoding(self.encoding_name)
            return len(encoding.encode(text))
        except Exception as err:
            logger.error(f'error retrieving encoding: {err}')
            return 0

    def call_openai(self, prompt: str) -> str:
        num_tokens = self.num_tokens(prompt)
        if num_tokens > self.token_limit:
            logger.error(f'(error) token limit exceeded (limit: {self.token_limit}, tokens: {num_tokens})')
            return None

        logger.info(f'token count: {num_tokens}')

        try:
            response = openai.ChatCompletion.create(
              model='gpt-4',
              messages=[
                    {
                        'role': 'system',
                        'content': 'You are a helpful AI cybersecurity assistant.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )
            return response.choices[0].message['content']
        except Exception as err:
            logger.error(f'error summarizing text: {err}')
            return None

    def mindmap(self, doc: Document) -> str:
        logger.info('creating mindmap')
        prompt = mindmap_prompt_template.format(document=doc.text)
        return self.call_openai(prompt=prompt)

    def summarize(self, doc: Document) -> str:
        logger.info('summarizing text')
        prompt = intel_summary_prompt.format(document=doc.text)
        summary = self.call_openai(prompt=prompt)
        return Summary(source=doc.source, summary=summary)
