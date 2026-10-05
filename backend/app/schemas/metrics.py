from pydantic import BaseModel


class MetricsRead(BaseModel):
    total_farmers: int
    total_cows: int
    total_logs: int
    average_total_milk: float | None
    average_feed: float | None
    average_predicted_yield: float | None
    ml_model_usage_rate: float
    status_breakdown: dict[str, int]