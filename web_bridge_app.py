from __future__ import annotations

import json
import asyncio
import sys
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI(title="Python Web Bridge")
BASE_DIR = Path(__file__).resolve().parent


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return """
<!doctype html>
<html lang='pt-BR'>
<head><meta charset='utf-8'><title>Python Web Bridge</title></head>
<body>
  <h1>Executar script Python</h1>
  <form method='post' action='/run'>
    <label>Mensagem para o script:</label><br />
    <input name='message' value='Olá do navegador' style='width:320px' />
    <button type='submit'>Executar</button>
  </form>
</body>
</html>
"""


@app.post("/run")
async def run_script(message: str = Form(...)) -> JSONResponse:
    script = BASE_DIR / "worker_script.py"
    if not script.exists():
        raise HTTPException(status_code=500, detail="worker_script.py não encontrado")

    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        str(script),
        message,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    payload = {
        "returncode": proc.returncode,
        "stdout": stdout.decode().strip(),
        "stderr": stderr.decode().strip(),
    }
    return JSONResponse(payload)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
