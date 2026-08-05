"""Exceptions shared by AI-agent implementations."""


class AgentConfigurationError(RuntimeError):
    """Raised when an agent cannot be configured."""


class AgentExecutionError(RuntimeError):
    """Raised when an agent workflow cannot produce a valid result."""
