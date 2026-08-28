"""
List all available models from the LLM provider.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def main():
    provider = "groq"
    api_key = os.getenv(f"{provider.upper()}_API_KEY")
    base_url = os.getenv(f"{provider.upper()}_BASE_URL")

    if not api_key:
        print(f"Error: {provider.upper()}_API_KEY not found in .env")
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url=base_url)

    print(f"Available models on {provider}:")
    print("=" * 60)

    models = client.models.list()
    for model in models.data:
        print(f"  - {model.id}")

if __name__ == "__main__":
    main()