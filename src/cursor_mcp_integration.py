#!/usr/bin/env python3

import json
import os
import asyncio
import websockets
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CursorMCPIntegration:
    """Integration with Cursor using Model Context Protocol"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.uri = f"ws://{host}:{port}"
        self.connection = None
        self.cursor_path = "/Applications/Cursor.app/Contents/MacOS/Cursor"
        
    async def initialize_cursor(self) -> bool:
        """Initialize Cursor with MCP configuration"""
        try:
            # Check if Cursor exists
            if not os.path.exists(self.cursor_path):
                logger.error(f"Cursor not found at: {self.cursor_path}")
                return False
                
            logger.info(f"Found Cursor at: {self.cursor_path}")
            
            # Start Cursor with MCP enabled
            process = subprocess.Popen(
                [self.cursor_path, "--enable-mcp", "--mcp-port", "8765"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for Cursor to initialize
            await asyncio.sleep(5)
            
            # Check if process is running
            if process.poll() is None:
                logger.info("Cursor started successfully with MCP enabled")
                return True
            else:
                stdout, stderr = process.communicate()
                logger.error(f"Cursor failed to start: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize Cursor: {e}")
            return False
    
    async def connect(self) -> bool:
        """Establish WebSocket connection with Cursor MCP"""
        try:
            # Initialize Cursor first
            if not await self.initialize_cursor():
                return False
            
            # Connect to MCP
            self.connection = await websockets.connect(self.uri)
            logger.info("Connected to Cursor MCP")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Cursor MCP: {e}")
            return False
            
    async def send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send a command to Cursor and get the response"""
        if not self.connection:
            if not await self.connect():
                return {"error": "Failed to connect to Cursor"}
        
        try:
            await self.connection.send(json.dumps(command))
            response = await self.connection.recv()
            return json.loads(response)
        except Exception as e:
            logger.error(f"Error sending command to Cursor: {e}")
            return {"error": str(e)}
            
    async def generate_code(self, instructions: str, output_dir: Path) -> bool:
        """Generate code based on instructions"""
        command = {
            "type": "generate_code",
            "instructions": instructions,
            "output_directory": str(output_dir),
            "settings": {
                "model": "claude-3-opus-20240229",
                "temperature": 0.7,
                "max_tokens": 4000
            }
        }
        
        response = await self.send_command(command)
        
        if "error" in response:
            logger.error(f"Code generation failed: {response['error']}")
            return False
            
        if response.get("status") == "success":
            generated_files = response.get("files", [])
            for file_info in generated_files:
                file_path = output_dir / file_info["path"]
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(file_path, "w") as f:
                    f.write(file_info["content"])
                    
            logger.info(f"Generated {len(generated_files)} files in {output_dir}")
            return True
        else:
            logger.error(f"Code generation failed: {response.get('message', 'Unknown error')}")
            return False
            
    async def setup_project(self, spec_path: str, output_dir: str) -> Optional[Path]:
        """Set up a new project based on specification"""
        try:
            # Load specification
            with open(spec_path, "r") as f:
                spec = json.load(f)
                
            # Create output directory
            project_dir = Path(output_dir) / spec["title"].lower().replace(" ", "_")
            project_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate project structure
            structure_command = {
                "type": "create_project_structure",
                "specification": spec,
                "output_directory": str(project_dir)
            }
            
            response = await self.send_command(structure_command)
            if "error" in response:
                logger.error(f"Failed to create project structure: {response['error']}")
                return None
                
            # Generate code for each component
            success = await self.generate_code(json.dumps(spec), project_dir)
            if not success:
                return None
                
            return project_dir
            
        except Exception as e:
            logger.error(f"Error setting up project: {e}")
            return None
            
    async def close(self):
        """Close the connection to Cursor"""
        if self.connection:
            await self.connection.close()
            self.connection = None

async def main():
    """Main function to test the integration"""
    integration = CursorMCPIntegration()
    
    # Example usage
    spec_path = "specs/ai_creative_collaborator_20250316_133542.json"
    output_dir = "generated_projects"
    
    project_dir = await integration.setup_project(spec_path, output_dir)
    if project_dir:
        print(f"Project generated successfully at: {project_dir}")
    else:
        print("Failed to generate project")
        
    await integration.close()

if __name__ == "__main__":
    asyncio.run(main()) 