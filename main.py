import logging
import os
import secrets

import httpx
from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request, Response
from openai import AsyncOpenAI

app = FastAPI(title="AI TOP 100 Bot")
log = logging.getLogger(__name__)
KAKAO_CALLBACK_URL = "https://kapi.kakao.com/v1/bot/callback"


@app.get("/health")
async def health():
    return {"status": "ok"}


async def answer_question(question: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "AI 서비스 설정을 준비 중입니다. 잠시 후 다시 질문해 주세요."
    client = AsyncOpenAI(api_key=api_key, timeout=45.0)
    response = await client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        instructions="당신은 카카오톡에서 대화하는 한국어 AI 도우미입니다. 친절하고 정확하게, 간결하게 답하세요. 모르면 모른다고 말하세요.",
        input=question,
        max_output_tokens=450,
    )
    return (response.output_text or "답변을 생성하지 못했습니다. 다시 질문해 주세요.")[:1000]


async def process_message(question: str, callback_token: str) -> None:
    try:
        answer = await answer_question(question)
    except Exception:
        log.exception("AI answer failed")
        answer = "답변을 처리하는 중 문제가 생겼습니다. 잠시 후 다시 시도해 주세요."

    bot_token = os.getenv("KAKAO_BOT_TOKEN")
    if not bot_token:
        log.error("KAKAO_BOT_TOKEN is missing")
        return

    body = {
        "skillResponse": {
            "version": "2.0",
            "template": {"outputs": [{"simpleText": {"text": answer}}]},
        }
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                KAKAO_CALLBACK_URL,
                headers={
                    "Authorization": f"KakaoAK {bot_token}",
                    "X-Bot-Callback-Token": callback_token,
                },
                json=body,
            )
            response.raise_for_status()
            result = response.json()
            if result.get("errorCount", 0) or not result.get("sendCount", 0):
                log.error("Kakao callback unsuccessful: %s", result)
    except Exception:
        log.exception("Kakao callback failed")


@app.post("/webhook", status_code=204)
async def webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_bot_secret: str | None = Header(default=None),
):
    expected = os.getenv("KAKAO_WEBHOOK_SECRET")
    if not expected:
        raise HTTPException(status_code=503, detail="Webhook secret is not configured")
    if not x_bot_secret or not secrets.compare_digest(
        x_bot_secret, expected
    ):
        raise HTTPException(status_code=401, detail="Unauthorized")

    payload = await request.json()
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid payload")
    if payload.get("op") == 0 and payload.get("t") == "MESSAGE_CREATE":
        data = payload.get("d")
        if isinstance(data, dict):
            question = data.get("content")
            callback_token = data.get("callbackToken")
            if (
                isinstance(question, str)
                and question.strip()
                and len(question) <= 2000
                and isinstance(callback_token, str)
                and callback_token
            ):
                background_tasks.add_task(
                    process_message, question.strip(), callback_token
                )
    return Response(status_code=204)
