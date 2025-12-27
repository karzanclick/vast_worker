import asyncio
from vastai import Serverless
import os
# add VAST_API_KEY to your environment variables before running
os.environ["VAST_API_KEY"] = "744fb1605309b6cf312b785ca09c3d2b23586946df0b3e265b1c9967600a8fd6"


MAX_TOKENS = 128

async def main():
    async with Serverless() as client:
        endpoint = await client.get_endpoint(name="wgugoh4t")

        payload = {
            "model": "Qwen/Qwen3-8B",
            "prompt" : "Who are you?",
            "max_tokens" : MAX_TOKENS,
            "temperature" : 0.7
        }
        
        response = await endpoint.request("/v1/completions", payload, cost=MAX_TOKENS)
        print(response["response"]["choices"][0]["text"])

if __name__ == "__main__":
    asyncio.run(main())