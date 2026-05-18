from openai import OpenAI

client = OpenAI(
    api_key="EMPTY",
    base_url="http://localhost:11434/v1"
)

response = client.chat.completions.create(
    model="qwen3.5:2b",
    messages=[
        {"role": "user", "content": "你好"}
    ]
)

print(response.choices[0].message.content)