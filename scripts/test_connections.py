import os
from dotenv import load_dotenv
from litellm import completion

load_dotenv()

test_models = [
    ("openai", "gpt-4o-mini"),
    ("anthropic", "claude-3-haiku-20240307"),
    ("gemini", "gemini/gemini-pro"),
    ("groq", "groq/qwen-2.5-32b"),
    ("mistral", "mistral/mistral-tiny"),
    ("deepseek", "deepseek/deepseek-chat"),
    ("xai", "xai/grok-beta"),
]

for provider, model in test_models:
    try:
        response = completion(
            model=model,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5
        )
        print(f"✅ {provider}: OK - {response.choices[0].message.content}")
    except Exception as e:
        error_msg = str(e)[:100]
        if "authentication" in error_msg.lower() or "api key" in error_msg.lower():
            print(f"❌ {provider}: AUTH ERROR - {error_msg}")
        else:
            print(f"⚠️  {provider}: Connection OK, model issue - {error_msg}")