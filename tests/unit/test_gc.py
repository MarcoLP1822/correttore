# test_full.py
import asyncio, grammarcheck, llm_correct
from openai import AsyncOpenAI

async def demo():
    txts   = ["pò", "D’ALI", "Lu'"]
    step1  = [grammarcheck.grammarcheck(t) for t in txts]
    client = AsyncOpenAI(api_key="...")          # legge API-key da variabile
    fixed  = await llm_correct.llm_correct_batch(step1, client)
    print("Step 1  →", step1)
    print("Final   →", fixed)

asyncio.run(demo())
