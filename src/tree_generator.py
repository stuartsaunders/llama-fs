import json
import os
import litellm

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


def create_file_tree(summaries: list, session, model=None):
    """Generate file organization tree using LiteLLM"""
    if model is None:
        model = os.getenv("MODEL_TEXT", "groq/llama-3.3-70b-versatile")
    
    try:
        response = litellm.completion(
            model=model,
            messages=[
                {"role": "system", "content": FILE_PROMPT},
                {"role": "user", "content": json.dumps(summaries)},
            ],
            temperature=0,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content.strip()
        
        # Try to extract JSON from response
        try:
            # Try direct parse first
            parsed = json.loads(content)
        except json.JSONDecodeError:
            # Look for JSON in markdown blocks
            if "{" in content and "}" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                if start >= 0 and end > start:
                    try:
                        parsed = json.loads(content[start:end])
                    except json.JSONDecodeError:
                        parsed = None
            else:
                parsed = None
        
        if parsed and "files" in parsed:
            file_tree = parsed["files"]
        else:
            # Fallback if parsing fails
            raise json.JSONDecodeError("Could not extract files array", content, 0)
        
    except json.JSONDecodeError as e:
        print(f"JSON parse error in tree generation: {e}")
        # Fallback: keep original structure
        file_tree = [{"src_path": s["file_path"], "dst_path": s["file_path"]} for s in summaries]
    except Exception as e:
        print(f"Error generating file tree: {e}")
        # Fallback: keep original structure  
        file_tree = [{"src_path": s["file_path"], "dst_path": s["file_path"]} for s in summaries]
    
    return file_tree
