from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, TypeVar

from pydantic import BaseModel

TSchema = TypeVar("TSchema", bound=BaseModel)


class LogLevel(str, Enum):
    """Logging levels compatible with Python's logging module."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LLMInterface(ABC):
    """Abstract interface for Large Language Model (LLM) interactions across different frameworks.

    This interface provides a unified way to interact with various LLM implementations,
    supporting both text generation and structured output generation. It includes both
    synchronous and asynchronous methods to accommodate different use cases and frameworks.
    """

    @abstractmethod
    def invoke(self, prompt: str) -> str:
        """Invoke the LLM with a text prompt and return the generated response.

        Args:
            prompt: The input text prompt to send to the LLM.

        Returns:
            The generated text response from the LLM.

        Raises:
            Exception: If the LLM invocation fails or times out.
        """
        pass

    @abstractmethod
    async def ainvoke(self, prompt: str) -> str:
        """Asynchronously invoke the LLM with a text prompt and return the generated response.

        Args:
            prompt: The input text prompt to send to the LLM.

        Returns:
            The generated text response from the LLM.

        Raises:
            Exception: If the LLM invocation fails or times out.
        """
        pass

    @abstractmethod
    def invoke_schema(self, prompt: str, schema: type[TSchema]) -> TSchema:
        """Invoke the LLM with a prompt and return a structured response matching the provided schema.

        This method enforces that the LLM response conforms to the specified Pydantic model schema,
        enabling reliable extraction of structured data from natural language responses.

        Args:
            prompt: The input text prompt to send to the LLM.
            schema: A Pydantic model class that defines the expected structure of the response.

        Returns:
            An instance of the schema class populated with data from the LLM response.

        Raises:
            ValidationError: If the LLM response cannot be parsed into the specified schema.
            Exception: If the LLM invocation fails or times out.
        """
        pass

    @abstractmethod
    async def ainvoke_schema(self, prompt: str, schema: type[TSchema]) -> TSchema:
        """Asynchronously invoke the LLM with a prompt and return a structured response.

        This method enforces that the LLM response conforms to the specified Pydantic model schema,
        enabling reliable extraction of structured data from natural language responses.

        Args:
            prompt: The input text prompt to send to the LLM.
            schema: A Pydantic model class that defines the expected structure of the response.

        Returns:
            An instance of the schema class populated with data from the LLM response.

        Raises:
            ValidationError: If the LLM response cannot be parsed into the specified schema.
            Exception: If the LLM invocation fails or times out.
        """
        pass


class EmbeddingInterface(ABC):
    """Abstract interface for Language Model embedding and text encoding operations.

    This interface provides methods for converting text into vector representations
    (embeddings) that can be used for similarity search, clustering, and other
    machine learning tasks. Supports both single text and batch processing.
    """

    @abstractmethod
    def encode(self, text: str) -> list[float]:
        """Encode a single text string into a vector representation.

        Args:
            text: The input text to encode into a vector.

        Returns:
            A list of floats representing the text as a vector embedding.

        Raises:
            Exception: If the encoding process fails or the model is unavailable.
        """
        pass

    @abstractmethod
    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        """Encode multiple text strings into vector representations in a single batch.

        Batch processing is typically more efficient than encoding texts individually,
        especially when dealing with large numbers of texts.

        Args:
            texts: A list of text strings to encode into vectors.

        Returns:
            A list of vector embeddings, where each embedding is a list of floats.
            The order of embeddings corresponds to the order of input texts.

        Raises:
            Exception: If the encoding process fails or the model is unavailable.
        """
        pass


class MetricsInterface(ABC):
    """Abstract interface for collecting and recording performance metrics.

    This interface provides a standardized way to collect metrics across different
    frameworks and implementations, enabling consistent monitoring and observability
    regardless of the underlying metrics collection system.
    """

    @abstractmethod
    def add(self, name: str, value: Any) -> None:
        """Record a metric value with the specified name.

        Args:
            name: The name/identifier for the metric. Should follow naming conventions
                 of the underlying metrics system (e.g., 'response_time_ms', 'error_count').
            value: The metric value to record. Can be numeric, string, or other types
                  depending on the metrics system capabilities.

        Raises:
            Exception: If the metric cannot be recorded or the metrics system is unavailable.
        """
        pass


class LoggingInterface(ABC):
    """Abstract interface for logging and progress reporting across different frameworks.

    This interface provides a unified logging API that can work with various logging
    frameworks and implementations. It supports both traditional logging levels and
    progress reporting for long-running operations, with both synchronous and
    asynchronous variants to accommodate different execution contexts.
    """

    @abstractmethod
    def report_progress(self, current: int, total: int, message: str) -> None:
        """Report the progress of a long-running operation.

        Args:
            current: The current step or item number being processed.
            total: The total number of steps or items to process.
            message: A descriptive message about the current operation or step.

        Raises:
            Exception: If progress reporting fails or the logging system is unavailable.
        """
        pass

    @abstractmethod
    async def areport_progress(self, current: int, total: int, message: str) -> None:
        """Asynchronously report the progress of a long-running operation.

        Args:
            current: The current step or item number being processed.
            total: The total number of steps or items to process.
            message: A descriptive message about the current operation or step.

        Raises:
            Exception: If progress reporting fails or the logging system is unavailable.
        """
        pass

    @abstractmethod
    def log(self, message: str, level: LogLevel | None = None) -> None:
        """Log a message with the specified level.

        Args:
            message: Log message
            level: Log level, defaults to INFO if None
        """
        pass

    @abstractmethod
    async def alog(self, message: str, level: LogLevel | None = None) -> None:
        """Log a message with the specified level.

        Args:
            message: Log message
            level: Log level, defaults to INFO if None
        """
        pass

    def debug(self, message: str) -> None:
        """Log a DEBUG level message.

        Args:
            message: Debug message
        """
        self.log(message, LogLevel.DEBUG)

    async def adebug(self, message: str) -> None:
        """Log a DEBUG level message asynchronously.

        Args:
            message: Debug message
        """
        await self.alog(message, LogLevel.DEBUG)

    def info(self, message: str) -> None:
        """Log an INFO level message.

        Args:
            message: Info message
        """
        self.log(message, LogLevel.INFO)

    async def ainfo(self, message: str) -> None:
        """Log an INFO level message asynchronously.

        Args:
            message: Info message
        """
        await self.alog(message, LogLevel.INFO)

    def warning(self, message: str) -> None:
        """Log a WARNING level message.

        Args:
            message: Warning message
        """
        self.log(message, LogLevel.WARNING)

    async def awarning(self, message: str) -> None:
        """Log a WARNING level message asynchronously.

        Args:
            message: Warning message
        """
        await self.alog(message, LogLevel.WARNING)

    def error(self, message: str) -> None:
        """Log an ERROR level message.

        Args:
            message: Error message
        """
        self.log(message, LogLevel.ERROR)

    async def aerror(self, message: str) -> None:
        """Log an ERROR level message asynchronously.

        Args:
            message: Error message
        """
        await self.alog(message, LogLevel.ERROR)

    def critical(self, message: str) -> None:
        """Log a CRITICAL level message.

        Args:
            message: Critical message
        """
        self.log(message, LogLevel.CRITICAL)

    async def acritical(self, message: str) -> None:
        """Log a CRITICAL level message asynchronously.

        Args:
            message: Critical message
        """
        await self.alog(message, LogLevel.CRITICAL)
