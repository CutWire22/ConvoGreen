import os
import io
import re
from datetime import datetime
from typing import Optional
import httpx
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import PyPDF2

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")

chat_history = []

profile_a = {
    "persona_name": "Model A",
    "system_prompt": "",
    "temperature": 1.0,
    "api_endpoint": "",
    "auth_key": "",
    "model_name": "",
    "rag_text": "",
}

profile_b = {
    "persona_name": "Model B",
    "system_prompt": "",
    "temperature": 1.0,
    "api_endpoint": "",
    "auth_key": "",
    "model_name": "",
    "rag_text": "",
}


class ProfileConfig(BaseModel):
    persona_name: str
    system_prompt: str
    temperature: float
    api_endpoint: str
    auth_key: str
    model_name: str
    rag_text: Optional[str] = ""


class ChatRequest(BaseModel):
    message: str
    profile_a: ProfileConfig
    profile_b: ProfileConfig


class SingleModelRequest(BaseModel):
    target: str
    message: Optional[str] = ""
    profile_a: ProfileConfig
    profile_b: ProfileConfig


def get_timestamp() -> str:
    return datetime.now().strftime("%H:%M %m/%d/%Y")


def sanitize_text_for_history(text: str) -> str:
    """Replaces massive base64 image strings with lightweight placeholders to prevent context bloat."""
    if not text:
        return ""
    # Strip base64 data URIs if they exist in text
    return re.sub(r'data:image/[^;]+;base64,[A-Za-z0-9+/=]+', '[Attached Image]', text)


def format_history_for_api(active_persona_name: str) -> list:
    result = []
    for e in chat_history:
        role = "assistant" if e["name"] == active_persona_name else "user"
        clean_text = sanitize_text_for_history(e["text"])
        result.append({
            "role": role,
            "content": f"{e['name']} Responded at {e['timestamp']}:\n{clean_text}",
        })
    return result


def build_system_prompt(profile, opposing_profile) -> str:
    base = profile["system_prompt"]
    injected = (
        f"\n\nYour active identity persona name is: {profile['persona_name']}.\n"
        f"You are engaging in a multi-turn conversation with a Human User and a secondary AI engine "
        f"whose persona name is: {opposing_profile['persona_name']}.\n"
        f"You are completely self-aware of your identity. Speak and debate exclusively as "
        f"{profile['persona_name']}, tracking the timestamps to maintain absolute temporal consistency.\n"
        f"CRITICAL ASSIGNMENT CONSTRAINT: Do not write your own name, speaker tags, or timestamps at the beginning of your response. "
        f"Do not output tags like \"{profile['persona_name']} Responded at...\". Start generating your message text immediately from the very first token. "
        f"The system harness manages headers automatically."
    )
    return base + injected


async def call_model(profile, opposing_profile) -> str:
    endpoint = profile["api_endpoint"].rstrip("/") + "/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    if profile["auth_key"]:
        headers["Authorization"] = f"Bearer {profile['auth_key']}"

    messages = [
        {"role": "system", "content": build_system_prompt(profile, opposing_profile)},
    ]
    if profile["rag_text"]:
        messages.append({
            "role": "user",
            "content": f"[SYSTEM NOTIFICATION: The user has attached the following reference document context for your verification. Review this data closely to answer subsequent prompts]:\n\n{profile['rag_text']}",
        })
    messages.extend(format_history_for_api(profile["persona_name"]))

    payload = {
        "model": profile["model_name"],
        "messages": messages,
        "temperature": profile["temperature"],
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(endpoint, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            error_body = e.response.text
            print(f"[ERROR] Inference server at {endpoint} returned HTTP {e.response.status_code}: {error_body}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Inference Server Error ({e.response.status_code}): {error_body}"
            )
        except httpx.RequestError as e:
            print(f"[ERROR] Connection failed to {endpoint}: {e}")
            raise HTTPException(
                status_code=502,
                detail=f"Could not connect to inference server at {endpoint}. Verify the model server is running."
            )


def parse_file_content(file: UploadFile) -> str:
    content = file.file.read()
    if file.filename and file.filename.lower().endswith(".pdf"):
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    return content.decode("utf-8", errors="replace")


def update_profile(target: str, config: ProfileConfig):
    global profile_a, profile_b
    p = profile_a if target == "a" else profile_b
    p["persona_name"] = config.persona_name
    p["system_prompt"] = config.system_prompt
    p["temperature"] = config.temperature
    p["api_endpoint"] = config.api_endpoint
    p["auth_key"] = config.auth_key
    p["model_name"] = config.model_name
    # Allows clearing rag_text when config.rag_text is empty or None
    p["rag_text"] = config.rag_text if config.rag_text is not None else ""


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.post("/api/profile/{target}")
async def save_profile(target: str, config: ProfileConfig):
    update_profile(target, config)
    return {"status": "ok"}


@app.post("/api/chat")
async def chat(request: ChatRequest):
    global profile_a, profile_b
    update_profile("a", request.profile_a)
    update_profile("b", request.profile_b)

    user_ts = get_timestamp()
    chat_history.append({
        "role": "user",
        "name": "User",
        "text": request.message,
        "timestamp": user_ts,
    })

    new_entries = []

    a_response = await call_model(profile_a, profile_b)
    ts_a = get_timestamp()
    chat_history.append({
        "role": "assistant",
        "name": profile_a["persona_name"],
        "text": a_response,
        "timestamp": ts_a,
    })
    new_entries.append({
        "role": "assistant",
        "name": profile_a["persona_name"],
        "text": a_response,
        "timestamp": ts_a,
    })

    b_response = await call_model(profile_b, profile_a)
    ts_b = get_timestamp()
    chat_history.append({
        "role": "assistant",
        "name": profile_b["persona_name"],
        "text": b_response,
        "timestamp": ts_b,
    })
    new_entries.append({
        "role": "assistant",
        "name": profile_b["persona_name"],
        "text": b_response,
        "timestamp": ts_b,
    })

    return {
        "user_entry": {
            "role": "user",
            "name": "User",
            "text": request.message,
            "timestamp": user_ts,
        },
        "responses": new_entries,
    }


@app.post("/api/chat/single")
async def single_model(request: SingleModelRequest):
    global profile_a, profile_b
    update_profile("a", request.profile_a)
    update_profile("b", request.profile_b)

    user_entry = None
    if request.message:
        user_ts = get_timestamp()
        chat_history.append({
            "role": "user",
            "name": "User",
            "text": request.message,
            "timestamp": user_ts,
        })
        user_entry = {
            "role": "user",
            "name": "User",
            "text": request.message,
            "timestamp": user_ts,
        }

    if request.target == "a":
        active, opposing = profile_a, profile_b
    else:
        active, opposing = profile_b, profile_a

    response = await call_model(active, opposing)
    resp_ts = get_timestamp()
    chat_history.append({
        "role": "assistant",
        "name": active["persona_name"],
        "text": response,
        "timestamp": resp_ts,
    })

    result = {
        "role": "assistant",
        "name": active["persona_name"],
        "text": response,
        "timestamp": resp_ts,
    }
    if user_entry:
        result["user_entry"] = user_entry
    return result


@app.post("/api/chat/new")
async def new_chat():
    global chat_history, profile_a, profile_b
    chat_history.clear()
    profile_a["rag_text"] = ""
    profile_b["rag_text"] = ""
    return {"status": "ok", "message": "Chat history and RAG buffers cleared."}


@app.get("/api/export")
async def export_chat():
    lines = ["# ConvoGreen Chat Export\n"]
    for entry in chat_history:
        if entry["role"] == "user":
            lines.append(f"**User Responded at {entry['timestamp']}:**\n\n{entry['text']}\n")
        else:
            lines.append(f"**{entry['name']} Responded at {entry['timestamp']}:**\n\n{entry['text']}\n")

    content = "\n---\n\n".join(lines)
    return StreamingResponse(
        iter([content]),
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename=convogreen_export.md"},
    )


@app.post("/api/upload/{target}")
async def upload_file(target: str, file: UploadFile = File(...)):
    global profile_a, profile_b
    p = profile_a if target == "a" else profile_b
    text = parse_file_content(file)
    p["rag_text"] = (p["rag_text"] + "\n\n---\n\n" + text) if p["rag_text"] else text
    return {"filename": file.filename, "preview": text[:200]}
