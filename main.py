from fastapi import FastAPI

app = FastAPI(title="AI TOP 100 Bot")

@app.get("/health")
async def health():
    return {"status": "ok"}
