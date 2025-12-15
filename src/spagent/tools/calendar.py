from datetime import datetime, timedelta
import pytz


TZ = pytz.timezone("America/Sao_Paulo")


def current_weekend(today: datetime | None = None):
    now = today.astimezone(TZ) if today else datetime.now(TZ)
    # find Friday of the same week (weekday: Mon=0 ... Sun=6)
    days_to_friday = (4 - now.weekday()) % 7
    friday = (now + timedelta(days=days_to_friday)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    sunday = friday + timedelta(days=2, hours=23, minutes=59)
    return friday, sunday
