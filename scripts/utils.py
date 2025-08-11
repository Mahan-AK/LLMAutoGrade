def calculate_gemini_cost(
    model: str,
    prompt_token_count: int,
    candidates_token_count: int,
    thinking_mode: bool = False
) -> float:
    """
    Calculate the cost of a Gemini 2.5 API request.

    Args:
        model (str): 'flash' or 'pro'
        prompt_token_count (int): Number of input tokens (prompt)
        candidates_token_count (int): Number of output tokens (completion)
        thinking_mode (bool): If True, use 'thinking' pricing for Flash (ignored for Pro)

    Returns:
        float: Total cost in USD for the request
    """
    # Pricing per 1M tokens (USD)
    if model == "flash":
        input_price = 0.15
        output_price = 3.50 if thinking_mode else 0.60
    elif model == "pro":
        input_price = 1.25
        output_price = 10.00
    else:
        raise ValueError("Model must be 'flash' or 'pro'.")

    # Calculate costs
    input_cost = (prompt_token_count / 1_000_000) * input_price
    output_cost = (candidates_token_count / 1_000_000) * output_price
    total_cost = input_cost + output_cost
    return total_cost
