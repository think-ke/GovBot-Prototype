import os
import httpx
import chainlit as cl
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")
API_KEY = os.getenv("GOVSTACK_API_KEY")


@cl.on_chat_start
async def start():
    """Initialize the chat session"""
    # Debug: Check if API key is loaded
    if not API_KEY:
        await cl.Message(
            content="⚠️ Warning: API_KEY not found in environment variables!"
        ).send()
    
    await cl.Message(
        content="Welcome to GovBot! How can I help you today?"
    ).send()


@cl.on_message
async def main(message: cl.Message):
    """Process incoming messages"""
    try:
        # Try multiple authentication methods
        headers_options = [
            {"Authorization": f"Bearer {API_KEY}"},
            {"X-API-Key": API_KEY},
            {"api-key": API_KEY},
        ]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            last_error = None
            
            for headers in headers_options:
                try:
                    response = await client.post(
                        f"{API_BASE_URL}/chat/",
                        json={"message": message.content},
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        await cl.Message(
                            content=data.get("answer", data.get("response", "No response"))
                        ).send()
                        return
                    elif response.status_code == 401:
                        last_error = f"Auth failed with headers: {list(headers.keys())}"
                        continue
                    else:
                        await cl.Message(
                            content=f"Server error: {response.status_code} - {response.text}"
                        ).send()
                        return
                        
                except Exception as e:
                    last_error = str(e)
                    continue
            
            # If all methods failed
            await cl.Message(
                content=f"❌ Authentication failed with all methods.\n\n"
                        f"Last error: {last_error}\n\n"
                        f"API URL: {API_BASE_URL}\n"
                        f"API Key present: {bool(API_KEY)}\n"
                        f"API Key prefix: {API_KEY[:8] if API_KEY else 'None'}..."
            ).send()
            
    except Exception as e:
        await cl.Message(
            content=f"Error: {str(e)}\n\nAPI_BASE_URL: {API_BASE_URL}\nAPI_KEY loaded: {bool(API_KEY)}"
        ).send()