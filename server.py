import json
import os
import queue
import shutil  # Add this import at the beginning of your file
from pathlib import Path
from typing import Optional

import agentops
from asciitree import LeftAligned
from asciitree.drawing import BOX_LIGHT, BoxStyle
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from watchdog.observers import Observer

from src.loader import get_dir_summaries
from src.tree_generator import create_file_tree
from src.watch_utils import Handler
from src.watch_utils import create_file_tree as create_watch_file_tree

load_dotenv()

# Initialize AgentOps only if explicitly enabled and API key is available
AGENTOPS_ENABLED = False
if os.environ.get("AGENTOPS_ENABLED", "false").lower() == "true" and os.environ.get("AGENTOPS_API_KEY"):
    try:
        agentops.init(tags=["llama-fs"], auto_start_session=False)
        AGENTOPS_ENABLED = True
        print("AgentOps tracking enabled")
    except Exception as e:
        print(f"AgentOps initialization failed: {e}")
        print("Continuing without AgentOps tracking...")
        AGENTOPS_ENABLED = False
else:
    print("AgentOps tracking disabled (not enabled in settings)")


class Request(BaseModel):
    path: Optional[str] = None
    instruction: Optional[str] = None
    incognito: Optional[bool] = False
    llm_provider: Optional[str] = None  # "local" or "groq"


class CommitRequest(BaseModel):
    base_path: str
    src_path: str  # Relative to base_path
    dst_path: str  # Relative to base_path


app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Or restrict to ['POST', 'GET', etc.]
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/llm-config")
async def get_llm_config():
    return {
        "current_provider": os.environ.get("LLM_PROVIDER", "local"),
        "local_llm_base_url": os.environ.get("LOCAL_LLM_BASE_URL", "http://127.0.0.1:1234"),
        "groq_configured": bool(os.environ.get("GROQ_API_KEY"))
    }


@app.get("/agentops-config")
async def get_agentops_config():
    return {
        "agentops_enabled": os.environ.get("AGENTOPS_ENABLED", "false").lower() == "true",
        "agentops_configured": bool(os.environ.get("AGENTOPS_API_KEY"))
    }


class LLMConfigRequest(BaseModel):
    provider: str  # "local" or "groq"
    local_llm_base_url: Optional[str] = None


@app.post("/llm-config")
async def set_llm_config(config: LLMConfigRequest):
    os.environ["LLM_PROVIDER"] = config.provider
    
    if config.local_llm_base_url:
        os.environ["LOCAL_LLM_BASE_URL"] = config.local_llm_base_url
    
    return {"message": "LLM configuration updated", "provider": config.provider}


class AgentOpsConfigRequest(BaseModel):
    enabled: bool


@app.post("/agentops-config")
async def set_agentops_config(config: AgentOpsConfigRequest):
    global AGENTOPS_ENABLED
    
    os.environ["AGENTOPS_ENABLED"] = "true" if config.enabled else "false"
    
    # Note: AgentOps initialization requires server restart to take effect
    # We update the environment variable for future sessions
    return {
        "message": "AgentOps configuration updated (restart server for changes to take effect)",
        "enabled": config.enabled,
        "restart_required": True
    }


@app.post("/batch")
async def batch(request: Request):
    session = None
    if AGENTOPS_ENABLED:
        session = agentops.start_session(tags=["LlamaFS"])

    path = request.path
    if not os.path.exists(path):
        raise HTTPException(status_code=400, detail="Path does not exist in filesystem")
    
    # Set LLM provider for this request (temporarily override environment)
    original_provider = os.environ.get("LLM_PROVIDER")
    if request.llm_provider:
        os.environ["LLM_PROVIDER"] = request.llm_provider

    try:
        summaries = await get_dir_summaries(path)
        # Get file tree
        files = create_file_tree(summaries, session)
    finally:
        # Restore original provider
        if original_provider:
            os.environ["LLM_PROVIDER"] = original_provider
        elif request.llm_provider:
            # Remove the temporary override
            os.environ.pop("LLM_PROVIDER", None)

    # Recursively create dictionary from file paths
    tree = {}
    for file in files:
        parts = Path(file["dst_path"]).parts
        current = tree
        for part in parts:
            current = current.setdefault(part, {})

    tree = {path: tree}

    tr = LeftAligned(draw=BoxStyle(gfx=BOX_LIGHT, horiz_len=1))
    print(tr(tree))

    # Prepend base path to dst_path
    for file in files:
        # file["dst_path"] = os.path.join(path, file["dst_path"])
        file["summary"] = summaries[files.index(file)]["summary"]

    if AGENTOPS_ENABLED and session:
        agentops.end_session(
            "Success", end_state_reason="Reorganized directory structure"
        )
    return files


@app.post("/watch")
async def watch(request: Request):
    path = request.path
    if not os.path.exists(path):
        raise HTTPException(status_code=400, detail="Path does not exist in filesystem")

    response_queue = queue.Queue()

    observer = Observer()
    event_handler = Handler(path, create_watch_file_tree, response_queue)
    await event_handler.set_summaries()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    # background_tasks.add_task(observer.start)

    def stream():
        while True:
            response = response_queue.get()
            yield json.dumps(response) + "\n"
            # yield json.dumps({"status": "watching"}) + "\n"
            # time.sleep(5)

    return StreamingResponse(stream())


@app.post("/commit")
async def commit(request: CommitRequest):
    print("*" * 80)
    print(request)
    print(request.base_path)
    print(request.src_path)
    print(request.dst_path)
    print("*" * 80)

    src = os.path.join(request.base_path, request.src_path)
    dst = os.path.join(request.base_path, request.dst_path)

    if not os.path.exists(src):
        raise HTTPException(
            status_code=400, detail="Source path does not exist in filesystem"
        )

    # Ensure the destination directory exists
    dst_directory = os.path.dirname(dst)
    os.makedirs(dst_directory, exist_ok=True)

    try:
        # If src is a file and dst is a directory, move the file into dst with the original filename.
        if os.path.isfile(src) and os.path.isdir(dst):
            shutil.move(src, os.path.join(dst, os.path.basename(src)))
        else:
            shutil.move(src, dst)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An error occurred while moving the resource: {e}"
        )

    return {"message": "Commit successful"}
