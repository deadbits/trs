import os
import openai
import tiktoken

from loguru import logger

from .schema import Document, Summary

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Dict, List


PROMPT_DIR = os.path.abspath(os.path.join(os.path.abspath('.'), 'prompts'))


class LLM:
    def __init__(self, openai_api_key: str) -> None:
        openai.api_key = openai_api_key
        self.model = 'gpt-3.5-turbo-16k'
        self.encoding_name = 'cl100k_base'
        self.token_limit = 16385 

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
    
    def _call_openai(self, user_prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        logger.info('Calling OpenAI')

        if system_prompt is None:
            system_prompt = 'You are a helpful AI cybersecurity assistant.'

        num_tokens = 0
        up_tokens = self.num_tokens(user_prompt)
        sp_tokens = self.num_tokens(system_prompt)

        if up_tokens == 0 or sp_tokens == 0:
            logger.warn(f'(error) failed to get token count for user prompt')
            return None

        num_tokens = up_tokens + sp_tokens
        if num_tokens > self.token_limit:
            logger.error(f'(error) token limit exceeded (limit: {self.token_limit}, tokens: {num_tokens})')
            return None

        logger.info(f'token count: {num_tokens}')
        try:
            params = {
                'model': self.model,
                'messages': [
                    {
                        'role': 'system',
                        'content': system_prompt
                    },
                    {
                        'role': 'user',
                        'content': user_prompt
                    }
                ]
            }

            response = openai.ChatCompletion.create(**params)
            return response.choices[0].message['content']
        except Exception as err:
            logger.error(f'error calling openai: {err}')
            return None

    def mindmap(self, doc: Document) -> str:
        logger.info('creating mindmap')
        mindmap_prompt_template = open(PROMPT_DIR + '/mindmap.txt', 'r').read()
        prompt = mindmap_prompt_template.format(document=doc.text)
        return self._call_openai(user_prompt=prompt)

    def summarize(self, doc: Document) -> str:
        logger.info('summarizing text')
        intel_summary_prompt = open(PROMPT_DIR + '/summary.txt', 'r').read()
        prompt = intel_summary_prompt.format(document=doc.text)
        summary = self._call_openai(user_prompt=prompt)
        return Summary(source=doc.source, summary=summary)
    
    def detect(self, doc: Document) -> str:
        logger.info('identifying detections')
        detection_prompt = open(PROMPT_DIR + '/detect.txt', 'r').read()
        prompt = detection_prompt.format(document=doc.text)
        return self._call_openai(user_prompt=prompt)
    
    def qna(self, question: str, docs: str) -> str:
        logger.info('sending qna prompt')
        qna_prompt_template = open(PROMPT_DIR + '/qna.txt', 'r').read()
        prompt = qna_prompt_template.format(question=question, documents=docs)
        return self._call_openai(user_prompt=prompt)
    
    def custom(self, prompt_name: str, doc: Document) -> str:
        logger.info('building custom prompt template')
        prompt_path = os.path.join(PROMPT_DIR, prompt_name + '.txt')

        if not os.path.exists(prompt_path):
            logger.error(f'custom prompt template not found: {prompt_path}')
            return None

        custom_template = open(prompt_path).read()
        prompt = custom_template.format(document=doc.text)
        return self._call_openai(user_prompt=prompt)


