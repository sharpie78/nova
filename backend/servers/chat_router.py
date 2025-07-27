from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from utils.ollama_client import OllamaClient  # Import Ollama client
from utils.logger import logger, setup_logger
import asyncio

setup_logger()
logger = logger.bind(name="Servers-Routes")

router = APIRouter()

# GET route for fetching models (tags)
@router.get("/api/tags")
def get_models():
    try:
        logger.debug("Received request to fetch models from Ollama API.")

        # Create an OllamaClient instance
        ollama_client = OllamaClient()

        # Fetch models from Ollama API
        models = ollama_client.fetch_models()

        logger.debug(f"Fetched models: {models}")

        return {"models": models}
    except Exception as e:
        logger.error(f"Error fetching models: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# POST route for processing chat messages
@router.post("/api/chat")
async def post_chat(request: Request):
    try:
        body = await request.json()
        model = body.get("model")
        messages = body.get("messages", [])

        if not model or not messages:
            logger.warning("Invalid request: Model or messages missing.")
            return JSONResponse(status_code=400, content={"error": "Invalid request. Model and messages are required."})

        logger.debug(f"sent response to llm")

        # Send the message to the LLM using OllamaClient
        ollama_client = OllamaClient()  # Create an instance of the OllamaClient

        # Run the synchronous generator in a separate thread and accumulate the result
        assistant_reply = await asyncio.to_thread(
            consume_generator, ollama_client.fetch_chat_stream_result(messages, model)
        )

        logger.debug(f"received response from llm")

        # Return the LLM's response to the frontend
        return {"status": "ok", "message": assistant_reply}

    except Exception as e:
        logger.error(f"Error processing /api/chat: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# Helper function to consume the synchronous generator in a separate thread
def consume_generator(generator):
    response = ""
    for message in generator:
        response += message  # Accumulate the message content
    return response
