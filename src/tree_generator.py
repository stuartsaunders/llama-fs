import json
import os

import ollama
from groq import Groq

FILE_PROMPT = """
You will be provided with list of source files and a summary of their contents. For each file, propose a new path and filename, using a directory structure that optimally organizes the files using known conventions and best practices.
Follow good naming conventions. Here are a few guidelines
- Think about your files : What related files are you working with?
- Identify metadata (for example, date, sample, experiment) : What information is needed to easily locate a specific file?
- Abbreviate or encode metadata
- Use versioning : Are you maintaining different versions of the same file?
- Think about how you will search for your files : What comes first?
- Deliberately separate metadata elements : Avoid spaces or special characters in your file names
If the file is already named well or matches a known convention, set the destination path to the same as the source path.

Your response must be a JSON object with the following schema:
```json
{
    "files": [
        {
            "src_path": "original file path",
            "dst_path": "new file path under proposed directory structure with proposed file name"
        }
    ]
}
```
""".strip()


def create_file_tree(summaries: list, session):
    llm_provider = os.environ.get("LLM_PROVIDER", "local").lower()

    if llm_provider == "groq":
        # Use Groq
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": FILE_PROMPT},
                {"role": "user", "content": json.dumps(summaries)},
            ],
            model="llama-3.1-70b-versatile",
            response_format={"type": "json_object"},
            temperature=0,
        )
        file_tree = json.loads(chat_completion.choices[0].message.content)["files"]
    else:
        # Use local LLM API (Ollama, LM Studio, etc.)
        local_llm_base_url = os.environ.get("LOCAL_LLM_BASE_URL", "http://127.0.0.1:1234")

        client = ollama.Client(host=local_llm_base_url)

        response = client.chat(
            model="",  # Let the local API use its default model
            messages=[
                {"role": "system", "content": FILE_PROMPT},
                {"role": "user", "content": json.dumps(summaries)},
            ],
            format="json",
            options={"temperature": 0},
        )

        file_tree = json.loads(response["message"]["content"])["files"]

    return file_tree
