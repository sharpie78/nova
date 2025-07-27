# utils/ollama_client.py

import json
import urllib.parse
import urllib.request
import time
from threading import Thread
from typing import List, Generator
from utils.logger import logger, setup_logger

setup_logger()
logger = logger.bind(name="Ollama")

class OllamaClient:
    def __init__(self, api_url="http://127.0.0.1:11434"):
        self.api_url = api_url
        logger.debug("OllamaClient initialized")

    def update_host(self, host_url: str):
        logger.debug(f"update_host() called with {host_url}")
        self.api_url = host_url

    def fetch_models(self) -> List[str]:
        logger.debug("fetch_models() called")
        try:
            with urllib.request.urlopen(
                urllib.parse.urljoin(self.api_url, "/api/tags")
            ) as response:
                data = json.load(response)
                models = [model["name"] for model in data["models"]]
                return models
        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return []

    def delete_model(self, model_name: str) -> str:
        logger.debug(f"delete_model() called for: {model_name}")
        req = urllib.request.Request(
            urllib.parse.urljoin(self.api_url, "/api/delete"),
            data=json.dumps({"name": model_name}).encode("utf-8"),
            method="DELETE",
        )
        try:
            with urllib.request.urlopen(req) as response:
                if response.status == 200:
                    return "Model deleted successfully."
                elif response.status == 404:
                    return "Model not found."
        except Exception as e:
            logger.error(f"Failed to delete model: {e}")
            return f"Failed to delete model: {e}"

    def download_model(self, model_name: str, insecure: bool = False) -> Generator[str, None, None]:
        logger.debug(f"download_model() called for: {model_name}")
        req = urllib.request.Request(
            urllib.parse.urljoin(self.api_url, "/api/pull"),
            data=json.dumps(
                {"name": model_name, "insecure": insecure, "stream": True}
            ).encode("utf-8"),
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as response:
                for line in response:
                    data = json.loads(line.decode("utf-8"))
                    log = data.get("error") or data.get("status") or "No response"
                    if "status" in data:
                        total = data.get("total")
                        completed = data.get("completed", 0)
                        if total:
                            log += f" [{completed}/{total}]"
                    yield log
        except Exception as e:
            logger.error(f"Failed to download model: {e}")
            yield f"Failed to download model: {e}"

    def fetch_chat_stream_result(self, chat_history: List[dict], model_name: str) -> Generator[str, None, None]:
        logger.debug("fetch_chat_stream_result() called")
        request = urllib.request.Request(
            urllib.parse.urljoin(self.api_url, "/api/chat"),
            data=json.dumps(
                {
                    "model": model_name,
                    "messages": chat_history,
                    "stream": True,
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request) as resp:
                for line in resp:
                    data = json.loads(line.decode("utf-8"))
                    if "message" in data:
                        time.sleep(0.01)
                        yield data["message"]["content"]
                    else:
                        logger.debug(f"Streamed data: {data}")
        except Exception as e:
            logger.error(f"Chat stream error: {e}")
            raise
