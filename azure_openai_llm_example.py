from openai import AzureOpenAI
import os

azure_key = os.getenv("AZURE_OPEN_AI_KEY")
azure_endpoint = os.getenv("AZURE_OPEN_AI_ENDPOINT")

client = AzureOpenAI(
  api_key = azure_key,  # Put your DIAL API Key here
  api_version = "2024-02-01",
  azure_endpoint = azure_endpoint
)

deployment_name = "gpt-5.4-2026-03-05-reasoning" #gpt-5.1-codex-mini-2025-11-13


print(client.chat.completions.create(
  model=deployment_name,
  temperature=0,
  messages=[
      {
        "role": "user",
        "content": "how are you?",
      },
  ],
))
