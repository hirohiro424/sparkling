import os, httpx
from tenacity import retry, wait_fixed, stop_after_attempt

API_KEY = os.getenv("OPENAI_API_KEY")

@retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
async def call_llm(system: str, user: str, model="gpt-5"):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {"model": model, "messages":[
        {"role":"system","content":system},
        {"role":"user","content":user}
    ]}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
