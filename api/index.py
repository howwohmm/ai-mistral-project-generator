from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import sys
import os
import json

# Add parent directory to path so we can import the backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the FastAPI app from backend
from src.backend.main import app as backend_app

# Create a new FastAPI app for Vercel
app = FastAPI()

# Forward all requests to the backend app
@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def forward_to_backend(request: Request, path: str):
    # Get the backend route handler
    for route in backend_app.routes:
        if route.path == f"/{path}" and request.method in route.methods:
            # Get request body
            body = await request.body()
            body_text = body.decode() if body else None
            
            # Parse JSON body if present
            json_body = None
            if body_text:
                try:
                    json_body = json.loads(body_text)
                except:
                    pass
            
            # Call the backend route handler
            if json_body:
                # If we have a JSON body, pass it to the handler
                response = await route.endpoint(json_body)
            else:
                # Otherwise, just call the handler
                response = await route.endpoint()
            
            # Return the response
            if isinstance(response, dict):
                return JSONResponse(content=response)
            return response
    
    # If no matching route is found, return 404
    return JSONResponse(
        status_code=404,
        content={"detail": f"Endpoint /api/{path} not found"}
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
            <li><a href="/api/chat">/api/chat</a> - Chat with Mistral (POST)</li>
            <li><a href="/api/generate-prd">/api/generate-prd</a> - Generate PRD (POST)</li>
            <li><a href="/api/create-project">/api/create-project</a> - Create project (POST)</li>
        </ul>
        <a href="https://github.com/howwohmm/ai-mistral-project-generator" class="btn">View on GitHub</a>
    </body>
    </html>
    """

# Add a direct health check endpoint
@app.get("/api/health")
async def api_health():
    return {"status": "healthy", "service": "AI Project Generator API"}