# Development Guide: Cursor AI Agent

This document provides detailed guidance for developers working on the Cursor AI Agent project.

## Project Setup

### Prerequisites

- Python 3.9 or higher
- Git
- Mistral API key
- Cursor AI (optional for implementation integration)

### Environment Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/cursor-ai-agent.git
   cd cursor-ai-agent
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` to add your Mistral API key and configure other settings.

## Project Structure

```
cursor-ai-agent/
├── docs/                     # Documentation
│   ├── PRD.md                # Product Requirements Document
│   ├── ARCHITECTURE.md       # Technical Architecture
│   ├── DEVELOPMENT.md        # This document
│   └── API.md                # API documentation
├── src/                      # Source code
│   ├── idea_intake.py        # Command-line idea intake module
│   ├── idea_intake_gui.py    # GUI for idea intake
│   └── idea_intake_gui_simple.py # Simplified GUI version
├── specs/                    # Generated specifications
├── .env.example              # Example environment variables
├── .gitignore                # Git ignore file
├── requirements.txt          # Python dependencies
└── README.md                 # Project overview
```

## Core Components

### 1. Idea Intake System

The Idea Intake System is responsible for collecting user ideas, guiding them through a structured questioning process, and producing a detailed specification.

#### Key Files:

- `src/idea_intake.py`: Command-line interface for idea intake
- `src/idea_intake_gui.py`: Graphical user interface for idea intake
- `src/idea_intake_gui_simple.py`: Simplified GUI version

#### Development Guidelines:

- Each question should be clear and concise
- Validate user input for each question
- Save progress at each step to prevent data loss
- Provide clear error messages for invalid input
- Structure prompts for optimal Claude response quality

### 2. Claude Integration

The Claude Integration component handles all communication with the Claude API for idea processing and specification generation.

#### Key Components:

- API authentication and request handling
- Prompt engineering and management
- Response parsing and validation
- Error handling and recovery

#### Prompt Engineering Guidelines:

1. **Start with clear instructions**
   - Begin prompts with a clear role and task definition
   - Example: "You are an expert system architect specializing in [technology]. Analyze the following project idea..."

2. **Provide structural guidance**
   - Include expected output format in the prompt
   - Use JSON templates to guide structured responses
   - Example: "Return your analysis in the following JSON format: {...}"

3. **Include examples**
   - For complex tasks, include examples of expected responses
   - Example: "Here's an example of how to analyze a similar project: [example]"

4. **Use temperature settings appropriately**
   - Use lower temperatures (0.0-0.3) for structured, factual responses
   - Use higher temperatures (0.5-0.7) for creative ideation

5. **Handle context limitations**
   - Break large prompts into logical segments
   - Maintain conversation context through state management
   - Use summarization techniques for long conversations

#### Response Parsing Techniques:

1. **JSON Extraction**
   - Request responses in JSON format
   - Use try/except blocks for JSON parsing
   - Validate against expected schema

2. **Fallback Mechanisms**
   - Implement regex extraction as fallback
   - Consider retry with simplified prompts
   - Log parsing failures for improvement

3. **Validation Rules**
   - Check for required fields
   - Validate data types and ranges
   - Verify logical consistency of responses

### 3. Specification Format

The system uses a structured JSON format for specifications to ensure consistency and compatibility with implementation systems.

#### Specification Structure:

```json
{
  "title": "Project Title",
  "description": "Comprehensive project description",
  "features": [
    {
      "name": "Feature Name",
      "description": "Detailed feature description",
      "priority": "high|medium|low",
      "requirements": [
        "Specific requirement 1",
        "Specific requirement 2"
      ]
    }
  ],
  "technologies": [
    {
      "name": "Technology Name",
      "purpose": "Why this technology is chosen",
      "alternatives": [
        "Alternative 1",
        "Alternative 2"
      ]
    }
  ],
  "architecture": {
    "style": "monolith|microservices|serverless",
    "components": [
      {
        "name": "Component Name",
        "purpose": "Component purpose",
        "interactions": [
          "Interaction with other component"
        ]
      }
    ]
  },
  "dataModels": [
    {
      "name": "Model Name",
      "fields": [
        {
          "name": "Field Name",
          "type": "string|number|boolean|etc",
          "description": "Field purpose"
        }
      ],
      "relationships": [
        "Relationship with other model"
      ]
    }
  ],
  "implementationNotes": [
    "Important implementation consideration 1",
    "Important implementation consideration 2"
  ]
}
```

### 4. Error Handling

Robust error handling is critical for providing a good user experience and recovering from API issues.

#### Error Handling Strategy:

1. **Anticipate Failure Points**
   - Claude API connection issues
   - Malformed or unexpected responses
   - Parsing failures
   - User input errors

2. **Implement Graceful Degradation**
   - Fallback to simpler prompts
   - Cache previous successful responses
   - Provide helpful error messages

3. **Logging and Analytics**
   - Log all errors with context
   - Track error rates by type
   - Analyze patterns for improvement

#### Example Error Handling:

```python
def get_claude_response(prompt, max_retries=3):
    retries = 0
    while retries < max_retries:
        try:
            response = client.messages.create(
                model=os.environ.get("MODEL_NAME", "claude-3-opus-20240229"),
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            retries += 1
            logger.error(f"Claude API error: {str(e)}, attempt {retries}/{max_retries}")
            if retries == max_retries:
                return {"error": f"Failed after {max_retries} attempts: {str(e)}"}
            time.sleep(2 ** retries)  # Exponential backoff
```

## Development Workflow

### Feature Development Process

1. **Requirement Analysis**
   - Review the PRD for the feature
   - Define acceptance criteria
   - Identify dependencies

2. **Design**
   - Create technical design document
   - Review with team
   - Update architecture docs if needed

3. **Implementation**
   - Follow coding standards
   - Add appropriate tests
   - Document as you go

4. **Testing**
   - Unit tests for components
   - Integration tests for API interactions
   - End-to-end tests for workflows

5. **Code Review**
   - Peer review for quality and standards
   - Verify against acceptance criteria
   - Check test coverage

### Testing Strategy

#### Unit Testing

- Test individual components in isolation
- Mock external dependencies (Claude API)
- Focus on edge cases and error handling

#### Integration Testing

- Test Claude API integration
- Verify correct prompt construction
- Validate response parsing

#### End-to-End Testing

- Test complete workflows
- Verify specification generation
- Test with various input types

### Prompt Development

Developing effective prompts is critical for getting quality responses from Claude. Follow this iterative process:

1. **Start with a baseline prompt**
   - Define the goal clearly
   - Include structural guidance

2. **Test with diverse inputs**
   - Try different project ideas
   - Include edge cases

3. **Analyze response quality**
   - Check for completeness
   - Verify logical consistency
   - Assess technical accuracy

4. **Refine and iterate**
   - Adjust instructions
   - Add examples where needed
   - Clarify ambiguous sections

5. **Maintain a prompt library**
   - Document successful prompts
   - Track versions and improvements
   - Note specific use cases

## API Integration

### Claude API Integration

The system uses the Anthropic API to access Claude models:

#### Basic Request Example:

```python
import os
import anthropic
from anthropic import Anthropic

# Initialize client with API key
client = Anthropic(api_key=os.environ["CLAUDE_API_KEY"])

# Create a message
response = client.messages.create(
    model=os.environ.get("MODEL_NAME", "claude-3-opus-20240229"),
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Generate a specification for a todo list app"}
    ]
)

# Process the response
specification = response.content[0].text
```

#### Response Handling:

```python
def parse_json_response(response_text):
    """Extract and parse JSON from the Claude response."""
    try:
        # Try to parse the entire response as JSON
        return json.loads(response_text)
    except json.JSONDecodeError:
        # If that fails, try to extract JSON using regex
        import re
        json_match = re.search(r'```json\n([\s\S]*?)\n```', response_text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                return {"error": "Failed to parse JSON from response", "raw_response": response_text}
        else:
            return {"error": "No JSON found in response", "raw_response": response_text}
```

### Environment Variables

The application uses the following environment variables:

- `CLAUDE_API_KEY`: Your Anthropic API key
- `MODEL_NAME`: Claude model to use (default: "claude-3-opus-20240229")
- `OUTPUT_DIR`: Directory for storing specifications (default: "specs")
- `LOG_LEVEL`: Logging level (default: "INFO")

## Deployment Guide

### Local Deployment

1. Complete the setup steps in the Project Setup section
2. Run the appropriate entry point:
   ```bash
   # Command-line interface
   python src/idea_intake.py
   
   # GUI interface
   python src/idea_intake_gui.py
   
   # Simple GUI interface
   python src/idea_intake_gui_simple.py
   ```

### Packaging

To create a distributable package:

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Create the executable:
   ```bash
   pyinstaller --onefile src/idea_intake.py
   ```

3. The executable will be created in the `dist` directory

### Docker Deployment

A Dockerfile is provided for containerized deployment:

1. Build the Docker image:
   ```bash
   docker build -t cursor-ai-agent .
   ```

2. Run the container:
   ```bash
   docker run -it --env-file .env cursor-ai-agent
   ```

## Troubleshooting Guide

### Common Issues

#### Claude API Issues

- **Rate Limiting**: Implement exponential backoff and retry logic
- **Authentication Errors**: Verify API key is correct and has appropriate permissions
- **Timeout Errors**: Consider breaking down requests into smaller chunks

#### Parsing Issues

- **Inconsistent Response Format**: Improve prompt instructions for format consistency
- **JSON Parsing Errors**: Implement fallback parsing mechanisms
- **Missing Fields**: Validate response completeness and request missing information

#### Environment Issues

- **Missing Dependencies**: Verify all requirements are installed
- **Environment Variables**: Check that all required variables are set
- **File Permissions**: Ensure the application has write access to the specs directory

### Debugging Tips

1. **Enable Debug Logging**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Inspect API Requests/Responses**
   ```python
   # Before making API call
   print(f"Sending prompt: {prompt}")
   
   # After receiving response
   print(f"Raw response: {response_text}")
   ```

3. **Step Through Parsing Logic**
   ```python
   # Add breakpoints or print statements to check intermediate results
   parsed_data = parse_json_response(response_text)
   print(f"Parsed data: {json.dumps(parsed_data, indent=2)}")
   ```

## Contributing Guidelines

### Code Style

- Follow PEP 8 style guide
- Use descriptive variable and function names
- Add docstrings to all functions and classes
- Keep functions focused and small (under 50 lines when possible)

### Documentation

- Update documentation when changing functionality
- Document prompt structures and expected responses
- Add examples for complex operations
- Keep the README up to date

### Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Update documentation
5. Submit pull request with clear description
6. Address review comments

### Versioning

The project follows Semantic Versioning (SemVer):

- MAJOR version for incompatible API changes
- MINOR version for backwards-compatible functionality
- PATCH version for backwards-compatible bug fixes 