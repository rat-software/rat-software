import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://api.studio.nebius.com/v1/",
    api_key=os.environ.get("NEBIUS_API_KEY")

)

response = client.chat.completions.create(
    model="mistralai/Devstral-Small-2505",
    max_tokens=512,
    temperature=0.5,
    top_p=0.9,
    extra_body={
        "top_k": 50
    },
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": """good day"""
                }
            ]
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": """ Good day to you too! How can I assist you today?"""
                }
            ]
        }
    ]
)

print(response.to_json())