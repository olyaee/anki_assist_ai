import tiktoken

# API pricing per 1K tokens (Official rates as of December 2025)
# Sources:
# - Gemini: https://ai.google.dev/gemini-api/docs/pricing (updated 2025-12-18)
# - OpenAI: Standard published rates
PRICING = {
    # OpenAI models
    "gpt-4o-mini": {
        "input": 0.00015,   # $0.15 per 1M tokens
        "output": 0.0006    # $0.60 per 1M tokens
    },
    # Gemini text models
    "gemini-2.5-flash": {
        "input": 0.00015,   # $0.15 per 1M tokens (text/image/video input)
        "output": 0.0006    # $0.60 per 1M tokens (text output without reasoning)
    },
    "gemini-2.0-flash": {
        "input": 0.00015,
        "output": 0.0006
    },
    # Gemini image generation (Nano Banana)
    "gemini-2.5-flash-image": {
        "input": 0.00015,   # Same as text input
        "output": 0.03      # $30 per 1M tokens (~1290 tokens per image = $0.039/image)
    },
    # Gemini TTS (Text-to-Speech)
    "gemini-2.5-flash-preview-tts": {
        "input": 0.0005,    # $0.50 per 1M tokens
        "output": 0.01      # $10.00 per 1M tokens (audio output)
    }
}

def num_tokens_from_string(string: str, model: str) -> int:
    """
    Returns the number of tokens in a text string.

    For Gemini models: Uses approximation (tiktoken as rough estimate)
    For OpenAI models: Uses tiktoken with cl100k_base encoding

    Note: For accurate Gemini token counts, use client.models.count_tokens()
    This is an approximation for cost estimation purposes.
    """
    # Use cl100k_base encoding as approximation for all models
    # Gemini tokens are roughly similar (1 token ≈ 4 characters)
    encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = len(encoding.encode(string))
    return num_tokens

def calculate_cost(input_text: str, output_text: str, model: str = "gpt-4o-mini") -> dict:
    """
    Calculate the cost of an API call (OpenAI or Gemini).

    Args:
        input_text (str): The input prompt text
        output_text (str): The output response text
        model (str): The model used (e.g., 'gemini-2.5-flash', 'gpt-4o-mini')

    Returns:
        dict: Dictionary containing token counts and costs

    Note: Token counting uses tiktoken approximation for Gemini models.
    For exact Gemini token counts, the API provides client.models.count_tokens().
    """
    if model not in PRICING:
        raise ValueError(f"Unknown model: {model}. Supported models: {list(PRICING.keys())}")
    
    # Calculate tokens
    input_tokens = num_tokens_from_string(input_text, model)
    output_tokens = num_tokens_from_string(output_text, model)
    total_tokens = input_tokens + output_tokens
    
    # Calculate costs
    input_cost = (input_tokens / 1000) * PRICING[model]["input"]
    output_cost = (output_tokens / 1000) * PRICING[model]["output"]
    total_cost = input_cost + output_cost
    
    return {
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "input_cost": round(input_cost, 6),
        "output_cost": round(output_cost, 6),
        "total_cost": round(total_cost, 6)
    } 