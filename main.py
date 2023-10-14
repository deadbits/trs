import os
import sys
import openai
import argparse
import tiktoken

from loguru import logger

from typing import Tuple

from rich.console import Console
from rich.markdown import Markdown
from colored import Fore, Back, Style

from trs.llm import LLM
from trs.loader import Loader
from trs.schema import Document
from trs.schema import Indicators
from trs.iocs import extract_iocs
from trs.chunker import TextSplitter
from trs.vectordb import VectorDB


vdb_dir = os.path.abspath(os.path.join(os.path.abspath('.'), 'data'))
splitter = TextSplitter(chunk_size=1024, overlap=200)
loader = Loader()
console = Console()


def url_to_doc(url: str) -> Document:
    logger.info(f'fetching url: {url}')
    doc = loader.url(url=url)

    if doc is None:
        logger.error(f'error retrieving html: {url}')
        return None
    
    doc_chunks = splitter.split(doc.text)
    vdb.add_texts(texts=doc_chunks,
        metadatas=[
            {'source': url} for _ in range(len(doc_chunks))
        ]
    )
    return doc

def process_detection(url: str) -> str:
    logger.info(f'processing url for detections: {url}')
    doc = url_to_doc(url=url)
    detections = llm.detect(doc=doc)
    return detections

def process_custom(url: str, prompt_name: str) -> str:
    logger.info(f'processing url with custom prompt: {url}')
    doc = url_to_doc(url=url)
    custom = llm.custom(prompt_name=prompt_name, doc=doc)
    return custom

def process_summary(url: str) -> Tuple[str, str, Indicators]:
    logger.info(f'processing url for summarization: {url}')
    doc = url_to_doc(url=url)

    summ = llm.summarize(doc=doc)

    vdb.add_texts(texts=[summ.summary], 
        metadatas=[
            {
                'orig-source': url,
                'type': 'summary'
            }
        ]
    )

    mindmap = llm.mindmap(doc=doc)

    logger.info('Extracting indicators')
    iocs = extract_iocs(doc.text)

    return summ.summary, mindmap, iocs


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='trs-cli',
        description='Chat with and summarize CTI reports'
    )

    parser.add_argument(
        '-c', '--chat',
        required=True,
        action='store_true',
        help='Enter chat mode'
    )

    args = parser.parse_args()

    OPENAI_KEY = os.environ.get('OPENAI_API_KEY')
    if OPENAI_KEY is None:
        logger.error('OPENAI_API_KEY environment variable not set')
        sys.exit(1)

    llm = LLM(openai_api_key=OPENAI_KEY)

    vdb = VectorDB(
        collection_name='trs',
        db_dir=vdb_dir,
        n_results=3,
        openai_key=OPENAI_KEY
    )

    if args.chat:
        print(f'{Style.BOLD}{Fore.cyan_3}commands:{Style.reset}')
        print(f'* {Fore.cyan_3}!summ <url>{Style.reset} - summarize a threat report')
        print(f'* {Fore.cyan_3}!detect <url>{Style.reset} - identify detections in report')
        print(f'* {Fore.cyan_3}!custom <prompt_name> <url>{Style.reset} - process URL with a custom prompt')
        print(f'* {Fore.cyan_3}!exit|!quit{Style.reset} - exit application')

        print(f'{Style.BOLD}{Fore.dark_orange_3b}ready to chat!{Style.reset}\n')

        try:
            while True:
                prompt = input('💀 >> ')

                if prompt.lower() in ['!exit', '!quit', '!q', '!x']:
                    logger.info('exiting')
                    break

                elif prompt.lower().startswith('!custom'):
                    print('processing custom prompt ...')

                    try:
                        prompt_name = prompt.split(' ')[1].strip()
                        url = prompt.split(' ')[2].strip()
                        response = process_custom(url=url, prompt_name=prompt_name)
                        print('🤖 >>')
                        console.print(Markdown(response))
                    except Exception as err:
                        logger.error(f'error processing custom prompt: {err}')
                        pass

                    continue

                elif prompt.lower().startswith('!summ'):
                    print('processing url ...')

                    try:
                        url = prompt.split('!summ ')[1].strip()
                        summ, mindmap, iocs = process_summary(url=url)
                        print('🤖 >>')
                        console.print(Markdown(summ))
                        print(mindmap)
                        print(iocs)
                    except Exception as err:
                        logger.error(f'error processing url: {err}')
                        pass

                    continue
            
                elif prompt.lower().startswith('!detect'):
                    print('identifying detection use cases ...')
                    
                    try:
                        url = prompt.split('!detect ')[1].strip()
                        detections = process_detection(url=url)
                        print('🤖 >>')
                        console.print(Markdown(detections))
                    except Exception as err:
                        logger.error(f'error processing url: {err}')
                        pass

                    continue

                else:
                    response = vdb.query(prompt)
                    texts = '\n'.join([item['text'] for item in response])

                    # uncomment at your own log-based peril. this can be a lot of messy text.
                    # logger.debug(f'texts: {texts}')
                    
                    qna_answer = llm.qna(question=prompt, docs=texts)
                    print('🤖 >>')
                    console.print(Markdown(qna_answer))

        except KeyboardInterrupt:
            logger.info('caught keyboard interrupt, exiting')
            sys.exit(0)
        
        except Exception as err:
            logger.error(f'error: {err}')
            sys.exit(1)

    elif args.url:
        summary, mindmap, iocs = process_url(url=args.url)
        print(Markdown(summary))
        print(Markdown(mindmap))
        print(iocs)

