#!/usr/bin/env python3

import json
import os
import subprocess
import sys
from pathlib import Path
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_specification(spec_path: str) -> Optional[Dict[str, Any]]:
    """Load and validate a specification file"""
    try:
        with open(spec_path, 'r') as f:
            spec = json.load(f)
        
        # Validate essential fields
        required_fields = ['title', 'description', 'features', 'technologies', 'architecture']
        for field in required_fields:
            if field not in spec:
                logger.warning(f"Specification missing '{field}' field")
        
        return spec
    except Exception as e:
        logger.error(f"Error loading specification: {str(e)}")
        return None

def generate_cursor_prompt(specification: Dict[str, Any]) -> str:
    """Transform specification into a detailed prompt for Cursor"""
    
    # Extract key elements from specification
    title = specification.get('title', 'Unnamed Project')
    description = specification.get('description', '')
    features = specification.get('features', [])
    technologies = specification.get('technologies', [])
    architecture = specification.get('architecture', {})
    implementation_plan = specification.get('implementationPlan', [])
    
    # Format features section
    features_text = "\n".join([
        f"- {f['name']}: {f['description']} (Priority: {f.get('priority', 'medium')})"
        for f in features
    ])
    
    # Format technologies section
    tech_text = "\n".join([
        f"- {t['name']}: {t['purpose']}"
        for t in technologies
    ])
    
    # Format architecture section
    arch_components = architecture.get('components', [])
    arch_text = "\n".join([
        f"- {c['name']}: {c['purpose']}\n  Interactions: {'; '.join(c.get('interactions', []))}"
        for c in arch_components
    ])
    
    # Format implementation plan
    impl_text = "\n".join([
        f"Phase {i+1}: {phase['phase']} ({phase['duration']})\n" +
        "\n".join([f"  - {task['name']} ({task['duration']})" for task in phase.get('tasks', [])])
        for i, phase in enumerate(implementation_plan)
    ])
    
    # Create the complete prompt
    cursor_prompt = f"""# Project: {title}

## Overview
{description}

## Requirements

### Key Features
{features_text}

### Technical Stack
{tech_text}

### Architecture
Type: {architecture.get('type', 'Not specified')}

Components:
{arch_text}

## Implementation Plan
{impl_text}

## Development Guidelines

1. Follow modern development practices and patterns
2. Implement proper error handling and logging
3. Write clean, maintainable, and well-documented code
4. Include appropriate tests for all components
5. Consider scalability and performance in the implementation

Please generate the project structure and implementation based on these specifications.
"""
    return cursor_prompt

def create_project_folder(specification: Dict[str, Any]) -> Path:
    """Create a project folder based on the specification"""
    project_name = specification.get('title', 'new_project').lower().replace(' ', '_')
    project_path = Path('generated_projects') / project_name
    
    if not project_path.exists():
        project_path.mkdir(parents=True)
        logger.info(f"Created project folder: {project_path}")
    else:
        logger.info(f"Project folder already exists: {project_path}")
    
    return project_path

def write_cursor_prompt(project_path: Path, cursor_prompt: str) -> Path:
    """Write the Cursor prompt to a file"""
    prompt_file = project_path / "CURSOR_INSTRUCTIONS.md"
    
    with open(prompt_file, 'w') as f:
        f.write(cursor_prompt)
    
    logger.info(f"Written Cursor instructions to: {prompt_file}")
    return prompt_file

def launch_cursor(prompt_file: Path) -> None:
    """Launch Cursor with the prompt file"""
    try:
        # This assumes 'cursor' is in your PATH
        subprocess.run(["cursor", str(prompt_file)])
        logger.info("Launched Cursor with the instructions file")
    except Exception as e:
        logger.error(f"Could not launch Cursor automatically: {e}")
        logger.info(f"Please open the following file in Cursor manually:")
        logger.info(f"  {prompt_file}")

def connect_claude_to_cursor(spec_path: str, output_dir: str = "generated_projects") -> Optional[Path]:
    """Main function to connect Claude specifications to Cursor code generation"""
    logger.info(f"Processing specification: {spec_path}")
    
    # 1. Load specification
    specification = load_specification(spec_path)
    if not specification:
        return None
    
    # 2. Generate Cursor prompt
    cursor_prompt = generate_cursor_prompt(specification)
    
    # 3. Create project folder
    project_path = create_project_folder(specification)
    
    # 4. Write the cursor prompt to a file
    prompt_file = write_cursor_prompt(project_path, cursor_prompt)
    
    return project_path

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Connect Claude specifications to Cursor code generation')
    parser.add_argument('spec_path', help='Path to the specification JSON file')
    parser.add_argument('--output', '-o', default='generated_projects', 
                       help='Directory to save generated code')
    parser.add_argument('--launch', '-l', action='store_true',
                       help='Launch Cursor after generating the instructions')
    
    args = parser.parse_args()
    
    result = connect_claude_to_cursor(args.spec_path, args.output)
    if result:
        print(f"\nProject setup complete!")
        print(f"Project folder: {result}")
        
        if args.launch:
            prompt_file = result / "CURSOR_INSTRUCTIONS.md"
            launch_cursor(prompt_file)
        else:
            print(f"\nTo proceed with code generation:")
            print(f"1. Open Cursor")
            print(f"2. Open the instructions file: {result}/CURSOR_INSTRUCTIONS.md")
            print(f"3. Use Cursor's AI features to generate the project code") 