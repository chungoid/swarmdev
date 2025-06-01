# Model-Aware Configuration System

## Overview

SwarmDev now uses an intelligent model-aware configuration system that automatically translates parameters based on the specific LLM model being used. This eliminates the need for users to manage different parameter sets for different models.

## How It Works

### Single Configuration, Multiple Models

Users continue to use the same configuration format:

```json
{
  "llm": {
    "provider": "openai",
    "model": "o1-mini",
    "temperature": 0.7,
    "max_tokens": 4000
  }
}
```

The system automatically translates these parameters to what each model expects:

### OpenAI Model Families

#### Reasoning/Thinking Models (o1, o3, o4 series)
- Includes: o1-preview, o1-mini, o1-pro, o3-mini, o3-preview, o4-mini, o4-preview, etc.
- `max_tokens` → `max_completion_tokens` (for reasoning tasks)
- Default: 25,000 tokens (much higher for reasoning)
- **Temperature: ONLY supports 1.0** - any other value causes errors, so user temperature settings are ignored
- Automatically excludes unsupported parameters (top_p, frequency_penalty, etc.)

#### GPT-4 and GPT-3.5 Models  
- Uses standard parameter set
- `max_tokens` stays as `max_tokens`
- Full parameter support (temperature, top_p, frequency_penalty, etc.)

### Anthropic Model Families

#### Claude 4 Models
- Opus 4: Up to 32k output tokens
- Sonnet 4: Up to 64k output tokens  
- Enhanced capabilities detection

#### Claude 3.7 Models
- Up to 64k output tokens
- Extended thinking capabilities

#### Claude 3.5 Models
- Up to 8192 output tokens
- Standard capabilities

#### Claude 3 Models
- Up to 4096 output tokens
- Base model capabilities

### Google Model Families

#### Gemini 2.0 Models
- `max_tokens` → `max_output_tokens`
- Enhanced parameter handling
- Higher output limits (8192 default)

#### Gemini 1.5 Models
- Large context windows
- Good performance characteristics
- 8192 token output

#### Gemini 1.0 Models
- Standard capabilities
- Lower output limits (2048 default)

## Benefits

### 1. Zero Configuration Complexity
Users don't need to know model-specific parameter names or limits. The same config works across all models.

### 2. Automatic Optimization
Each model gets optimal parameter settings based on its capabilities and limits.

### 3. Future-Proof
New models are automatically supported by adding their parameter mappings to the providers.

### 4. Backward Compatible
Existing configurations continue to work without changes.

## Examples

### Using Reasoning Models
```json
{
  "llm": {
    "provider": "openai", 
    "model": "o1-mini",
    "max_tokens": 10000,
    "temperature": 0.7
  }
}
```

Automatically becomes:
```python
{
  "model": "o1-mini",
  "max_completion_tokens": 10000
  # temperature omitted - reasoning models only support 1.0, so user setting ignored
}
```

*This applies to all reasoning models: o1-preview, o1-mini, o1-pro, o3-mini, o3-preview, o4-mini, o4-preview, etc.*

### Using Claude 3.5 Sonnet
```json
{
  "llm": {
    "provider": "anthropic",
    "model": "claude-3-5-sonnet-20241022", 
    "max_tokens": 6000
  }
}
```

Automatically becomes:
```python
{
  "model": "claude-3-5-sonnet-20241022",
  "max_tokens": 6000,  # Capped at 8192 for Claude 3.5
  "temperature": 0.7,
  "top_p": 1.0
}
```

### Using Gemini 2.0
```json
{
  "llm": {
    "provider": "google",
    "model": "gemini-2.0-flash-001",
    "max_tokens": 5000
  }
}
```

Automatically becomes:
```python
{
  "temperature": 0.7,
  "max_output_tokens": 5000,  # Google uses different parameter name
  "top_p": 0.95,
  "top_k": 40
}
```

## Error Handling

The system includes intelligent fallbacks:

1. **Parameter Compatibility**: Automatically excludes parameters not supported by specific models
2. **Token Limits**: Enforces model-specific maximum token limits
3. **Graceful Degradation**: Falls back to compatible parameters if model doesn't support advanced features

## Implementation Details

Each provider now includes:

- **Model Detection**: Identifies model family and capabilities
- **Parameter Mapping**: Translates generic parameters to model-specific ones  
- **Limit Enforcement**: Ensures parameters stay within model limits
- **Fallback Logic**: Handles edge cases gracefully

This approach ensures users get the best performance from each model without configuration complexity. 