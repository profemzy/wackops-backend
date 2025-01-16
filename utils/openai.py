import os
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from openai import AzureOpenAI
from openai.types.chat import ChatCompletion
from tenacity import retry
from tenacity import stop_after_attempt
from tenacity import wait_exponential


class AzureOpenAIClient:
    """A client for interacting with Azure OpenAI services."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        deployment: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        Initialize the Azure OpenAI client.

        Args:
            endpoint: Azure OpenAI endpoint URL. Defaults to env variable.
            deployment: Model deployment name. Defaults to env variable.
            api_key: Azure OpenAI API key. Defaults to environment variable.
        """
        self.endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment = deployment or os.getenv("DEPLOYMENT_NAME", "gpt-4")
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("Azure OpenAI API key must be provided")

        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version="2024-05-01-preview",
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry_error_callback=lambda retry_state: None,
    )
    def get_answer(
        self,
        question: str,
        context: str,
        max_tokens: int = 800,
        temperature: float = 0.7,
        top_p: float = 0.95,
        frequency_penalty: float = 0,
        presence_penalty: float = 0,
        stop: Optional[Union[str, List[str]]] = None,
        stream: bool = False,
    ) -> Optional[Dict]:
        """
        Get an answer from the Azure OpenAI service.

        Args:
            question: The user's question
            context: The system context/prompt
            max_tokens: Maximum number of tokens in the response
            temperature: Sampling temperature (0-1)
            top_p: Nucleus sampling parameter
            frequency_penalty: Frequency penalty for token selection
            presence_penalty: Presence penalty for token selection
            stop: Optional stop sequences
            stream: Whether to stream the response

        Returns:
            Completion response as a dictionary, or None if the request fails

        Raises:
            openai.APIError: If the API request fails after retries
        """
        try:
            completion: ChatCompletion = self.client.chat.completions.create(
                model=self.deployment,
                messages=self._prepare_chat(question, context),
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                stop=stop,
                stream=stream,
            )
            return completion.model_dump()

        except Exception as e:
            print(f"Error getting completion: {str(e)}")
            return None

    @staticmethod
    def _prepare_chat(
        question: str, context: str
    ) -> List[Dict[str, Union[str, List[Dict[str, str]]]]]:
        """
        Prepare the chat messages for the API request.

        Args:
            question: The user's question
            context: The system context/prompt

        Returns:
            A list of message dictionaries
        """
        return [
            {"role": "system", "content": [{"type": "text", "text": context}]},
            {"role": "user", "content": [{"type": "text", "text": question}]},
        ]
