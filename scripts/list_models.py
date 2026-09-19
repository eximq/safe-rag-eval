"""
List all available models from LLM providers.

Usage:
    python scripts/list_models.py              # Show all providers
    python scripts/list_models.py groq         # Show specific provider
    python scripts/list_models.py gemini       # Show specific provider
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


def list_models_for_provider(provider_name: str, config: dict) -> list:
    """List available models for a specific provider. Returns list of model IDs."""
    api_key = os.getenv(config["env_key"])

    if not api_key:
        print(f"  ⚠️ {config['env_key']} not found in .env")
        return []

    try:
        client = OpenAI(api_key=api_key, base_url=config["base_url"])
        models = client.models.list()
        model_ids = [model.id for model in models.data]
        return model_ids
    except Exception as e:
        print(f"  ⚠️ Error: {e}")
        return []


def main():
    # Determine which providers to list
    if len(sys.argv) >= 2:
        # Specific provider requested
        provider = sys.argv[1].lower()
        
        if provider not in PROVIDERS:
            print(f"❌ Unknown provider: {provider}")
            print(f"Available providers: {', '.join(PROVIDERS.keys())}")
            sys.exit(1)
        
        providers_to_list = {provider: PROVIDERS[provider]}
    else:
        # List all providers
        providers_to_list = PROVIDERS
    
    # Header
    print("=" * 70)
    print("🤖 Available LLM Models")
    print("=" * 70)
    
    total_models = 0
    
    for provider_name, config in providers_to_list.items():
        print(f"\n📡 {provider_name.upper()}")
        print("-" * 70)
        
        models = list_models_for_provider(provider_name, config)
        
        if models:
            # Sort models alphabetically
            for model_id in sorted(models):
                print(f"  • {model_id}")
            total_models += len(models)
            print(f"\n  Total: {len(models)} models")
        else:
            print("  (no models available)")
    
    # Footer
    print("\n" + "=" * 70)
    print(f"📊 Total across all providers: {total_models} models")
    print("=" * 70)


if __name__ == "__main__":
    main()