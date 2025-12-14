from openai import OpenAI

# Lazy-load client to allow .env to be loaded first
_client = None

def get_client():
    global _client
    if _client is None:
        _client = OpenAI()
    return _client

def call_llm(system_prompt: str, user_prompt: str, temperature=0):
    client = get_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response.choices[0].message.content
