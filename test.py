import litellm
import os
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
response = litellm.completion(
    model="gemini/gemini-2.0-flash-lite",
    messages=[{"role": "user", "content": "કેમ છો  મજામાં ?"}],
    api_key=GEMINI_API_KEY,
)

print(response['choices'][0]['message']['content'])