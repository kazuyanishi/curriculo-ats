class SemanticMatchingGroundingError(Exception):
    """Raised when semantic matching output cannot be grounded safely."""

    def __init__(self) -> None:
        super().__init__("Semantic matching output could not be grounded")
