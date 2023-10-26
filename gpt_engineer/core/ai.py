"""
This module provides an interface to interact with AI models.
It leverages the OpenAI GPT models and allows for integration with Azure-based instances of the same.
The AI class encapsulates the chat functionalities, allowing to start, advance, and manage a conversation with the model.

Key Features:
- Integration with Azure-based OpenAI instances through the LangChain AzureChatOpenAI class.
- Token usage logging to monitor the number of tokens consumed during a conversation.
- Seamless fallback to default models in case the desired model is unavailable.
- Serialization and deserialization of chat messages for easier transmission and storage.
- Token usage calculation and logging for monitoring and optimization purposes.

Classes:
- AI: Main class providing chat functionalities. It provides methods to start and advance a conversation, serialize and deserialize messages, and calculate and log token usage. The start method in particular is used to initiate a conversation with a system and user message, preparing it for interaction with the language model.

Dependencies:
- langchain: For chat models and message schemas.
- openai: For the core GPT models interaction.
- backoff: For handling rate limits and retries.
- typing: For type hints.

For more specific details, refer to the docstrings within each class and function.
"""

from __future__ import annotations

import json
import logging
import os

from typing import List, Optional, Union

import backoff
import openai

from gpt_engineer.core.token_usage import TokenUsageLog

from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI
from langchain.chat_models.base import BaseChatModel
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    messages_from_dict,
    messages_to_dict,
)

# Type hint for a chat message
Message = Union[AIMessage, HumanMessage, SystemMessage]

# Set up logging
logger = logging.getLogger(__name__)


class AI:
    """
    A class to interface with a language model for chat-based interactions.

    This class provides methods to initiate and maintain conversations using
    a specified language model. It handles token counting, message creation,
    serialization and deserialization of chat messages, and interfaces with
    the language model to get AI-generated responses. It also provides methods
    to calculate and log the number of tokens used in a conversation, which can
    be useful for monitoring and optimization purposes.

    Attributes
    ----------
    temperature : float
        The temperature setting for the model, affecting the randomness of the output.
    azure_endpoint : str
        The Azure endpoint URL, if applicable.
    model_name : str
        The name of the model being used.
    llm : Any
        The chat model instance.
    token_usage_log : Any
        The token usage log used to store cumulitive tokens used during the lifetime of the ai class

    Methods
    -------
    start(system, user, step_name) -> List[Message]:
        Start the conversation with a system and user message. This method initializes the conversation and prepares it for interaction with the language model.
    next(messages, prompt, step_name) -> List[Message]:
        Advance the conversation by interacting with the language model. This method takes the current conversation, adds a new user message (if provided), and gets a response from the language model.
    backoff_inference(messages, callbacks) -> Any:
        Interact with the model using an exponential backoff strategy in case of rate limits. This method handles potential rate limit errors from the OpenAI API by implementing an exponential backoff strategy.
    serialize_messages(messages) -> str:
        Serialize a list of messages to a JSON string. This method is useful for storing or transmitting the conversation in a compact format.
    deserialize_messages(jsondictstr) -> List[Message]:
        Deserialize a JSON string into a list of messages. This method is useful for loading a conversation from a stored or transmitted format.
    update_token_usage_log(messages, answer, step_name) -> None:
        Update the token usage log with the number of tokens used in the latest interaction. This method is useful for monitoring and optimizing token usage.
    format_token_usage_log() -> str:
        Format the token usage log as a string for easy viewing. This method is useful for displaying the token usage log in a human-readable format.
    usage_cost(messages) -> int:
        Calculate the cost in tokens of a list of messages. This method is useful for estimating the token usage of a conversation without making an API call.
    num_tokens(message) -> int:
        Calculate the number of tokens in a message. This method is useful for estimating the token usage of a single message.
    num_tokens_from_messages(messages) -> int:
        Calculate the total number of tokens in a list of messages. This method is useful for estimating the token usage of a conversation.

    """

    def __init__(self, model_name="gpt-4", temperature=0.1, azure_endpoint=""):
        """
        Initialize the AI class.

        Parameters
        ----------
        model_name : str, optional
            The name of the model to use, by default "gpt-4".
        temperature : float, optional
            The temperature to use for the model, by default 0.1.
        """
        self.temperature = temperature
        self.azure_endpoint = azure_endpoint
        self.model_name = self._check_model_access_and_fallback(model_name)

        self.llm = self._create_chat_model()
        self.token_usage_log = TokenUsageLog(model_name)

        logger.debug(f"Using model {self.model_name}")

    def start(self, system: str, user: str, step_name: str) -> List[Message]:
        """
        Start the conversation with a system message and a user message. This method initializes the conversation and prepares it for interaction with the language model. It takes a system message and a user message as input, and returns a list of messages ready for interaction with the language model. The system message typically sets the behavior of the assistant, while the user message is the user's input to the assistant. The step_name parameter is used for logging purposes to identify the step in the conversation.

        Parameters
        ----------
        system : str
            The content of the system message, which typically sets the behavior of the assistant.
        user : str
            The content of the user message, which is the user's input to the assistant.
        step_name : str
            The name of the step, used for logging purposes to identify the step in the conversation.

        Returns
        -------
        List[Message]
            The list of messages in the conversation, ready for interaction with the language model.
        """

        messages: List[Message] = [
            SystemMessage(content=system),
            HumanMessage(content=user),
        ]
        return self.next(messages, step_name=step_name)

    def next(
        self,
        messages: List[Message],
        prompt: Optional[str] = None,
        *,
        step_name: str,
    ) -> List[Message]:
        """
        Advance the conversation by interacting with the language model. This method takes the current conversation, represented by the 'messages' parameter, and optionally adds a new user message, represented by the 'prompt' parameter. It then gets a response from the language model and adds it to the conversation. The updated conversation, which includes the new AI message, is returned.

        Parameters
        ----------
        messages : List[Message]
            The current conversation, represented as a list of messages.
        prompt : Optional[str], optional
            An optional user message to add to the conversation. If provided, this message is added to the conversation before getting a response from the language model.
        step_name : str
            The name of the step. This is used for logging purposes to identify the step in the conversation.

        Returns
        -------
        List[Message]
            The updated conversation, represented as a list of messages. This includes the new AI message generated by the language model.

        This method interacts with the language model through the 'llm' attribute of the AI class. It also updates the token usage log through the 'token_usage_log' attribute.
        """
        """
        Advances the conversation by sending message history
        to LLM and updating with the response.
        """
        if prompt:
            messages.append(HumanMessage(content=prompt))

        logger.debug(f"Creating a new chat completion: {messages}")

        callbacks = [StreamingStdOutCallbackHandler()]
        response = self.backoff_inference(messages, callbacks)

        self.token_usage_log.update_log(
            messages=messages, answer=response.content, step_name=step_name
        )
        messages.append(response)
        logger.debug(f"Chat completion finished: {messages}")

        return messages

    @backoff.on_exception(
        backoff.expo, openai.error.RateLimitError, max_tries=7, max_time=45
    )
    def backoff_inference(self, messages, callbacks):
        """
        Perform inference using the language model while implementing an exponential backoff strategy.

        This function will retry the inference in case of a rate limit error from the OpenAI API.
        It uses an exponential backoff strategy, meaning the wait time between retries increases
        exponentially. The function will attempt to retry up to 7 times within a span of 45 seconds.

        Parameters
        ----------
        messages : List[Message]
            A list of chat messages which will be passed to the language model for processing.

        callbacks : List[Callable]
            A list of callback functions that are triggered after each inference. These functions
            can be used for logging, monitoring, or other auxiliary tasks.

        Returns
        -------
        Any
            The output from the language model after processing the provided messages.

        Raises
        ------
        openai.error.RateLimitError
            If the number of retries exceeds the maximum or if the rate limit persists beyond the
            allotted time, the function will ultimately raise a RateLimitError.

        Example
        -------
        >>> messages = [SystemMessage(content="Hello"), HumanMessage(content="How's the weather?")]
        >>> callbacks = [some_logging_callback]
        >>> response = backoff_inference(messages, callbacks)
        """
        return self.llm(messages, callbacks=callbacks)  # type: ignore

    @staticmethod
    def serialize_messages(messages: List[Message]) -> str:
        """
        Serialize a list of messages to a JSON string.

        Parameters
        ----------
        messages : List[Message]
            The list of messages to serialize.

        Returns
        -------
        str
            The serialized messages as a JSON string.
        """
        return json.dumps(messages_to_dict(messages))

    @staticmethod
    def deserialize_messages(jsondictstr: str) -> List[Message]:
        """
        Deserialize a JSON string into a list of messages. This method takes a JSON string representing a list of messages, and returns the corresponding list of Message objects. It is useful for loading a conversation from a stored or transmitted format.

        Parameters
        ----------
        jsondictstr : str
            The JSON string to deserialize.

        Returns
        -------
        List[Message]
            The deserialized list of messages.
        """
        data = json.loads(jsondictstr)
        # Modify implicit is_chunk property to ALWAYS false
        # since Langchain's Message schema is stricter
        prevalidated_data = [
            {**item, "data": {**item["data"], "is_chunk": False}} for item in data
        ]
        return list(messages_from_dict(prevalidated_data))  # type: ignore

    def _check_model_access_and_fallback(self, model_name) -> str:
        """
        Retrieve the specified model, or fallback to "gpt-3.5-turbo" if the model is not available.

        Parameters
        ----------
        model : str
            The name of the model to retrieve.

        Returns
        -------
        str
            The name of the retrieved model, or "gpt-3.5-turbo" if the specified model is not available.
        """
        try:
            openai.Model.retrieve(model_name)
        except openai.InvalidRequestError:
            print(
                f"Model {model_name} not available for provided API key. Reverting "
                "to gpt-3.5-turbo. Sign up for the GPT-4 wait list here: "
                "https://openai.com/waitlist/gpt-4-api\n"
            )
            return "gpt-3.5-turbo"

        return model_name

    def _create_chat_model(self) -> BaseChatModel:
        """
        Create a chat model with the specified model name and temperature.

        Parameters
        ----------
        model : str
            The name of the model to create.
        temperature : float
            The temperature to use for the model.

        Returns
        -------
        BaseChatModel
            The created chat model.
        """
        if self.azure_endpoint:
            return AzureChatOpenAI(
                openai_api_base=self.azure_endpoint,
                openai_api_version=os.getenv("OPENAI_API_VERSION", "2023-05-15"),
                deployment_name=self.model_name,
                openai_api_type="azure",
                streaming=True,
            )

        return ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            streaming=True,
            client=openai.ChatCompletion,
        )


def serialize_messages(messages: List[Message]) -> str:
    """
    Serialize a list of chat messages into a JSON-formatted string.

    This function acts as a wrapper around the `AI.serialize_messages` method,
    providing a more straightforward access to message serialization.

    Parameters
    ----------
    messages : List[Message]
        A list of chat messages to be serialized. Each message should be an
        instance of the `Message` type (which includes `AIMessage`, `HumanMessage`,
        and `SystemMessage`).

    Returns
    -------
    str
        A JSON-formatted string representation of the input messages.

    Example
    -------
    >>> msgs = [SystemMessage(content="Hello"), HumanMessage(content="Hi, AI!")]
    >>> serialize_messages(msgs)
    '[{"type": "system", "content": "Hello"}, {"type": "human", "content": "Hi, AI!"}]'
    """
    return AI.serialize_messages(messages)
