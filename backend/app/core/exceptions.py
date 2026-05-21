from typing import Any, Dict


class ConflictError(Exception):
    """Application-level 409 Conflict.

    `detail` is a JSON-serializable dict that becomes the response body's `detail` field.
    """

    def __init__(self, detail: Dict[str, Any]):
        self.detail = detail
        super().__init__(str(detail))
