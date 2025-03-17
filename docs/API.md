# API Documentation

This document provides details on the external APIs used by the AI Creative Collaborator and how they are integrated into the application.

## Mistral API

The AI Creative Collaborator uses the Mistral API for natural language processing, ideation, and specification generation.

### API Setup

1. **Obtain API Key**:
   - Create a Mistral account at [https://console.mistral.ai/](https://console.mistral.ai/)
   - Generate an API key in the console
   - Store your API key securely in the `.env` file

2. **Configure Environment**:
   ```
   MISTRAL_API_KEY=your_api_key_here
   MODEL_NAME=open-mistral-7b
   ```

### API Integration

The application uses the official Mistral Python library:

```python
import os
import mistralai
from mistralai import MistralClient

# Initialize client
client = MistralClient(api_key=os.environ["MISTRAL_API_KEY"])

# Generate a response
response = client.chat(
    model=os.environ.get("MODEL_NAME", "mistral-large-latest"),
    messages=[
        {"role": "user", "content": "Your prompt here"}
    ],
    temperature=0.7
)

# Extract the response text
response_text = response.messages[-1].content
```

### Mistral Models

The application is designed to work with the following Mistral models:

| Model | Description | Best Use Case |
|-------|-------------|--------------|
| mistral-large-latest | Most powerful model with detailed understanding | Complex specifications, detailed technical analysis |
| mistral-medium | Balanced capability and speed | Most general use cases |
| mistral-small | Fastest, most efficient model | Quick responses, simpler tasks |

Configure the model in the `.env` file using the `MODEL_NAME` variable.

### Prompt Engineering

Effective prompt design is critical for getting quality results from Mistral. Our application uses structured prompts with:

1. **Clear Instructions**: Explicit task description and expected output format
2. **Contextual Information**: Background details about the project
3. **Structured Output Guidance**: JSON templates and examples
4. **Follow-up Questions**: Guidance for handling missing information

Example prompt template:

```
You are an expert software architect and specification writer.

I need you to create a detailed specification for the following project idea:
{idea_description}

Please structure your response as a JSON object with the following format:
{json_template}

If any critical information is missing from my description, please identify what's needed.

Here's an example of a good specification:
{example_specification}
```

### Response Handling

The application handles Mistral responses with robust parsing and validation:

```python
def parse_ai_response(response_text):
    """Parse structured data from Mistral response."""
    try:
        # Try to parse the entire response as JSON
        return json.loads(response_text)
    except json.JSONDecodeError:
        # If that fails, try to extract JSON using regex
        import re
        json_match = re.search(r'({[\s\S]*})', response_text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                # Final fallback: try to find JSON-like content
                return extract_structured_data(response_text)
        else:
            return {"error": "Failed to parse response", "raw": response_text}
```

### Error Handling

The application implements comprehensive error handling for the Mistral API:

1. **Rate Limiting**: Exponential backoff for rate limit errors
2. **Timeout Handling**: Retry logic with increasing timeouts
3. **Content Policy**: Detection and handling of content policy violations
4. **Malformed Responses**: Fallback parsing mechanisms
5. **API Errors**: Logging and user-friendly error messages

Example error handling:

```python
def call_mistral_api(prompt, max_retries=3):
    """Call Mistral API with retry logic."""
    for attempt in range(max_retries):
        try:
            response = client.chat(
                model=os.environ.get("MODEL_NAME", "mistral-large-latest"),
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            return response
        except mistralai.MistralAPIError as e:
            if "rate_limit" in str(e).lower():  # Rate limit
                wait_time = (2 ** attempt) + random.random()
                logger.warning(f"Rate limited, waiting {wait_time}s before retry")
                time.sleep(wait_time)
            else:
                logger.error(f"API error: {str(e)}")
                if attempt == max_retries - 1:
                    raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            if attempt == max_retries - 1:
                raise
```

## Cursor Integration

The AI Creative Collaborator is designed to work seamlessly with Cursor for code implementation, but this integration is currently manual through the specification files generated.

Future versions may include direct API integration with Cursor.

## Local API

The application exposes the following internal API endpoints:

### Chat API

- **Endpoint**: `/chat`
- **Method**: `POST`
- **Purpose**: Send messages to Mistral AI
- **Request Body**:
  ```json
  {
    "messages": [
      {"role": "user", "content": "Your message here"}
    ]
  }
  ```
- **Response**:
  ```json
  {
    "response": "AI's response text"
  }
  ```

### PRD Generation API

- **Endpoint**: `/generate-prd`
- **Method**: `POST`
- **Purpose**: Generate a PRD from chat history
- **Request Body**:
  ```json
  {
    "messages": [
      {"role": "user", "content": "Project discussion"},
      {"role": "assistant", "content": "AI's response"}
    ]
  }
  ```
- **Response**: Complete PRD specification in JSON format

### Project Creation API

- **Endpoint**: `/create-project`
- **Method**: `POST`
- **Purpose**: Create a new Cursor project from PRD
- **Request Body**: PRD specification in JSON format
- **Response**:
  ```json
  {
    "project_dir": "Path to created project"
  }
  ```

## API Rate Limits

Be aware of the following rate limits when using the application:

1. **Mistral API**:
   - Requests per minute: Varies by account tier
   - Tokens per minute: Varies by account tier
   - Check the [Mistral documentation](https://docs.mistral.ai/api) for the latest limits

2. **Local API**:
   - Chat timeout: 5 minutes
   - PRD generation timeout: 10 minutes
   - Project creation timeout: 1 minute

## API Security

The application implements the following security measures:

1. **API Key Security**:
   - API keys stored in environment variables, not in code
   - No logging of API keys
   - API keys not exposed to clients

2. **Request Validation**:
   - Input validation for all API requests
   - Sanitization of user inputs
   - Timeouts to prevent hanging requests

3. **Response Security**:
   - No sensitive data in responses
   - Proper error handling to avoid information leakage
   - CORS configured for frontend access only 