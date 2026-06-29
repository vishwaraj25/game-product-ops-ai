class AIReasoningError(Exception):
    pass


class ProviderNotConfiguredError(AIReasoningError):
    pass


class StructuredOutputValidationError(AIReasoningError):
    pass
