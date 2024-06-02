import json
import logging

logger = logging.getLogger(__name__)

url = "http://localhost:11434/api/generate"


async def make_async_request(session, text):
    data = {
        "model": "intent-extraction",
        "prompt": text,  # Remove leading/trailing whitespaces
        "stream": False,
        "format": "json",
    }
    headers = {"Content-Type": "application/json"}

    async with session.post(url, json=data, headers=headers) as resp:
        try:
            if resp.content_type == "application/x-ndjson":
                # Read ndjson content line by line and parse each line as JSON
                results = [json.loads(line) async for line in resp.content.iter_any()]
                return results[0]["response"].strip()
            else:
                result = await resp.json()  # Use .json() to parse JSON response
                return result["response"].strip()
        except Exception as e:
            logger.error(f"Fail with {text}: {str(e)}")
            return "ERROR"
