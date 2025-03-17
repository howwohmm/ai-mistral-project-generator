from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
import sys
import os
import json
import logging
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Create a new FastAPI app for Vercel
app = FastAPI()

# Initialize Mistral client
api_key = os.getenv('MISTRAL_API_KEY')
if not api_key:
    logger.error("MISTRAL_API_KEY environment variable is not set")
    raise ValueError("MISTRAL_API_KEY environment variable is not set")
    
client = MistralClient(api_key=api_key)
MODEL = os.getenv('MODEL_NAME', 'mistral-large-latest')

# Health check endpoint
@app.get("/api/health")
async def health_check():
    try:
        # Test the Mistral client
        response = client.chat(
            model=MODEL,
            messages=[ChatMessage(role="user", content="test")],
            temperature=0.7,
        )
        return {
            "status": "healthy",
            "service": "AI Creative Collaborator",
            "mistral_api": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "AI Creative Collaborator",
            "error": str(e)
        }

# Chat endpoint
@app.post("/api/chat")
async def chat(request: Request):
    try:
        # Parse request body
        body = await request.json()
        messages = body.get("messages", [])
        
        # Log incoming request
        logger.info("Received chat request")
        
        # Count previous messages to determine phase
        user_msg_count = sum(1 for msg in messages if msg["role"] == "user")
        logger.info(f"User message count: {user_msg_count}")
        
        # If this is early in the conversation (1-2 messages), use question-asking mode
        if user_msg_count <= 2:
            system_message = ChatMessage(
                role="system",
                content="""You are an AI creative collaborator who MUST follow this exact questioning pattern:

CRUCIAL FORMAT REQUIREMENTS:
- Begin with a brief acknowledgment of the user's idea
- ALWAYS format your first response in this EXACT structure:

"[Brief acknowledgment of idea]

1️⃣ [Category Name (e.g., Core Functionality)]:
- [Specific question 1]
- [Specific question 2]

2️⃣ [Different Category (e.g., User Experience)]:
- [Specific question 1]
- [Specific question 2]

✅ Possible Features (Let me know if these sound good):
- [Feature suggestion 1]
- [Feature suggestion 2]
- [Feature suggestion 3]"

IMPORTANT RULES:
1. NEVER generate a PRD or complete solution in early messages
2. Ask AT LEAST 5-7 questions total across categories
3. Questions should be brief but specific
4. Always suggest 3-4 potential features with checkmarks (✅)
5. EXACTLY match the formatting of the example above

Example response to "I want a browser extension that makes tweets philosophical":
"That sounds like a fun creative tool! Let me ask a few questions to understand your vision better:

1️⃣ Core Functionality:
- Does this only work on Twitter, or should it work anywhere you type?
- Should it rewrite the entire text, or just suggest an alternate version?

2️⃣ Style Customization:
- How many philosophical styles do you want included?
- Would you want a setting to control how extreme the rewrite is?

3️⃣ User Interaction:
- Should the user activate it manually or should it auto-suggest changes?
- Would users be able to tweak the output before posting?

✅ Possible Features (Let me know if these sound good):
- Rewrite History so users can see past versions
- Emoji Mode where it adds relevant philosophical emojis
- Tone Slider (Casual → Formal → Extreme)
- Save Favorite Styles for quick access"

YOU MUST FOLLOW THIS EXACT FORMAT IN YOUR FIRST 1-2 RESPONSES."""
            )
        # Otherwise, use collaborative brainstorming mode
        else:
            system_message = ChatMessage(
                role="system",
                content="""You are a collaborative AI partner helping refine product ideas.

After initial questions, you can now help structure the idea, but STILL be interactive:

1. Keep responses concise, use bullet points when possible
2. Maintain a conversational, helpful tone
3. If suggesting technical solutions, give clear reasons WHY they fit
4. Periodically ask if the user wants to move to PRD creation
5. Use formatting like bold/italics/emojis to highlight key points

WHEN APPROPRIATE, offer to organize the information into:
- Project name (creative but descriptive)
- Clear problem statement
- Target users
- Prioritized features
- Technical stack suggestions
- Initial architecture

NEVER jump straight to a complete PRD without asking if the user is ready.
Maintain the conversational flow at all times."""
            )
        
        # Log system message content
        logger.info(f"Using system message: {system_message.content[:100]}...")
        
        # Convert user messages and add system message
        chat_messages = [system_message] + [
            ChatMessage(role=msg["role"], content=msg["content"]) 
            for msg in messages
        ]
        
        # Make the API call
        logger.info(f"Sending request to Mistral API with {len(chat_messages)} messages, model={MODEL}")
        response = client.chat(
            model=MODEL,
            messages=chat_messages,
            temperature=0.9,  # Slightly lower to prevent extremely creative but verbose responses
        )
        
        # Extract the response content
        try:
            content = response.choices[0].message.content
            # Log the response
            logger.info(f"Response from Mistral: {content[:100]}...")
            return {"response": content}
        except (AttributeError, IndexError) as e:
            logger.error(f"Failed to extract content from response: {e}")
            logger.error(f"Response structure: {dir(response)}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Failed to extract content from Mistral's response"}
            )
            
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        logger.error(f"Full error details: {repr(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error processing chat request: {str(e)}"}
        )

# Simple HTML response for the root path
@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Project Generator with Mistral</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 2rem;
                line-height: 1.6;
            }
            h1 {
                color: #333;
                border-bottom: 1px solid #eee;
                padding-bottom: 0.5rem;
            }
            .btn {
                display: inline-block;
                background-color: #0070f3;
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 4px;
                text-decoration: none;
                margin-top: 1rem;
            }
            .btn:hover {
                background-color: #0051a2;
            }
        </style>
    </head>
    <body>
        <h1>AI Project Generator with Mistral</h1>
        <p>This is the API server for the AI Project Generator. The frontend is deployed separately.</p>
        <p>Check the <a href="/api/health">health endpoint</a> to confirm the API is working.</p>
        <p>API endpoints:</p>
        <ul>
            <li><a href="/api/health">/api/health</a> - Check API health</li>
            <li><code>/api/chat</code> - Chat with Mistral (POST)</li>
        </ul>
        <a href="https://github.com/howwohmm/ai-mistral-project-generator" class="btn">View on GitHub</a>
    </body>
    </html>
    """