from __future__ import annotations
import asyncio
import sys
from pathlib import Path
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI(title="Python Web Bridge")
BASE_DIR = Path(__file__).resolve().parent

@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <html><body><h1>Executar script Python</h1>
    <form method="post" action="/run">
        <input name="message" value="Olá" />
        <button type="submit">Executar</button>
    </form></body></html>
    """

@app.post("/run")
async def run_script(message: str = Form(...)):
    script = BASE_DIR / "worker_script.py"
    if not script.exists():
        raise HTTPException(500, "worker_script.py not found")
    proc = await asyncio.create_subprocess_exec(
        sys.executable, str(script), message,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return JSONResponse({
        "returncode": proc.returncode,
        "stdout": stdout.decode().strip(),
        "stderr": stderr.decode().strip(),
    })

@app.get("/health")
async def health():
    return {"status": "ok"}
