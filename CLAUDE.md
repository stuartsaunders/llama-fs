# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

LlamaFS is a self-organizing file manager that automatically renames and organizes files based on their content using AI. It consists of two main components in a monorepo structure:

- **Python Backend** (`/`): FastAPI server that processes files using Llama3 via Groq/Ollama
- **Electron Frontend** (`/electron-react-app/`): Desktop application providing the user interface

## Development Commands

### Python Backend

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI development server
fastapi dev server.py

# Run batch processing from command line
python main.py <source_path> <destination_path> [--auto-yes]

# Example API call for batch processing
curl -X POST http://127.0.0.1:8000/batch \
  -H "Content-Type: application/json" \
  -d '{"path": "/path/to/directory", "instruction": "string", "incognito": false}'
```

### Electron Frontend

```bash
# Navigate to electron app directory
cd electron-react-app

# Install Node.js dependencies  
npm install

# Build for production (recommended for development due to webpack issues)
npm run build

# Run built application
npx electron ./release/app/dist/main/main.js

# Package for distribution (creates .app, .dmg, .zip)
npm run package

# Lint code
npm run lint

# Run tests
npm test
```

## Architecture

### Core Processing Pipeline

1. **File Loading** (`src/loader.py`): Uses LlamaIndex to read supported file types (.pdf, .txt, .png, .jpg, .jpeg)
2. **Content Summarization**: Files are processed by Llama3 model to generate content summaries
3. **Tree Generation** (`src/tree_generator.py`): AI creates optimal directory structure based on content
4. **File Operations**: Files are moved/renamed according to the generated structure

### API Modes

- **Batch Mode** (`/batch`): Process entire directories at once
- **Watch Mode** (`/watch`): Real-time monitoring with proactive file organization based on user patterns
- **Commit Mode** (`/commit`): Execute specific file move operations

### AI Integration

- **Groq API**: Fast cloud inference using Llama-3.1-70b-versatile model
- **Ollama Integration**: Local inference for "incognito mode" using moondream for images
- **AgentOps**: Optional monitoring and session replay (gracefully degrades if unavailable)

### Frontend Architecture

The Electron app uses a main/renderer process architecture:
- **Main Process** (`electron-react-app/src/main/`): Electron lifecycle, window management, preload security
- **Renderer Process** (`electron-react-app/src/renderer/`): React UI with file browser interface
- **Communication**: Secure IPC through preload scripts

## Environment Setup

### Required Environment Variables

Create `.env` file in root directory:

```bash
GROQ_API_KEY=your_groq_api_key_here
AGENTOPS_API_KEY=your_agentops_api_key_here  # Optional
```

### Optional Setup

```bash
# For local image processing in incognito mode
ollama pull moondream
```

## Development Workflow

### Backend Development
1. Modify Python code in `src/` directory
2. Server auto-reloads with `fastapi dev server.py`
3. Test API endpoints with curl or frontend

### Frontend Development
1. Navigate to `electron-react-app/`
2. Make React/TypeScript changes
3. Run `npm run build` (development server has webpack issues)
4. Test with `npx electron ./release/app/dist/main/main.js`

### Testing Integration
1. Start backend: `fastapi dev server.py` (port 8000)
2. Build and run frontend
3. Frontend communicates with backend via HTTP API

## File Processing Details

### Supported File Types
- Documents: PDF, TXT
- Images: PNG, JPG, JPEG (processed via Moondream vision model)
- Extensible via `src/loader.py` configuration

### Content Processing
- Large files are chunked using TokenTextSplitter (6144 token chunks)
- Images use specialized vision model prompts
- Summaries focus on content-based organization rather than generic descriptions

### Directory Structure Generation
The AI follows specific conventions:
- Time-based organization for dated content
- Content-type grouping (documents, images, etc.)
- Metadata encoding in filenames
- Version control considerations
- Search-optimized naming

## Known Issues

### Electron Frontend
- Development server (`npm start`) has DLL circular dependency issues
- Use production build workflow for development
- Packaging may fail during postinstall - see troubleshooting in `electron-react-app/CLAUDE.md`

### Backend
- AgentOps integration is optional and fails gracefully
- Large directory processing may hit API rate limits
- Image processing requires Ollama setup for incognito mode