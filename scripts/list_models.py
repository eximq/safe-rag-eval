"""
List all available models from the LLM provider.

Usage:
    python scripts/list_models.py groq
    python scripts/list_models.py gemini
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Provider configuration
PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "env_key": "GROQ_API_KEY",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "env_key": "GEMINI_API_KEY",
    },
}


def main():
    # Get provider from command line
    if len(sys.argv) < 2:
        print("Usage: python scripts/list_models.py <provider>")
        print(f"Available providers: {', '.join(PROVIDERS.keys())}")
        sys.exit(1)
    
    provider = sys.argv[1].lower()
    
    if provider not in PROVIDERS:
        print(f"Unknown provider: {provider}")
        print(f"Available providers: {', '.join(PROVIDERS.keys())}")
        sys.exit(1)
    
    config = PROVIDERS[provider]
    api_key = os.getenv(config["env_key"])

    if not api_key:
        print(f"Error: {config['env_key']} not found in .env")
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url=config["base_url"])

    print(f"Available models on {provider}:")
    print("=" * 60)

    try:
        models = client.models.list()
        for model in models.data:
            print(f"  - {model.id}")
    except Exception as e:
        print(f"Error listing models: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()