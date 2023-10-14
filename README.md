# trs - threat report summarizer

## Overview
`trs` is a command line tool that leverages an LLM (OpenAI) to chat with and analyze cyber threat intelligence reports and blogs. 

Supply a threat report to pre-built commands for summarization, MITRE TTP extraction, mindmap creation, and identification of detection opportunities, or run your own custom prompts against the report content.

Each URL's text content is stored in a Chroma vector database so you can have QnA / Retrieval-Augmented-Generation (RAG) chat sessions with the processed reports.

The OpenAI model `gpt-3.5-turbo-16k` is used in order to support larger contexts more easily, but feel free to swap this out for the `gpt-4-32k` model in the config if you have access.

## Features
- **Report Summarization**: Concise summary of threat reports
- **MITRE TTP Extraction**: Extract MITRE ATT&CK tactics, techniques, and procedures.
- **IOC Extraction**: Extract IOCs via [python-iocextract](https://github.com/InQuest/iocextract)
- **Mindmap Creation**: Generate Mermaid.js mindmap representing report artifacts
- **Detection Opportunities**: Identify potential detections 
- **Custom Prompts**: Add your own prompts to apply to report content
- **Chat Mode**: Interactive Q&A with data stored in the vector db

## Installation
```
git clone https://github.com/deadbits/trs.git
cd trs
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python main.py --chat
```

Once the application starts, you'll be greeted with the message:
```
commands:
* !summ <url> - summarize a threat report
* !detect <url> - identify detections in threat report
* !custom <name> <url> - run custom prompt against URL
* !exit|!quit - exit application
ready to chat!

💀 >> _
```

### Commands
URLs provided to the `!summ`, `!detect`, and `!custom` commands go through the following workflow:
1. Retrieve URL and parse to text content only
2. Chunk the full chunks
3. Store text and their embeddings in vector database with source URL metadata
4. Send full text content with specified prompt template (the command) to OpenAI and return response

* **!summ**: generate a summary of the URL's content with a list of key takeaways, summary paragraph, MITRE TTPs, and a [Mermaid mindmap](https://mermaid.live/) representing an overview of the report
* **!detect**: identify any threat detection opportunities within the URL's content
* **!custom**: fetch the URL's content and process it with a custom prompt

#### Custom Prompts
Custom prompt templates can be saved to the `prompts/` directory as text files with the `.txt` extension. The `!custom` command will look for prompts by file basename in that directory, add the URL's text content to the template, and send it to the LLM for processing.

Custom prompts **must** include the format string `{document}` so the URL text content can be added.

### Retrieval-Augmented-Generation
Before you can use the RAG chat functionality, you first must process a URL with one of the commands above so the vector database has some context to use for your questions.

Any input that is **not** a `!command` will be processed for RAG/QnA over the data stored in the vector database.

You currently can't ask the LLM questions outside of your context. If the answer is not available in the context, you won't get an answer. This can be addressed with OpenAI's function calling models; see [Issue 3](https://github.com/deadbits/trs/issues/3).

**example**

```
💀 >> Summarize the LemurLoot malware functionality        
2023-10-14 14:51:51.140 | INFO     | trs.vectordb:query:84 - Querying database for: Summarize the LemurLoot malware functionality
2023-10-14 14:51:51.840 | INFO     | trs.vectordb:query:90 - Found 3 results
2023-10-14 14:51:51.841 | INFO     | trs.llm:qna:98 - sending qna prompt
2023-10-14 14:51:51.841 | INFO     | trs.llm:_call_openai:41 - Calling OpenAI
2023-10-14 14:51:51.854 | INFO     | trs.llm:_call_openai:59 - token count: 2443
🤖 >>
The LemurLoot malware has several functionalities. It uses the header field “X-siLock-Step1’ to receive commands from the operator, with two well-defined commands: -1 and -2.  
Command “-1” retrieves Azure system settings from MOVEit Transfer and performs SQL queries to retrieve files. Command “-2” deletes a user account with the LoginName and        
RealName set to "Health Check Service". If any other values are received, the web shell opens a specified file and retrieves it. If no values are specified, it creates the     
“Health Check Service” admin user and creates an active session.
```

## Technology Stack
- **Python**
- **OpenAI API**: LLM
- **Loguru**: Logging
- **Rich**: Better visuals
- **Chroma:** Vector database
- **Iocextract:** IOC extraction
- **LlamaIndex:** Text chunking
- **Unstructured:** URL retrieval and parsing

## Contributing
Feel free to open issues or PRs if you want to improve the app or add new functionalities.

## License
This project is licensed under the Apache 2.0 License - see the [LICENSE.md](LICENSE.md) file for details.

---

Made with ❤️ for the cybersecurity community.
