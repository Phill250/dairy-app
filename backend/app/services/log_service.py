import uuid
from app.repository.log_repository import LogRepository
from app.repository.cow_repository import CowRepository
from app.services.ml_service import ml_service
from app.models.log import LogModel
from app.models.cow import CowModel
from app.schemas.log import LogCreate, LogUpdate


class LogService:
    def __init__(self, repository: LogRepository, cow_repository: CowRepository):
        self.repository = repository
        self.cow_repository = cow_repository

    def list_logs_for_farmer(self, farmer_id: uuid.UUID) -> list[LogModel]:
        return self.repository.get_all_for_farmer(farmer_id)

    def _get_owned_cow(self, cow_id: uuid.UUID, farmer_id: uuid.UUID) -> CowModel | None:
        cow = self.cow_repository.get_by_id(cow_id)
        if cow is None or cow.farmer_id != farmer_id:
            return None
        return cow

    def get_log_for_farmer(self, log_id: uuid.UUID, farmer_id: uuid.UUID) -> LogModel | None:
        log = self.repository.get_by_id(log_id)
        if log is None:
            return None
        cow = self.cow_repository.get_by_id(log.cow_id)
        if cow is None or cow.farmer_id != farmer_id:
            return None
        return log

    def _predict_for_cow(self, cow: CowModel, feed: float, milking_times: int, recent_logs: list[LogModel]) -> tuple[float, bool]:
        recent_avg_yield = (
            sum(log.total_milk for log in recent_logs) / len(recent_logs)
            if recent_logs else None
        )
        expected_yield = ml_service.predict_expected_yield(
            feed=feed, milking_times=milking_times, breed=cow.breed.value,
            recent_avg_yield=recent_avg_yield,
        )
        return expected_yield, ml_service.is_loaded

    @staticmethod
    def _detect_trend(recent_logs: list[LogModel], current_total_milk: float) -> str | None:
        """
        Compares an OLDER window of a cow's recent history against a NEWER
        window (rather than just today vs. a single blended average) to
        catch a gradual decline that a rolling average would otherwise
        mask -- since the rolling baseline itself drifts down alongside a
        slow decline, a single day-vs-average comparison can miss it
        entirely. Returns "declining", "improving", or None (not enough
        data, or genuinely stable).
        """
        if len(recent_logs) < 4:
            return None  

        chronological = list(reversed(recent_logs))  # oldest -> newest
        values = [log.total_milk for log in chronological] + [current_total_milk]

        midpoint = len(values) // 2
        older_half = values[:midpoint]
        newer_half = values[midpoint:]

        avg_older = sum(older_half) / len(older_half)
        avg_newer = sum(newer_half) / len(newer_half)

        if avg_older <= 0:
            return None

        pct_change = (avg_newer - avg_older) / avg_older * 100
        if pct_change <= -15:
            return "declining"
        elif pct_change >= 15:
            return "improving"
        return None

    def create_log(self, log_in: LogCreate, farmer_id: uuid.UUID) -> LogModel:
        cow = self._get_owned_cow(log_in.cow_id, farmer_id)
        if cow is None:
            raise ValueError("Cow not found or not owned by this farmer")

        recent_logs = self.repository.get_all_for_cow(cow.id, limit=7)
        total_milk = round(sum(log_in.milkings), 1)
        expected_yield, model_used = self._predict_for_cow(cow, log_in.feed, log_in.milkingTimes, recent_logs)
        trend = self._detect_trend(recent_logs, total_milk)
        status, color, advice = self._derive_advice(
            cow_name=cow.name, total_milk=total_milk, expected_yield=expected_yield,
            feed=log_in.feed, trend=trend,
        )

        log_model = LogModel(
            cow_id=log_in.cow_id,
            date=log_in.date,
            feed=log_in.feed,
            milking_times=log_in.milkingTimes,
            total_milk=total_milk,
            status=status,
            color=color,
            advice=advice,
            predicted_yield=expected_yield,
            used_ml_model=model_used,
        )
        return self.repository.create(log_model)

    def predict(
        self, cow_id: uuid.UUID, feed: float, milking_times: int, farmer_id: uuid.UUID
    ) -> tuple[float, bool] | None:
        cow = self._get_owned_cow(cow_id, farmer_id)
        if cow is None:
            return None
        recent_logs = self.repository.get_all_for_cow(cow.id, limit=7)
        return self._predict_for_cow(cow, feed, milking_times, recent_logs)

    def update_log(self, log_id: uuid.UUID, log_in: LogUpdate, farmer_id: uuid.UUID) -> LogModel | None:
        log_model = self.get_log_for_farmer(log_id, farmer_id)
        if log_model is None:
            return None

        target_cow_id = log_in.cow_id if log_in.cow_id is not None else log_model.cow_id
        cow = self._get_owned_cow(target_cow_id, farmer_id)
        if cow is None:
            raise ValueError("Cow not found or not owned by this farmer")

        if log_in.cow_id is not None:
            log_model.cow_id = log_in.cow_id
        if log_in.date is not None:
            log_model.date = log_in.date
        if log_in.feed is not None:
            log_model.feed = log_in.feed
        if log_in.milkingTimes is not None:
            log_model.milking_times = log_in.milkingTimes
        if log_in.milkings is not None:
            log_model.total_milk = round(sum(log_in.milkings), 1)

        recent_logs = [
            l for l in self.repository.get_all_for_cow(cow.id, limit=8) if l.id != log_model.id
        ][:7]
        expected_yield, model_used = self._predict_for_cow(cow, log_model.feed, log_model.milking_times, recent_logs)
        trend = self._detect_trend(recent_logs, log_model.total_milk)
        status, color, advice = self._derive_advice(
            cow_name=cow.name, total_milk=log_model.total_milk,
            expected_yield=expected_yield, feed=log_model.feed, trend=trend,
        )
        log_model.status = status
        log_model.color = color
        log_model.advice = advice
        log_model.predicted_yield = expected_yield
        log_model.used_ml_model = model_used

        return self.repository.update(log_model)

    def delete_log(self, log_id: uuid.UUID, farmer_id: uuid.UUID) -> bool:
        log = self.get_log_for_farmer(log_id, farmer_id)
        if log is None:
            return False
        self.repository.delete(log)
        return True

    @staticmethod
    def _derive_advice(
        cow_name: str, total_milk: float, expected_yield: float, feed: float, trend: str | None = None
    ) -> tuple[str, str, str]:
        deviation_pct = 0.0 if expected_yield <= 0 else (total_milk - expected_yield) / expected_yield * 100
        deviation_liters = round(abs(total_milk - expected_yield), 1)
        name = cow_name or "This cow"

        trend_note = ""
        if trend == "declining":
            trend_note = (
                f" Also worth noting: {name}'s yield has been trending down over the past several days. "
                f"Even if today alone doesn't look alarming, a steady decline like this is worth watching closely."
            )
        elif trend == "improving":
            trend_note = f" Good news: {name}'s yield has also been improving over the past several days."

        if deviation_pct <= -30:
            return (
                "Critical Alert",
                "#dc2626",
                f"{name} gave {deviation_liters}L less milk than usual today "
                f"({total_milk}L, compared to her usual {expected_yield:.1f}L). "
                f"That's a big drop. Check her now: Is she eating and drinking normally? "
                f"Any swelling, heat, or pain in the udder? Is she standing and moving normally? "
                f"If anything seems off, contact a vet today.{trend_note}"
            )
        elif deviation_pct <= -10:
            return (
                "Warning / Low",
                "#ea580c",
                f"{name} gave a bit less milk than usual today "
                f"({total_milk}L, compared to her usual {expected_yield:.1f}L). "
                f"Check that she finished all {feed}kg of her feed and has enough clean water. "
                f"If this continues for more than a day or two, it's worth checking with a vet.{trend_note}"
            )
        else:
           
            if trend == "declining":
                return (
                    "Warning / Low",
                    "#ea580c",
                    f"{name} gave {total_milk}L today, close to her recent usual amount. "
                    f"However, her yield has been trending downward over the past several days "
                    f"worth keeping an eye on, even though today alone isn't a red flag.{trend_note.replace(' Also worth noting:', '')}"
                )
            return (
                "Good Condition",
                "#16a34a",
                f"{name} gave {total_milk}L today, matching or beating her usual {expected_yield:.1f}L. "
                f"Great work — keep up the same feeding and care routine.{trend_note}"
            )