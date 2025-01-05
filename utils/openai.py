import os
from openai import AzureOpenAI
from dotenv import load_dotenv


load_dotenv()
endpoint = os.getenv(
    "AZURE_OPENAI_ENDPOINT", "https://eastus.api.cognitive.microsoft.com/"
)
deployment = os.getenv("DEPLOYMENT_NAME", "gpt-4o")
subscription_key = os.getenv(
    "AZURE_OPENAI_API_KEY", "REPLACE_WITH_YOUR_KEY_VALUE_HERE"
)

# Initialize Azure OpenAI client with key-based authentication
client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=subscription_key,
    api_version="2024-05-01-preview",
)


# Define a function that takes in question, context and returns the answer
def get_answer(question, context):

    completion = client.chat.completions.create(
        model=deployment,
        messages=prepare_chat(question, context),
        max_tokens=800,
        temperature=0.7,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
        stream=False,
    )
    return completion.to_json()


# Prepare the chat prompt
def prepare_chat(question, content):
    return [
        {"role": "system", "content": [{"type": "text", "text": content}]},
        {"role": "user", "content": [{"type": "text", "text": question}]},
    ]
