# test_gc.py
import asyncio, os
from openai import AsyncOpenAI
import llm_correct


async def demo():
    client = AsyncOpenAI(api_key="...")   # 1) client ASYNC
    txts   = ["famigliaaa", "couming out"]
    fixed  = await llm_correct.llm_correct_batch(txts, client)  # 2) ok
    print(fixed)

if __name__ == "__main__":
    asyncio.run(demo())
