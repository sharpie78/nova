#####

import subprocess
import os, signal
from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime
import re

EditorRouter = APIRouter()

HOME = Path.home()

PROJECTS_DIR = HOME / "nova" / "vault" / "projects"

VAULT_DIR = HOME / "nova" / "vault"

class ProjectRequest(BaseModel):
    name: str

class VaultFileRequest(BaseModel):
    content: str

class SaveFileRequest(BaseModel):
    path: str
    content: str

class InjectTextRequest(BaseModel):
    path: str
    new_content: str
    mode: str = "append"  # or "replace"

ALLOWED_WRITE_ROOTS = [HOME / "nova" / "projects", HOME / "nova" / "vault"]

editor_pid = None

def is_within_allowed_roots(path: Path, for_writing: bool = False) -> bool:
    path = path.resolve()
    if for_writing:
        return any(str(path).startswith(str(root)) for root in ALLOWED_WRITE_ROOTS)
    return True  # read access is allowed anywhere

@EditorRouter.post("/ensure_folder")
def ensure_folder(path: str = Query(..., description="Folder to create if missing")):
    try:
        folder = Path(path).resolve()
        if not is_within_allowed_roots(folder, for_writing=True):
            raise HTTPException(status_code=403, detail="Permission denied")
        folder.mkdir(parents=True, exist_ok=True)
        return {"success": True, "created": str(folder)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@EditorRouter.post("/create_project")
def create_project(request: ProjectRequest):
    project_name = re.sub(r'[^\w\-]', '_', request.name.strip())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_path = PROJECTS_DIR / f"{project_name}_{timestamp}"
    file_path = folder_path / "new_project.txt"

    try:
        folder_path.mkdir(parents=True, exist_ok=False)
        file_path.write_text("")
        return {"success": True, "file_path": str(file_path)}
    except FileExistsError:
        raise HTTPException(status_code=400, detail="Project already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@EditorRouter.post("/create_vault_file")
def create_vault_file(request: VaultFileRequest):
    first_line = request.content.strip().split("\n")[0][:60]
    title = re.sub(r'[^\w\-]', '_', first_line).strip("_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{title}_{timestamp}.txt"
    file_path = VAULT_DIR / filename

    try:
        VAULT_DIR.mkdir(parents=True, exist_ok=True)
        file_path.write_text(request.content)
        return {"success": True, "file_path": str(file_path), "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@EditorRouter.post("/save_file")
def save_file(request: SaveFileRequest):
    path = Path(request.path).resolve()
    if not is_within_allowed_roots(path, for_writing=True):
        raise HTTPException(status_code=403, detail="Write access denied")
    try:
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(request.content)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@EditorRouter.get("/load_file")
def load_file(path: str):
    try:
        file_path = Path(path).resolve()
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        return {"content": file_path.read_text()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@EditorRouter.get("/list_directory")
def list_directory(folder: str):
    path = Path(folder).resolve()
    try:
        if not path.exists() or not path.is_dir():
            raise HTTPException(status_code=404, detail="Folder not found")
        return {
            "folder": str(path),
            "items": [
                {
                    "name": p.name,
                    "is_dir": p.is_dir(),
                    "path": str(p)
                }
                for p in path.iterdir()
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@EditorRouter.delete("/delete_path")
def delete_path(path: str = Query(..., description="Full path to file or folder")):
    target = Path(path).resolve()
    if not is_within_allowed_roots(target, for_writing=True):
        raise HTTPException(status_code=403, detail="Delete not allowed outside projects or vault")
    try:
        if not target.exists():
            raise HTTPException(status_code=404, detail="Path does not exist")
        if target.is_dir():
            for child in target.rglob("*"):
                if child.is_file():
                    child.unlink()
                elif child.is_dir():
                    child.rmdir()
            target.rmdir()
        else:
            target.unlink()
        return {"success": True, "deleted": str(target)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@EditorRouter.post("/inject_text")
def inject_text(request: InjectTextRequest):
    target = Path(request.path).resolve()
    if not is_within_allowed_roots(target, for_writing=True):
        raise HTTPException(status_code=403, detail="Write access denied")

    try:
        existing = target.read_text() if target.exists() else ""
        content = (
            request.new_content if request.mode == "replace"
            else existing + request.new_content
        )
        target.write_text(content)
        return {"success": True, "updated_content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Use this version for deploying app
@EditorRouter.post("/launch_editor")
def launch_editor():
    global editor_pid
    appimage = Path.home() / "nova" / "frontend" / "nova-editor.AppImage"
    try:
        if not appimage.is_file():
            raise HTTPException(status_code=404, detail=f"AppImage not found: {appimage}")

        process = subprocess.Popen(
            [str(appimage)],
            cwd=str(appimage.parent),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        editor_pid = process.pid
        return JSONResponse(content={"status": "launched", "pid": editor_pid, "path": str(appimage)})
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# Use this version when developing app
#@EditorRouter.post("/launch_editor")
#def launch_editor():
#    global editor_pid
#    try:
#        process = subprocess.Popen(
#            ["npx", "tauri", "dev"],
#            cwd="/home/jack/nova/frontend/nova-editor",
#            stdout=subprocess.DEVNULL,
#            stderr=subprocess.DEVNULL,
#        )
#        editor_pid = process.pid
#        return JSONResponse(content={"status": "launched", "pid": editor_pid})
#    except Exception as e:
#        return JSONResponse(content={"error": str(e)}, status_code=500)

@EditorRouter.post("/close_editor")
def close_editor():
    global editor_pid
    try:
        result = subprocess.run(['wmctrl', '-l', '-x'], capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if 'nova-editor' in line.lower():
                    window_id = line.split()[0]
                    subprocess.run(['wmctrl', '-i', '-c', window_id])
                    if editor_pid:
                        os.kill(editor_pid, signal.SIGTERM)
                    editor_pid = None
                    return JSONResponse(content={"status": "closed"})
            return JSONResponse(content={"status": "not_found"})
        else:
            return JSONResponse(content={"error": "wmctrl failed"}, status_code=500)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@EditorRouter.get("/clipboard/read")
def clipboard_read():
    try:
        import pyperclip
        text = pyperclip.paste() or ""
        return {"text": text}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@EditorRouter.post("/clipboard/write")
def clipboard_write(payload: dict):
    try:
        import pyperclip
        text = payload.get("text", "") or ""
        pyperclip.copy(text)
        return {"ok": True}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
