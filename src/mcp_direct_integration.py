import asyncio
import websockets
import json
import os
from pathlib import Path

class CursorMCPIntegration:
    def __init__(self, port=8765):
        self.port = port
        self.uri = f"ws://localhost:{port}"
        self.workspace_root = Path(os.getcwd())

    async def connect(self):
        """Establish WebSocket connection with Cursor MCP"""
        try:
            self.websocket = await websockets.connect(self.uri)
            print("Connected to Cursor MCP")
            return True
        except Exception as e:
            print(f"Failed to connect to Cursor MCP: {e}")
            return False

    async def process_specification(self, spec_file):
        """Process a specification file and generate code"""
        try:
            # Read and parse specification
            with open(spec_file, 'r') as f:
                spec = json.load(f)

            # Create output directory
            project_name = spec['title'].lower().replace(' ', '_')
            output_dir = self.workspace_root / 'generated_projects' / project_name
            output_dir.mkdir(parents=True, exist_ok=True)

            # Generate instructions
            instructions = self.generate_instructions(spec)
            instructions_file = output_dir / 'INSTRUCTIONS.md'
            with open(instructions_file, 'w') as f:
                f.write(instructions)

            # Send command to Cursor for code generation
            message = {
                "command": "generateCode",
                "data": {
                    "instructions": instructions,
                    "outputDir": str(output_dir)
                }
            }
            
            await self.websocket.send(json.dumps(message))
            response = await self.websocket.recv()
            print(f"Cursor response: {response}")
            
            return True

        except Exception as e:
            print(f"Error processing specification: {e}")
            return False

    def generate_instructions(self, spec):
        """Generate markdown instructions from specification"""
        return f"""# Project: {spec['title']}

## Overview
{spec['description']}

## Requirements

### Key Features
{chr(10).join(f"- {f['name']}: {f['description']} (Priority: {f['priority']})" for f in spec['features'])}

### Technical Stack
{chr(10).join(f"- {t['name']}: {t['purpose']}" for t in spec['technologies'])}

### Architecture
Type: {spec['architecture']['type']}

Components:
{chr(10).join(f"- {c['name']}: {c['purpose']}{chr(10)}  Interactions: {', '.join(c['interactions'])}" for c in spec['architecture']['components'])}

## Implementation Plan
{chr(10).join(f"Phase {i+1}: {phase['phase']} ({phase['duration']}){chr(10)}" + chr(10).join(f"  - {task['name']} ({task['duration']})" for task in phase['tasks']) for i, phase in enumerate(spec['implementationPlan']))}

## Development Guidelines

1. Follow modern development practices and patterns
2. Implement proper error handling and logging
3. Write clean, maintainable, and well-documented code
4. Include appropriate tests for all components
5. Consider scalability and performance in the implementation

Please generate the project structure and implementation based on these specifications."""

async def main():
    integration = CursorMCPIntegration()
    
    if await integration.connect():
        spec_file = Path('specs/test_project.json')
        if spec_file.exists():
            await integration.process_specification(spec_file)
        else:
            print(f"Specification file not found: {spec_file}")
    
    # Keep the connection alive
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")

if __name__ == "__main__":
    asyncio.run(main()) 