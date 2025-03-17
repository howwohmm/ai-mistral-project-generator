from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import sys
import os

# Add parent directory to path so we can import the backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the FastAPI app from backend
from src.backend.main import app as backend_app

# Create a new FastAPI app for Vercel
app = FastAPI()

# Forward all requests to the backend app
@app.get("/api/{path:path}")
async def forward_to_backend(request: Request, path: str):
    return await backend_app.handle_request(request)

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
        <a href="https://github.com/howwohmm/ai-mistral-project-generator" class="btn">View on GitHub</a>
    </body>
    </html>
    """ 