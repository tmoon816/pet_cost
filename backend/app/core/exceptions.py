from typing import Any, Dict


class ConflictError(Exception):
    """Application-level 409 Conflict.

    `detail` is a JSON-serializable dict that becomes the response body's `detail` field.
    """

    def __init__(self, detail: Dict[str, Any]):
        self.detail = detail
        super().__init__(str(detail))


class InsufficientBalanceError(Exception):
    """储值余额不足以支付订单 → 400。

    `detail` 携带当前余额与所需金额，便于前端提示。
    """

    def __init__(self, balance: Any, required: Any):
        self.detail = {
            "detail": "insufficient_balance",
            "balance": str(balance),
            "required": str(required),
        }
        super().__init__(str(self.detail))
