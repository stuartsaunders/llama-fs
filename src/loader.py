import asyncio
import json
import os
from collections import defaultdict

import litellm
import ollama
from llama_index.core import Document, SimpleDirectoryReader
from llama_index.core.node_parser import TokenTextSplitter
from llama_index.core.schema import ImageDocument
from termcolor import colored


def extract_json_from_response(content: str, fallback_doc: dict = None) -> dict:
    """
    Extract JSON from various response formats with robust fallbacks
    """
    # Try direct JSON parse first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # Look for JSON in markdown blocks or extract from mixed content
    if "{" in content and "}" in content:
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                extracted = content[start:end]
                return json.loads(extracted)
            except json.JSONDecodeError:
                pass
    
    # Create fallback summary from raw content
    file_path = "unknown"
    if fallback_doc:
        file_path = fallback_doc.get("file_path", fallback_doc.get("file_name", "unknown"))
    
    if content.strip():
        # Clean and use raw content as summary if reasonable
        clean_content = content.replace("'file_path'", "").strip()
        # Remove Python dict artifacts
        clean_content = clean_content.replace("{'", "").replace("'}", "")
        if 10 < len(clean_content) < 500:
            summary_text = clean_content
        else:
            summary_text = "Document content processed"
    else:
        summary_text = "File content analyzed"
    
    return {
        "file_path": file_path,
        "summary": summary_text
    }

try:
    from agentops.sdk.decorators import operation
except ImportError:
    # Fallback for older versions or if decorators are not available
    def operation(name=None, version=None):
        def decorator(func):
            return func

        return decorator


@operation(name="get directory summaries")
async def get_dir_summaries(path: str):
    doc_dicts = load_documents(path)
    # metadata = process_metadata(doc_dicts)

    summaries = await get_summaries(doc_dicts)

    # Convert path to relative path
    for summary in summaries:
        summary["file_path"] = os.path.relpath(summary["file_path"], path)

    return summaries

    # [
    #     {
    #         file_path:
    #         file_name:
    #         file_size:
    #         content:
    #         summary:
    #         creation_date:
    #         last_modified_date:
    #     }
    # ]


@operation(name="load documents")
def load_documents(path: str):
    reader = SimpleDirectoryReader(
        input_dir=path,
        recursive=True,
        required_exts=[
            ".pdf",
            # ".docx",
            # ".py",
            ".txt",
            # ".md",
            ".png",
            ".jpg",
            ".jpeg",
            # ".ts",
        ],
    )
    splitter = TokenTextSplitter(chunk_size=6144)
    documents = []
    for docs in reader.iter_data():
        # By default, llama index split files into multiple "documents"
        if len(docs) > 1:
            # So we first join all the document contexts, then truncate by token count
            for d in docs:
                # Some files will not have text and need to be handled
                contents = splitter.split_text("\n".join(d.text))
                if len(contents) > 0:
                    text = contents[0]
                else:
                    text = ""
                documents.append(Document(text=text, metadata=docs[0].metadata))
        else:
            documents.append(docs[0])
    return documents


@operation(name="process_metadata")
def process_metadata(doc_dicts):
    file_seen = set()
    metadata_list = []
    for doc in doc_dicts:
        if doc["file_path"] not in file_seen:
            file_seen.add(doc["file_path"])
            metadata_list.append(doc)
    return metadata_list


async def summarize_document(doc, model=None):
    """Summarize a document using LiteLLM (supports any provider)"""
    if model is None:
        model = os.getenv("MODEL_TEXT", "groq/llama-3.3-70b-versatile")

    PROMPT = """
You will be provided with the contents of a file along with its metadata. Provide a summary of the contents. The purpose of the summary is to organize files based on their content. To this end provide a concise but informative summary. Make the summary as specific to the file as possible.

Write your response a JSON object with the following schema:

```json
{
    "file_path": "path to the file including name",
    "summary": "summary of the content"
}
```
""".strip()

    try:
        response = await litellm.acompletion(
            model=model,
            messages=[
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": json.dumps(doc)},
            ],
            temperature=0,
            max_tokens=200,
        )

        content = response.choices[0].message.content.strip()
        summary = extract_json_from_response(content, doc)

    except Exception as e:
        print(f"Error processing document: {e}")
        summary = {
            "file_path": doc.get("file_path", doc.get("file_name", "unknown")),
            "summary": f"Processing failed: {str(e)}",
        }

    try:
        # Print the filename in green
        print(colored(summary["file_path"], "green"))
        print(summary["summary"])  # Print the summary of the contents
        # Print a separator line with spacing for readability
        print("-" * 80 + "\n")
    except KeyError as e:
        print(e)
        print(summary)

    return summary


async def summarize_image_document(doc: ImageDocument, model=None):
    """Summarize an image document using LiteLLM with vision model"""
    if model is None:
        model = os.getenv("MODEL_VISION", "groq/llama-4-scout-17b-16e-instruct")

    PROMPT = """
You will be provided with an image along with its metadata. Provide a summary of the image contents. The purpose of the summary is to organize files based on their content. To this end provide a concise but informative summary. Make the summary as specific to the file as possible.

Write your response a JSON object with the following schema:

```json
{
    "file_path": "path to the file including name",
    "summary": "summary of the content"
}
```
""".strip()

    try:
        # Read image as base64 for LiteLLM
        import base64

        with open(doc.image_path, "rb") as image_file:
            image_data = image_file.read()

        # Check if image is too large for Groq (4MB base64 limit)
        if len(image_data) > 4 * 1024 * 1024:  # 4MB limit
            print(
                f"Warning: Image {doc.image_path} is too large ({len(image_data) / 1024 / 1024:.1f}MB)"
            )
            print(
                "Groq vision models have a 4MB limit. Consider resizing the image or using a different model."
            )

        base64_image = base64.b64encode(image_data).decode("utf-8")

        response = await litellm.acompletion(
            model=model,
            messages=[
                {"role": "system", "content": PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Summarize the contents of this image.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                },
            ],
            temperature=0,
            max_tokens=200,
        )

        content = response.choices[0].message.content.strip()

        summary = extract_json_from_response(content, {"file_path": doc.image_path})
    except Exception as e:
        print(f"Error processing image: {e}")
        # Fallback to direct Ollama for vision if LiteLLM fails
        try:
            client = ollama.AsyncClient()
            chat_completion = await client.chat(
                messages=[
                    {
                        "role": "user",
                        "content": "Summarize the contents of this image.",
                        "images": [doc.image_path],
                    },
                ],
                model="moondream",
                options={"num_predict": 128},
            )
            summary = {
                "file_path": doc.image_path,
                "summary": chat_completion["message"]["content"],
            }
        except Exception as fallback_error:
            print(f"Fallback error: {fallback_error}")
            summary = {
                "file_path": doc.image_path,
                "summary": f"Image processing failed: {str(e)}",
            }

    # Print the filename in green
    print(colored(summary["file_path"], "green"))
    print(summary["summary"])  # Print the summary of the contents
    # Print a separator line with spacing for readability
    print("-" * 80 + "\n")
    return summary


async def dispatch_summarize_document(doc):
    """Route document to appropriate summarization function"""
    if isinstance(doc, ImageDocument):
        return await summarize_image_document(doc)
    elif isinstance(doc, Document):
        return await summarize_document({"content": doc.text, **doc.metadata})
    else:
        raise ValueError("Document type not supported")


async def get_summaries(documents):
    """Process documents to generate summaries using LiteLLM"""
    summaries = await asyncio.gather(
        *[dispatch_summarize_document(doc) for doc in documents]
    )
    return summaries


@operation(name="merge")
def merge_summary_documents(summaries, metadata_list):
    list_summaries = defaultdict(list)

    for item in summaries:
        list_summaries[item["file_path"]].append(item["summary"])

    file_summaries = {
        path: ". ".join(summaries) for path, summaries in list_summaries.items()
    }

    file_list = [
        {"summary": file_summaries[file["file_path"]], **file} for file in metadata_list
    ]

    return file_list


################################################################################################
# Synchronous versions for single file processing                                           #
################################################################################################


def get_file_summary(path: str):
    """Get summary for a single file using LiteLLM (synchronous version)"""
    reader = SimpleDirectoryReader(input_files=[path]).iter_data()

    docs = next(reader)
    splitter = TokenTextSplitter(chunk_size=6144)
    text = splitter.split_text("\n".join([d.text for d in docs]))[0]
    doc = Document(text=text, metadata=docs[0].metadata)
    summary = dispatch_summarize_document_sync(doc)
    return summary


def dispatch_summarize_document_sync(doc):
    """Route document to appropriate synchronous summarization function"""
    if isinstance(doc, ImageDocument):
        return summarize_image_document_sync(doc)
    elif isinstance(doc, Document):
        return summarize_document_sync({"content": doc.text, **doc.metadata})
    else:
        raise ValueError("Document type not supported")


def summarize_document_sync(doc, model=None):
    """Summarize a document using LiteLLM (synchronous version)"""
    if model is None:
        model = os.getenv("MODEL_TEXT", "groq/llama-3.3-70b-versatile")

    PROMPT = """
You will be provided with the contents of a file along with its metadata. Provide a summary of the contents. The purpose of the summary is to organize files based on their content. To this end provide a concise but informative summary. Make the summary as specific to the file as possible.

Write your response a JSON object with the following schema:

```json
{
    "file_path": "path to the file including name",
    "summary": "summary of the content"
}
```
""".strip()

    try:
        response = litellm.completion(
            model=model,
            messages=[
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": json.dumps(doc)},
            ],
            temperature=0,
            max_tokens=200,
        )

        content = response.choices[0].message.content.strip()

        # Extract JSON from markdown code blocks if present
        if "```" in content and "{" in content:
            # Find the JSON content between ``` blocks or extract JSON directly
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                content = content[start:end]

        summary = json.loads(content)

    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        summary = {
            "file_path": doc.get("file_path", doc.get("file_name", "unknown")),
            "summary": "File content analyzed (JSON format error)",
        }
    except Exception as e:
        print(f"Error processing document: {e}")
        summary = {
            "file_path": doc.get("file_path", doc.get("file_name", "unknown")),
            "summary": f"Processing failed: {str(e)}",
        }

    try:
        # Print the filename in green
        print(colored(summary["file_path"], "green"))
        print(summary["summary"])  # Print the summary of the contents
        # Print a separator line with spacing for readability
        print("-" * 80 + "\n")
    except KeyError as e:
        print(e)
        print(summary)

    return summary


def summarize_image_document_sync(doc: ImageDocument, model=None):
    """Summarize an image document using LiteLLM (synchronous version)"""
    if model is None:
        model = os.getenv("MODEL_VISION", "groq/llama-4-scout-17b-16e-instruct")

    PROMPT = """
You will be provided with an image along with its metadata. Provide a summary of the image contents. The purpose of the summary is to organize files based on their content. To this end provide a concise but informative summary. Make the summary as specific to the file as possible.

Write your response a JSON object with the following schema:

```json
{
    "file_path": "path to the file including name",
    "summary": "summary of the content"
}
```
""".strip()

    try:
        # Read image as base64 for LiteLLM
        import base64

        with open(doc.image_path, "rb") as image_file:
            image_data = image_file.read()

        # Check if image is too large for Groq (4MB base64 limit)
        if len(image_data) > 4 * 1024 * 1024:  # 4MB limit
            print(
                f"Warning: Image {doc.image_path} is larger than 4MB ({len(image_data) / 1024 / 1024:.1f}MB)"
            )
            print(
                "Consider resizing the image for better performance with Groq vision models."
            )

        base64_image = base64.b64encode(image_data).decode("utf-8")

        response = litellm.completion(
            model=model,
            messages=[
                {"role": "system", "content": PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Summarize the contents of this image.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                },
            ],
            temperature=0,
            max_tokens=200,
        )

        content = response.choices[0].message.content.strip()

        summary = extract_json_from_response(content, {"file_path": doc.image_path})
    except Exception as e:
        print(f"Error processing image: {e}")
        # Fallback to direct Ollama for vision if LiteLLM fails
        try:
            client = ollama.Client()
            chat_completion = client.chat(
                messages=[
                    {
                        "role": "user",
                        "content": "Summarize the contents of this image.",
                        "images": [doc.image_path],
                    },
                ],
                model="moondream",
                options={"num_predict": 128},
            )
            summary = {
                "file_path": doc.image_path,
                "summary": chat_completion["message"]["content"],
            }
        except Exception as fallback_error:
            print(f"Fallback error: {fallback_error}")
            summary = {
                "file_path": doc.image_path,
                "summary": f"Image processing failed: {str(e)}",
            }

    # Print the filename in green
    print(colored(summary["file_path"], "green"))
    print(summary["summary"])  # Print the summary of the contents
    # Print a separator line with spacing for readability
    print("-" * 80 + "\n")

    return summary
