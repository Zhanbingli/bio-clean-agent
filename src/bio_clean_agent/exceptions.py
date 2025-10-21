"""Custom exception hierarchy for Bio-Clean-Agent.

This module provides a comprehensive exception hierarchy for better error handling
and debugging throughout the application.
"""

from typing import Any, Dict, Optional


class BioCleanAgentError(Exception):
    """Base exception for all Bio-Clean-Agent errors.

    All custom exceptions in the application inherit from this base class,
    making it easy to catch all application-specific errors.

    Attributes:
        message: Human-readable error message
        details: Additional context about the error
        error_code: Optional error code for categorization
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.error_code = error_code

    def __str__(self) -> str:
        """String representation including error code if present."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        result = {
            "error": self.__class__.__name__,
            "message": self.message,
        }
        if self.error_code:
            result["error_code"] = self.error_code
        if self.details:
            result["details"] = self.details
        return result


# Data-related exceptions


class DataError(BioCleanAgentError):
    """Base class for data-related errors."""

    pass


class DataValidationError(DataError):
    """Data validation failed.

    Raised when input data doesn't meet expected format or constraints.
    """

    pass


class DataQualityError(DataError):
    """Data quality issues detected.

    Raised when data quality falls below acceptable thresholds.
    """

    pass


class DataNotFoundError(DataError):
    """Requested data not found.

    Raised when attempting to access non-existent data files or records.
    """

    pass


class DataFormatError(DataError):
    """Data format is invalid or unsupported.

    Raised when data format cannot be parsed or is not supported.
    """

    pass


# Pipeline-related exceptions


class PipelineError(BioCleanAgentError):
    """Base class for pipeline execution errors."""

    pass


class PipelineExecutionError(PipelineError):
    """Pipeline execution failed.

    Raised when a pipeline step fails during execution.
    """

    pass


class PipelineConfigurationError(PipelineError):
    """Pipeline configuration is invalid.

    Raised when pipeline configuration is missing required parameters
    or contains invalid values.
    """

    pass


class PipelineStepError(PipelineError):
    """Pipeline step failed.

    Raised when a specific pipeline step encounters an error.
    """

    def __init__(
        self,
        message: str,
        step_name: Optional[str] = None,
        step_index: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.step_name = step_name
        self.step_index = step_index
        if step_name:
            self.details["step_name"] = step_name
        if step_index is not None:
            self.details["step_index"] = step_index


# Knowledge base exceptions


class KnowledgeBaseError(BioCleanAgentError):
    """Base class for knowledge base errors."""

    pass


class KnowledgeNotFoundError(KnowledgeBaseError):
    """Requested knowledge entry not found.

    Raised when querying for non-existent knowledge entries.
    """

    pass


class EvidenceError(KnowledgeBaseError):
    """Evidence validation or retrieval error.

    Raised when evidence cannot be validated or retrieved.
    """

    pass


# LLM-related exceptions


class LLMError(BioCleanAgentError):
    """Base class for LLM integration errors."""

    pass


class LLMAPIError(LLMError):
    """LLM API request failed.

    Raised when external LLM API calls fail.
    """

    pass


class LLMConfigurationError(LLMError):
    """LLM configuration is invalid.

    Raised when LLM configuration is missing or invalid.
    """

    pass


class LLMResponseError(LLMError):
    """LLM response parsing failed.

    Raised when LLM response cannot be parsed or is invalid.
    """

    pass


# Job management exceptions


class JobError(BioCleanAgentError):
    """Base class for job management errors."""

    pass


class JobNotFoundError(JobError):
    """Requested job not found.

    Raised when attempting to access non-existent job.
    """

    pass


class JobExecutionError(JobError):
    """Job execution failed.

    Raised when job execution encounters an error.
    """

    pass


class JobCancelledError(JobError):
    """Job was cancelled.

    Raised when job is cancelled by user or system.
    """

    pass


class JobTimeoutError(JobError):
    """Job execution exceeded timeout.

    Raised when job execution takes longer than allowed.
    """

    pass


# Security exceptions


class SecurityError(BioCleanAgentError):
    """Base class for security-related errors."""

    pass


class AuthenticationError(SecurityError):
    """Authentication failed.

    Raised when authentication credentials are invalid or missing.
    """

    pass


class AuthorizationError(SecurityError):
    """Authorization failed.

    Raised when user lacks permission for requested operation.
    """

    pass


class FileSecurityError(SecurityError):
    """File security validation failed.

    Raised when file upload fails security checks.
    """

    pass


class PHIViolationError(SecurityError):
    """PHI/PII protection violation detected.

    Raised when attempting to expose protected health information.
    """

    pass


# Configuration exceptions


class ConfigurationError(BioCleanAgentError):
    """Base class for configuration errors."""

    pass


class MissingConfigurationError(ConfigurationError):
    """Required configuration is missing.

    Raised when required configuration parameters are not provided.
    """

    pass


class InvalidConfigurationError(ConfigurationError):
    """Configuration value is invalid.

    Raised when configuration contains invalid values.
    """

    pass


# API exceptions


class APIError(BioCleanAgentError):
    """Base class for API errors."""

    pass


class InvalidRequestError(APIError):
    """API request is invalid.

    Raised when API request validation fails.
    """

    pass


class ResourceNotFoundError(APIError):
    """Requested resource not found.

    Raised when API resource doesn't exist.
    """

    pass


class RateLimitError(APIError):
    """Rate limit exceeded.

    Raised when client exceeds API rate limits.
    """

    pass


# Error codes for categorization


class ErrorCode:
    """Standard error codes for the application."""

    # Data errors (1xxx)
    INVALID_DATA_FORMAT = "E1001"
    MISSING_REQUIRED_FIELD = "E1002"
    DATA_QUALITY_TOO_LOW = "E1003"
    DATA_NOT_FOUND = "E1004"
    UNSUPPORTED_DATA_TYPE = "E1005"

    # Pipeline errors (2xxx)
    PIPELINE_STEP_FAILED = "E2001"
    PIPELINE_CONFIG_INVALID = "E2002"
    PIPELINE_TIMEOUT = "E2003"

    # Knowledge base errors (3xxx)
    KNOWLEDGE_NOT_FOUND = "E3001"
    EVIDENCE_INVALID = "E3002"

    # LLM errors (4xxx)
    LLM_API_ERROR = "E4001"
    LLM_RESPONSE_INVALID = "E4002"
    LLM_CONFIG_MISSING = "E4003"

    # Job errors (5xxx)
    JOB_NOT_FOUND = "E5001"
    JOB_EXECUTION_FAILED = "E5002"
    JOB_CANCELLED = "E5003"
    JOB_TIMEOUT = "E5004"

    # Security errors (6xxx)
    UNAUTHORIZED = "E6001"
    FORBIDDEN = "E6002"
    FILE_SECURITY_VIOLATION = "E6003"
    PHI_VIOLATION = "E6004"

    # Configuration errors (7xxx)
    CONFIG_MISSING = "E7001"
    CONFIG_INVALID = "E7002"

    # API errors (8xxx)
    INVALID_REQUEST = "E8001"
    RESOURCE_NOT_FOUND = "E8002"
    RATE_LIMIT_EXCEEDED = "E8003"


# Utility functions for error handling


def format_error_response(exception: Exception) -> Dict[str, Any]:
    """Format exception as standardized error response.

    Args:
        exception: Exception to format

    Returns:
        Dictionary containing error information
    """
    if isinstance(exception, BioCleanAgentError):
        return exception.to_dict()

    # Handle standard Python exceptions
    return {
        "error": exception.__class__.__name__,
        "message": str(exception),
    }


def create_error_context(
    operation: str, **kwargs: Any
) -> Dict[str, Any]:
    """Create error context dictionary.

    Args:
        operation: Operation being performed when error occurred
        **kwargs: Additional context information

    Returns:
        Dictionary containing error context
    """
    context = {"operation": operation}
    context.update(kwargs)
    return context
