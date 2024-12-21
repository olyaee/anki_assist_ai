import tiktoken

# OpenAI pricing per 1K tokens (as of March 2024)
PRICING = {
    "gpt-4o-mini": {
        "input": 0.00015,   # $0.00015 per 1K input tokens
        "output": 0.0006    # $0.0006 per 1K output tokens
    }
}

def num_tokens_from_string(string: str, model: str) -> int:
    """Returns the number of tokens in a text string."""
    # Use cl100k_base encoding for gpt-4o-mini
    encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = len(encoding.encode(string))
    return num_tokens

def calculate_cost(input_text: str, output_text: str, model: str = "gpt-4o-mini") -> dict:
    """
    Calculate the cost of an OpenAI API call.
    
    Args:
        input_text (str): The input prompt text
        output_text (str): The output response text
        model (str): The model used (default: gpt-4o-mini)
        
    Returns:
        dict: Dictionary containing token counts and costs
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