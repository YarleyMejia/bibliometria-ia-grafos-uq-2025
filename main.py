# app/main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Form
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import subprocess, shlex, uuid, os
from pathlib import Path
from datetime import datetime
from typing import List, Optional

app = FastAPI(title="Mini Job Runner UI")

# Templates & static
TEMPLATES_DIR = Path("templates")
STATIC_DIR = Path("static")
TEMPLATES_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Carpeta donde se guardan resultados y logs (montar volume /data en Railway)
BASE_DIR = Path(os.environ.get("OUT_BASE", "/data"))
BASE_DIR.mkdir(parents=True, exist_ok=True)

# Whitelist scripts (asegura que no puedan ejecutar cualquier cosa)
SCRIPTS = {
    "similarity": "main_similarity.py",
    "terminos": "main_terminos_es.py",
    "cluster": "main_cluster.py",
    "req5": "main_req5.py",
}

# reutilizable: ejecutar script en background
def _spawn_task(script_key: str, args: Optional[List[str]] = None):
    if script_key not in SCRIPTS:
        raise ValueError("Script no permitido.")
    script_name = SCRIPTS[script_key]
    task_id = str(uuid.uuid4())[:8]
    out_dir = BASE_DIR / task_id
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "run.log"
    cmd = f"python3 scripts/{script_name} " + " ".join(shlex.quote(a) for a in (args or []))
    # Background function
    def _run():
        with open(log_path, "w", encoding="utf-8") as lf:
            lf.write(f"Inicio: {datetime.utcnow().isoformat()}\nComando: {cmd}\n\n")
            lf.flush()
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in proc.stdout:
                lf.write(line)
                lf.flush()
            proc.wait()
            lf.write(f"\nFinalizado con código {proc.returncode}\n")
    # run in separate process via background thread (FastAPI BackgroundTasks will schedule it)
    return task_id, _run

# API Endpoints (machine friendly)
class RunReq(BaseModel):
    script: str
    args: Optional[List[str]] = None

@app.post("/api/run")
def api_run(req: RunReq, bg: BackgroundTasks):
    if req.script not in SCRIPTS:
        raise HTTPException(400, "Script no permitido")
    task_id, runner = _spawn_task(req.script, req.args)
    bg.add_task(runner)
    return {"task_id": task_id, "log_url": f"/logs/{task_id}", "files_url": f"/files/{task_id}"}

@app.get("/api/files/{task_id}")
def api_list_files(task_id: str):
    task_dir = BASE_DIR / task_id
    if not task_dir.exists(): raise HTTPException(404, "Tarea no encontrada")
    files = [str(p.relative_to(task_dir)) for p in task_dir.rglob("*") if p.is_file()]
    return {"task_id": task_id, "files": files}

@app.get("/api/logs/{task_id}")
def api_get_log(task_id: str):
    p = BASE_DIR / task_id / "run.log"
    if not p.exists(): raise HTTPException(404, "Log no encontrado")
    return FileResponse(p)

# UI Endpoints (web)
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    # list existing tasks (folders) sorted newest first
    tasks = []
    for p in sorted(BASE_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if p.is_dir():
            tasks.append({
                "id": p.name,
                "mtime": datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
                "files": [str(f.relative_to(p)) for f in p.rglob("*") if f.is_file()]
            })
    return templates.TemplateResponse("index.html", {"request": request, "scripts": SCRIPTS, "tasks": tasks})

@app.post("/run", response_class=HTMLResponse)
def run_form(request: Request, bg: BackgroundTasks, script: str = Form(...), args: str = Form("")):
    # args: string con argumentos separados por espacios (opcional)
    if script not in SCRIPTS:
        return templates.TemplateResponse("index.html", {"request": request, "error": "Script no permitido", "scripts": SCRIPTS, "tasks": []})
    arg_list = args.split() if args.strip() else []
    task_id, runner = _spawn_task(script, arg_list)
    bg.add_task(runner)
    # Redirect to task page
    return RedirectResponse(url=f"/task/{task_id}", status_code=303)

@app.get("/task/{task_id}", response_class=HTMLResponse)
def task_view(request: Request, task_id: str):
    task_dir = BASE_DIR / task_id
    if not task_dir.exists():
        raise HTTPException(404, "Tarea no encontrada")
    files = [p for p in sorted(task_dir.rglob("*"), key=lambda x: x.name) if p.is_file()]
    # read tail of log (last 5000 chars)
    log_path = task_dir / "run.log"
    log_text = ""
    if log_path.exists():
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                data = f.read()
                log_text = data[-5000:]
        except Exception:
            log_text = "(no se puede leer el log todavía)"
    return templates.TemplateResponse("task.html", {"request": request, "task_id": task_id, "files": files, "log": log_text})

@app.get("/download/{task_id}/{file_path:path}")
def download_file(task_id: str, file_path: str):
    p = BASE_DIR / task_id / file_path
    if not p.exists():
        raise HTTPException(404, "Archivo no encontrado")
    return FileResponse(p, filename=p.name)
