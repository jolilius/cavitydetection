"""
Generate LLM-based explanations of code optimization strategies.

Provides a reusable module for generating natural-language explanations of
evolved code optimizations by sending the baseline and evolved code to an
OpenAI-compatible LLM API (Ollama endpoint).

Usage:
    from explanation_generator import generate_explanation

    explanation = generate_explanation(
        evolved_code="...",
        baseline_code="...",
        llm_config={
            "primary_model": "qwen2.5-coder:32b",
            "api_base": "http://localhost:11434/v1/",
            "api_key": "ollama",
            "temperature": 0.8,
            "max_tokens": 512,
            "timeout": 30
        },
        explanation_prompt_text="[prompt from explanation_prompt.txt]"
    )

    if explanation:
        print(f"Explanation: {explanation}")
    else:
        print("Failed to generate explanation (timeout or API error)")

Returns:
    - str: A 1-2 sentence explanation of the optimization strategy
    - None: If the LLM call fails (timeout, network error, API error)

Non-blocking: Timeouts and errors are caught and logged, not propagated.
"""

import json
import sys
from typing import Optional

try:
    import requests
except ImportError:
    requests = None  # Graceful fallback; error will be raised at call time


def generate_explanation(
    evolved_code: str,
    baseline_code: str,
    llm_config: dict,
    explanation_prompt_text: str,
) -> Optional[str]:
    """
    Generate a 1-2 sentence explanation of code optimization via LLM.

    Calls an OpenAI-compatible API (e.g., Ollama) to generate natural-language
    descriptions of the optimization strategy applied to the evolved code.

    Args:
        evolved_code (str): Full evolved C program code
        baseline_code (str): Full baseline (reference) C program code
        llm_config (dict): LLM configuration with keys:
            - primary_model (str): Model name (e.g., "qwen2.5-coder:32b")
            - api_base (str): API endpoint (e.g., "http://localhost:11434/v1/")
            - api_key (str): API key for authentication
            - temperature (float): Sampling temperature (0.0-1.0)
            - max_tokens (int): Maximum tokens in response
            - timeout (int): Request timeout in seconds
        explanation_prompt_text (str): System prompt loaded from explanation_prompt.txt

    Returns:
        Optional[str]: A 1-2 sentence explanation, or None if generation fails.

    Side Effects:
        - Prints status messages to stdout (for user visibility)
        - Non-blocking: timeouts and API errors are caught and logged
    """

    # Check if requests library is available
    if requests is None:
        print(
            "Error: requests library not available. Install with: pip3 install requests",
            file=sys.stderr,
        )
        return None

    api_base = llm_config.get("api_base", "http://localhost:11434/v1/")
    api_key = llm_config.get("api_key", "ollama")
    model = llm_config.get("primary_model", "qwen2.5-coder:32b")
    temperature = llm_config.get("temperature", 0.8)
    max_tokens = llm_config.get("max_tokens", 512)
    timeout = llm_config.get("timeout", 30)

    # Construct the user message with code comparison
    user_message = f"""BASELINE CODE:
{baseline_code}

EVOLVED CODE:
{evolved_code}
"""

    # Construct the API request
    endpoint = f"{api_base.rstrip('/')}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": explanation_prompt_text},
            {"role": "user", "content": user_message},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        # Call the LLM API
        print(f"Generating explanation via {model}...", end=" ", file=sys.stderr)
        response = requests.post(
            endpoint, json=payload, headers=headers, timeout=timeout
        )

        # Check for HTTP errors
        if response.status_code >= 500:
            print(f"server error ({response.status_code}), skipping", file=sys.stderr)
            return None

        if response.status_code >= 400:
            print(f"client error ({response.status_code}), skipping", file=sys.stderr)
            return None

        # Parse response
        data = response.json()
        choices = data.get("choices", [])

        if not choices:
            print("no response content, skipping", file=sys.stderr)
            return None

        explanation = choices[0].get("message", {}).get("content", "").strip()

        if not explanation:
            print("empty response, skipping", file=sys.stderr)
            return None

        print("OK", file=sys.stderr)
        return explanation

    except requests.exceptions.Timeout:
        print("timeout, skipping", file=sys.stderr)
        return None

    except requests.exceptions.ConnectionError:
        print("connection error, skipping", file=sys.stderr)
        return None

    except requests.exceptions.RequestException as e:
        print(f"request error ({type(e).__name__}), skipping", file=sys.stderr)
        return None

    except json.JSONDecodeError:
        print("malformed response, skipping", file=sys.stderr)
        return None

    except Exception as e:
        print(f"unexpected error ({type(e).__name__}), skipping", file=sys.stderr)
        return None


if __name__ == "__main__":
    import yaml

    # Load configuration
    try:
        with open("config.yaml") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print("Error: config.yaml not found", file=sys.stderr)
        sys.exit(1)

    # Load prompt
    try:
        with open("explanation_prompt.txt") as f:
            prompt_text = f.read()
    except FileNotFoundError:
        print("Error: explanation_prompt.txt not found", file=sys.stderr)
        sys.exit(1)

    # Load baseline code
    try:
        with open("initial_program.c") as f:
            baseline = f.read()
    except FileNotFoundError:
        print("Error: initial_program.c not found", file=sys.stderr)
        sys.exit(1)

    # Create a minimal evolved version for testing
    # (just a cosmetic change to demonstrate the API)
    evolved = baseline.replace(
        "void run_pipeline(unsigned char image_in[N][M], unsigned char image_out[N][M])",
        "void run_pipeline(unsigned char image_in[N][M], unsigned char image_out[N][M]) // optimized",
    )

    # Generate explanation
    llm_config = config.get("llm", {})
    explanation = generate_explanation(evolved, baseline, llm_config, prompt_text)

    if explanation:
        print(f"\nGenerated explanation:\n{explanation}")
    else:
        print("\nFailed to generate explanation")
        sys.exit(1)
