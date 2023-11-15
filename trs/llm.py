import os
import openai
import tiktoken
from loguru import logger
from .schema import Document, Summary
from typing import Optional


PROMPT_DIR = os.path.abspath(os.path.join(os.path.abspath('.'), 'prompts'))


class LLM:
    def __init__(self, openai_api_key: str) -> None:
        openai.api_key = openai_api_key
        self.model = 'gpt-4-1106-preview'
        self.encoding_name = 'cl100k_base'
        self.token_limit = 128000

        try:
            openai.Model.list()
        except Exception as err:
            logger.error(f'Error connecting to OpenAI: {err}')
            raise

    def num_tokens(self, text: str) -> int:
        try:
            encoding = tiktoken.get_encoding(self.encoding_name)
            return len(encoding.encode(text))
        except Exception as err:
            logger.error(f'Error retrieving encoding: {err}')
            return 0
    
    def _read_prompt(self, prompt_name: str) -> Optional[str]:
        path = os.path.join(PROMPT_DIR, f'{prompt_name}.txt')
        if os.path.exists(path):
            with open(path, 'r') as f:
                return f.read()
        logger.error(f'Prompt not found: {path}')
        return None

    def _call_openai(self, user_prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        system_prompt = system_prompt or 'You are a helpful AI cybersecurity assistant.'
        
        token_counts = [self.num_tokens(p) for p in [user_prompt, system_prompt]]
        if 0 in token_counts:
            logger.warn('Failed to get token count for prompts')
            return None

        if sum(token_counts) > self.token_limit:
            logger.error(f'Token limit exceeded: limit {self.token_limit}, used {sum(token_counts)}')
            return None

        try:
            params = {
                'model': self.model,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ]
            }
            response = openai.ChatCompletion.create(**params)
            return response.choices[0].message['content']
        except Exception as err:
            logger.error(f'Error calling OpenAI: {err}')
            return None

    def _generic_prompt(self, prompt_name: str, doc: Document) -> Optional[str]:
        template = self._read_prompt(prompt_name)
        if template:
            return self._call_openai(user_prompt=template.format(document=doc.text))
        return None

    def mindmap(self, doc: Document) -> Optional[str]:
        return self._generic_prompt('mindmap', doc)

    def summarize(self, doc: Document) -> Optional[Summary]:
        summary = self._generic_prompt('summary', doc)
        if summary:
            return Summary(source=doc.source, summary=summary)
        return None

    def detect(self, doc: Document) -> Optional[str]:
        return self._generic_prompt('detect', doc)
    
    def qna(self, question: str, docs: str) -> Optional[str]:
        template = self._read_prompt('qna')
        if template:
            return self._call_openai(user_prompt=template.format(question=question, documents=docs))
        return None

    def custom(self, prompt_name: str, doc: Document) -> Optional[str]:
        return self._generic_prompt(prompt_name, doc)
