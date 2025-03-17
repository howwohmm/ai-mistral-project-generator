from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import json
import os
from pathlib import Path
from dotenv import load_dotenv
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="AI Creative Collaborator")

# Configure CORS - Allow Vercel domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:8502", "https://*.vercel.app", "https://*.now.sh"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Mistral client
api_key = os.getenv('MISTRAL_API_KEY')
if not api_key:
    logger.error("MISTRAL_API_KEY environment variable is not set")
    raise ValueError("MISTRAL_API_KEY environment variable is not set")
    
client = MistralClient(api_key=api_key)
MODEL = os.getenv('MODEL_NAME', 'mistral-large-latest')

# Models
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

class ProjectSpec(BaseModel):
    title: str
    description: str
    features: List[dict]
    technologies: List[dict]
    architecture: dict
    implementationPlan: List[dict]

# Health check endpoint
@app.get("/health")
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

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": f"Endpoint {request.url.path} not found"}
    )

@app.exception_handler(405)
async def method_not_allowed_handler(request, exc):
    return JSONResponse(
        status_code=405,
        content={"detail": f"Method {request.method} not allowed for {request.url.path}"}
    )

# Routes
@app.get("/chat")
async def get_chat_info():
    return {
        "message": "This endpoint accepts POST requests with a ChatRequest body",
        "example": {
            "messages": [
                {"role": "user", "content": "Your message here"}
            ]
        }
    }

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # Log incoming request
        logger.info("Received chat request")
        
        # Count previous messages to determine phase
        user_msg_count = sum(1 for msg in request.messages if msg.role == "user")
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
            ChatMessage(role=msg.role, content=msg.content) 
            for msg in request.messages
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
            raise HTTPException(
                status_code=500,
                detail="Failed to extract content from Mistral's response"
            )
            
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        logger.error(f"Full error details: {repr(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        )

@app.get("/generate-prd")
async def get_prd_info():
    return {
        "message": "This endpoint accepts POST requests with a ChatRequest body to generate a PRD",
        "example": {
            "messages": [
                {"role": "user", "content": "I want to build a task management app"}
            ]
        }
    }

@app.post("/generate-prd")
async def generate_prd(request: ChatRequest):
    try:
        # Add system message for PRD generation
        system_message = ChatMessage(
            role="system",
            content="""You are creating a structured PRD as a JSON object. ONLY return the JSON with NO additional text.

Focus on creating a clear, implementable spec with:
1. A concise project description (2-3 sentences)
2. 3-5 specific, prioritized features with short descriptions 
3. Relevant technologies with clear justification
4. A simplified architecture
5. A realistic implementation plan with 2-3 phases"""
        )
        
        # Convert messages and add system message
        chat_messages = [system_message] + [
            ChatMessage(role=msg.role, content=msg.content) 
            for msg in request.messages
        ]
        
        # Add final instruction for JSON format
        chat_messages.append(ChatMessage(
            role="user",
            content="""Create a PRD in JSON format with this EXACT structure:
{
    "title": "Project Title",
    "description": "Brief description - 2-3 sentences only",
    "features": [
        {"name": "Feature 1", "description": "Short description", "priority": "High"},
        {"name": "Feature 2", "description": "Short description", "priority": "Medium"}
    ],
    "technologies": [
        {"name": "Technology 1", "purpose": "Brief explanation"},
        {"name": "Technology 2", "purpose": "Brief explanation"}
    ],
    "architecture": {
        "type": "Type (e.g. Client-Server, Microservices)",
        "components": [
            {"name": "Component 1", "purpose": "Purpose", "interactions": ["Interaction 1"]}
        ]
    },
    "implementationPlan": [
        {"phase": "Phase 1", "duration": "X weeks", "tasks": [{"name": "Task 1", "duration": "X days"}]}
    ],
    "projectLinks": {
        "frontend": "http://localhost:3000",
        "backend": "http://localhost:3001",
        "repository": "generated_projects/[project_name]"
    }
}

ONLY return valid JSON with NO other text. Ensure JSON is valid - no trailing commas or syntax errors."""
        ))

        try:
            response = client.chat(
                model=MODEL,
                messages=chat_messages,
                temperature=0.1,  # Very low temperature for consistent JSON
            )
            
            # Extract JSON from response
            spec_text = response.choices[0].message.content.strip()
            
            # Try to clean up JSON text if needed
            if not spec_text.startswith('{'):
                # Try to find JSON object using regex
                import re
                json_match = re.search(r'({[\s\S]*})', spec_text)
                if json_match:
                    spec_text = json_match.group(1)
                else:
                    raise ValueError("Could not find valid JSON in Mistral's response")
            
            # Remove any markdown code block markers
            spec_text = spec_text.replace('```json', '').replace('```', '')
            
            try:
                spec_json = json.loads(spec_text)
            except json.JSONDecodeError:
                # Try to fix common JSON issues
                spec_text = re.sub(r',(\s*[}\]])', r'\1', spec_text)  # Remove trailing commas
                spec_json = json.loads(spec_text)
            
            # Validate required fields
            required_fields = ["title", "description", "features", "technologies", "architecture", "implementationPlan"]
            missing_fields = [field for field in required_fields if field not in spec_json]
            if missing_fields:
                raise ValueError(f"Missing required fields in JSON: {', '.join(missing_fields)}")
                
            # Always set projectLinks to use port 3000
            spec_json["projectLinks"] = {
                "frontend": "http://localhost:3000",
                "backend": "http://localhost:3001",
                "repository": f"generated_projects/{spec_json['title'].lower().replace(' ', '_')}"
            }
                
            return spec_json
            
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to parse JSON from Mistral's response. Error: {str(e)}\nResponse: {spec_text[:200]}..."
            )
        except ValueError as e:
            raise HTTPException(status_code=500, detail=str(e))
            
    except Exception as e:
        logger.error(f"Error in generate_prd endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create-project")
async def create_project(spec: ProjectSpec):
    try:
        # Create project directory
        project_name = spec.title.lower().replace(" ", "_")
        project_dir = Path("generated_projects") / project_name
        project_dir.mkdir(parents=True, exist_ok=True)

        # Generate detailed implementation instructions
        implementation_guide = f"""# Project Implementation Guide: {spec.title}

## Overview
{spec.description}

## Implementation Checklist

### Setup
- [x] Create project structure
- [ ] Install dependencies
- [ ] Configure server for port 3000
- [ ] Setup build process
- [ ] Configure environment variables

### Features
{chr(10).join(f"- [ ] **{f['name']}** (Priority: {f['priority']})\n  - {f['description']}" for f in spec.features)}

### Technical Requirements
{chr(10).join(f"- [ ] **{t['name']}**: {t['purpose']}" for f in spec.technologies)}

### Architecture Implementation
**Type:** {spec.architecture['type']}

**Components to Implement:**
{chr(10).join(f"- [ ] **{c['name']}**\n  - Purpose: {c['purpose']}\n  - Interactions: {', '.join(c['interactions'])}" for c in spec.architecture['components'])}

## Implementation Plan
{chr(10).join(f"### Phase {i+1}: {phase['phase']} ({phase['duration']})\n" + chr(10).join(f"- [ ] {task['name']} ({task['duration']})" for task in phase['tasks']) for i, phase in enumerate(spec.implementationPlan))}

## Server Configuration
The application should be configured to run on the following ports:
- Frontend: http://localhost:3000
- Backend API: http://localhost:3001

## Development Guidelines
1. Write clean, modular code with proper comments
2. Implement proper error handling
3. Include tests for all major functionality
4. Use environment variables for configuration
5. Document API endpoints

## Next Steps
1. Start by implementing the server setup on port 3000
2. Implement core features first
3. Add styling and UI enhancements
4. Implement integration with required services
5. Add tests and documentation
"""

        # Save implementation guide
        with open(project_dir / "IMPLEMENTATION_GUIDE.md", "w") as f:
            f.write(implementation_guide)

        # Save original PRD as a reference
        instructions = f"""# Project: {spec.title}

## Project Description
{spec.description}

## Project Links
- Frontend: http://localhost:3000
- Backend: http://localhost:3001

## Getting Started
1. Make sure you have Node.js installed
2. Run `npm install` to install dependencies
3. Run `npm run dev` to start the development server
4. Open your browser to http://localhost:3000

## Scope
This project implements the functionality defined in the PRD.
"""

        # Save PRD instructions
        with open(project_dir / "PRD.md", "w") as f:
            f.write(instructions)
            
        # Create a basic project structure for implementation
        # Create folders for frontend, backend, and shared code
        (project_dir / "src").mkdir(exist_ok=True)
        (project_dir / "src" / "frontend").mkdir(exist_ok=True)
        (project_dir / "src" / "backend").mkdir(exist_ok=True)
        (project_dir / "src" / "shared").mkdir(exist_ok=True)
        (project_dir / "docs").mkdir(exist_ok=True)
        (project_dir / "tests").mkdir(exist_ok=True)
            
        # Add README with project links
        readme = f"""# {spec.title}

{spec.description}

## Project Links
- Frontend: http://localhost:3000
- Backend: http://localhost:3001
- Project Directory: {str(project_dir)}

## Getting Started
1. Clone this repository
2. Install dependencies: `npm install`
3. Start the development server: `npm run dev`
4. Access the application at http://localhost:3000

## Features
{chr(10).join(f"- {f['name']}: {f['description']}" for f in spec.features)}

## Implementation Status
See IMPLEMENTATION_GUIDE.md for the current implementation status and next steps.
"""
        with open(project_dir / "README.md", "w") as f:
            f.write(readme)
            
        # Create a .env file for environment configuration
        env_file = """# Environment Configuration
PORT=3000
API_PORT=3001
NODE_ENV=development

# Add any API keys or secrets below (but don't commit them to version control)
# API_KEY=your_api_key_here
"""
        with open(project_dir / ".env", "w") as f:
            f.write(env_file)

        return {
            "project_dir": str(project_dir),
            "frontend_url": "http://localhost:3000",
            "backend_url": "http://localhost:3001"
        }
        
    except Exception as e:
        logger.error(f"Error in create_project endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    try:
        # Check if port 8000 is already in use
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 8000))
        sock.close()
        
        if result == 0:
            logger.warning("Port 8000 is already in use. Using port 8001 instead.")
            port = 8001
        else:
            port = 8000
            
        logger.info(f"Starting server on localhost:{port} with model {MODEL}")
        uvicorn.run(
            app, 
            host="127.0.0.1",
            port=port,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        raise 