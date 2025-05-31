# Google LLM Provider Configuration

This document describes how to configure and use the Google Gemini models with SwarmDev.

## Overview

The Google provider gives you access to Google's Gemini models, including:
- **Gemini 2.0 Flash** - Latest multimodal model with code execution
- **Gemini 1.5 Pro** - High-performance model with 2M token context
- **Gemini 1.5 Flash** - Fast, efficient model for most tasks

## Setup

### 1. Install Dependencies

```bash
pip install google-genai
```

### 2. Get API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Set the environment variable:

```bash
export GOOGLE_API_KEY="your-api-key-here"
```

Or add to your `.env` file:
```
GOOGLE_API_KEY=your-api-key-here
```

## Usage

### Command Line

Use Google Gemini models via the CLI:

```bash
# Use default Gemini 2.0 Flash
swarmdev build --goal goal.txt --llm-provider google

# Specify a specific model
swarmdev build --goal goal.txt --llm-provider google --llm-model gemini-1.5-pro-001

# Use with assistant
swarmdev assistant --llm-provider google --llm-model gemini-2.0-flash-001
```

### Programmatic Usage

```python
from swarmdev.utils.llm_provider import GoogleProvider

# Initialize provider
provider = GoogleProvider(
    api_key="your-api-key",
    model="gemini-2.0-flash-001"
)

# Generate text
response = provider.generate_text("Explain quantum computing")

# Chat conversation
messages = [
    {"role": "user", "content": "Hello!"},
    {"role": "agent", "content": "Hi! How can I help?"},
    {"role": "user", "content": "What's the weather like?"}
]
response = provider.generate_chat(messages)
```

## Available Models

| Model | Description | Context Length | Best For |
|-------|-------------|----------------|----------|
| `gemini-2.0-flash-001` | Latest model with code execution | 1M tokens | Development, coding, multimodal |
| `gemini-1.5-pro-001` | High-performance model | 2M tokens | Complex reasoning, long documents |
| `gemini-1.5-flash-001` | Fast, efficient model | 1M tokens | Quick tasks, conversations |

## Features

### Multimodal Support

Gemini models support images, video, and audio inputs:

```python
# Example with image (when using SDK directly)
import google.genai as genai

model = genai.GenerativeModel("gemini-2.0-flash-001")
response = model.generate_content([
    "What's in this image?",
    {"mime_type": "image/jpeg", "data": image_bytes}
])
```

### Function Calling

Gemini models support function calling for tool use:

```python
# Function calling is automatically supported
# through the SwarmDev agent framework
```

### Code Execution

Gemini 2.0 models can execute Python code:

```python
# This happens automatically when the model needs to run code
# during development tasks
```

## Configuration Options

### Generation Parameters

```python
provider = GoogleProvider(
    model="gemini-2.0-flash-001",
    temperature=0.7,      # Creativity (0.0-1.0)
    top_p=0.9,           # Nucleus sampling
    top_k=40,            # Top-k sampling
    max_tokens=1000      # Response length
)
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Your Google API key | Required |
| `GOOGLE_MODEL` | Default model to use | `gemini-2.0-flash-001` |

## Pricing

Google offers competitive pricing:
- Text generation: ~$0.0001 per 1K characters
- Multimodal: Varies by input type
- See [Google AI Pricing](https://ai.google.dev/pricing) for details

## Troubleshooting

### Common Issues

1. **API Key Error**
   ```
   ValueError: Google API key required
   ```
   Solution: Set `GOOGLE_API_KEY` environment variable

2. **Import Error**
   ```
   ImportError: Google GenAI package not installed
   ```
   Solution: `pip install google-genai`

3. **Rate Limiting**
   ```
   429 Too Many Requests
   ```
   Solution: Automatic retry with exponential backoff is built-in

### Debugging

Enable verbose logging to see API calls:

```bash
swarmdev build --goal goal.txt --llm-provider google --verbose
```

## Comparison with Other Providers

| Feature | Google Gemini | OpenAI GPT | Anthropic Claude |
|---------|---------------|------------|------------------|
| Multimodal | Yes (Native) | Yes (Limited) | Yes (Limited) |
| Code Execution | Yes (Gemini 2.0) | No | No |
| Context Length | Up to 2M | Up to 128k | Up to 200k |
| Pricing | Very competitive | Moderate | Higher |
| Speed | Very fast | Fast | Moderate |

## Best Practices

1. **Model Selection**
   - Use Gemini 2.0 Flash for development projects
   - Use Gemini 1.5 Pro for complex analysis
   - Use Gemini 1.5 Flash for quick iterations

2. **Context Management**
   - Take advantage of long context for large codebases
   - Include relevant documentation in prompts

3. **Multimodal Usage**
   - Include screenshots for UI/UX development
   - Use diagrams for architecture discussions

4. **Cost Optimization**
   - Use appropriate model for task complexity
   - Monitor usage through Google AI Studio

## Examples

### Development Project

```bash
# Create a web application
swarmdev build --goal "Build a React todo app" --llm-provider google --llm-model gemini-2.0-flash-001
```

### Research Project

```bash
# Analyze a large codebase
swarmdev build --goal "Analyze security vulnerabilities" --llm-provider google --llm-model gemini-1.5-pro-001
```

### Quick Iteration

```bash
# Fast prototyping
swarmdev assistant --llm-provider google --llm-model gemini-1.5-flash-001
```

For more information, see the [Google AI documentation](https://ai.google.dev/docs). 