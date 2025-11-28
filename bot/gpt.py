import os
import logging

from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv("env.env")

# Initialize logging
logger = logging.getLogger("gpt")

# from settings import OPEN_AI_KEY
openAiKey = os.getenv("OPEN_AI_KEY")
baseUrl = os.getenv("BASE_URL")
# gpt = AsyncOpenAI(api_key=OPEN_AI_KEY,
#                   http_client=httpx.AsyncClient())

# openAiKey = OPEN_AI_KEY
gpt = AsyncOpenAI(api_key=openAiKey, base_url=baseUrl)


async def gpt_request(text, model="deepseek-chat-v3-0324:free"):
    logger.debug(f"Starting GPT request with model {model}")
    logger.info(f"Request text: {text[:100]}...")

    response = await gpt.chat.completions.create(
        messages=[{"role": "user", "content": str(text)}], model=model
    )

    logger.debug(
        f"GPT response received: {response.choices[0].message.content[:50]}..."
    )
    return response

def split_text(text, max_length=4096, prefix_length=0):
    effective_max = max_length - prefix_length
    if effective_max <= 0:
        raise ValueError("Prefix length exceeds or equals max_length")
        
    chunks = []
    while len(text) > effective_max:
        split_at = text.rfind(' ', 0, effective_max)
        if split_at == -1:
            split_at = effective_max
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip()
    chunks.append(text)
    logger.debug(f"Split text into {len(chunks)} chunks (effective max: {effective_max})")
    for i, chunk in enumerate(chunks, 1):
        logger.debug(f"Chunk {i} length: {len(chunk)}")
    return chunks

if __name__ == "__main__":
    # Test the split_text function
    long_text = " ".join(["word"] * 10000)  # Create a very long text
    chunks = split_text(long_text)
    print(f"Split into {len(chunks)} chunks")
    for i, chunk in enumerate(chunks, 1):
        print(f"Chunk {i}: {len(chunk)} chars")
