import openai

from loguru import logger


class Embedder:
    def __init__(self, openai_key: str = None):
        openai.api_key = openai_key
        try:
            openai.Model.list()
        except Exception as err:
            logger.error(f'Failed to connect to OpenAI API: {err}')
            raise Exception(f"Connection to OpenAI API failed: {err}")

        logger.success('Loaded embedder.')
    
    def generate(self, input_text: str) -> List:
        logger.info('Generating embedding with OpenAI')

        try:
            response = openai.Embedding.create(
                input=input_text, model='text-embedding-ada-002'
            )
            data = response['data'][0]
            return data['embedding']
        except Exception as err:
            logger.error(f'Failed to generate embedding: {err}')
            return []