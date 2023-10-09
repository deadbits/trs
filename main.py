import sys
import openai
import tiktoken

from loguru import logger

from unstructured.partition.html import partition_html

from flask import Flask, request, render_template
from flask import abort, redirect, url_for

from trs.llm import Summarizer
from trs.schema import Document
# from trs.iocs import extract_iocs


app = Flask(__name__)

OPENAI_KEY = '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'


def get_page_content(url: str) -> str:
    logger.info(f'retrieving html from {url}')
    try:
        elements = partition_html(url=url)
    except Exception as err:
        logger.error(f'error retrieving html: {url} - {err}')
        return None

    content = '\n'.join([elem.text for elem in elements])
    doc = Document(source=url, text=content)
    return doc



@app.route('/report', methods=['GET'])
def report_route():
    url = request.args.get('url', '')
    if url == '':
        logger.warning('missing url; using debug default')
        url = 'https://blog.talosintelligence.com/qakbot-affiliated-actors-distribute-ransom/'

    logger.debug(f'url: {url}')
    doc = get_page_content(url=url)

    if doc is None:
        logger.error(f'error retrieving html: {url}')
        abort(500)

    summ = summarizer.summarize(doc=doc)
    mindmap = summarizer.mindmap(doc=doc)
    mindmap = mindmap.replace("```", '')

    logger.debug(f'summary: {summ.summary}')
    logger.debug(f'mindmap: {mindmap}')

    return render_template(
        'report.html',
        summary=summ.summary,
        mindmap=mindmap,
        source=summ.source
    )


if __name__ == '__main__':
    summarizer = Summarizer(openai_api_key=OPENAI_KEY)
    app.run(debug=True)
