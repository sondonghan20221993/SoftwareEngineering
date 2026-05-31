class DroneEvalError(Exception):
    """Base exception for all application errors."""


class FileLoadError(DroneEvalError):
    """Raised when a required input file cannot be loaded or parsed."""

    def __init__(self, path: str, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f"Failed to load '{path}': {reason}")


class ValidationError(DroneEvalError):
    """Raised when input data fails validation checks."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("Validation failed:\n" + "\n".join(f"  - {e}" for e in errors))


class EvaluationError(DroneEvalError):
    """Raised when the evaluation pipeline encounters a fatal error."""


class ExportError(DroneEvalError):
    """Raised when one or more output files cannot be saved."""

    def __init__(self, failed: list[tuple[str, str]]) -> None:
        self.failed = failed
        lines = [f"  - {name}: {reason}" for name, reason in failed]
        super().__init__("Export failed for:\n" + "\n".join(lines))
