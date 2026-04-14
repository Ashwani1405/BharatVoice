"""
Sprint 4 — Pathway Stream Listener
Background worker process leveraging Pathway to process live Redis events
and flag velocity anomalies (e.g. DDOS or rapid API usage from same IP).

Compatible with pathway==0.11.0.
API notes:
  - Input:  pw.io.python.read(ConnectorSubject subclass, schema=...)
  - Output: pw.io.subscribe(table, on_change=callback)  — NOT pw.io.python.write
  - Window: table.windowby(..., window=pw.temporal.tumbling(...)).reduce(...)
"""
import pathway as pw
import json
import logging
import redis as redis_lib
from time import sleep

from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FraudEventSchema(pw.Schema):
    user_id: str
    ip_address: str
    event_type: str
    timestamp: float


class RedisConnectorSubject(pw.io.python.ConnectorSubject):
    """
    Pathway ConnectorSubject that drains a Redis list and feeds rows into the
    Pathway computation graph.  The streaming loop must live in run().
    """

    def run(self):
        r = redis_lib.from_url(settings.REDIS_URL, decode_responses=True)
        logger.info("Pathway Worker: Connected to Redis, listening on 'fraud_events'...")

        while True:
            try:
                item = r.blpop("fraud_events", timeout=1)
                if item:
                    _, data_str = item
                    data = json.loads(data_str)
                    self.next(
                        user_id=data.get("user_id", "unknown"),
                        ip_address=data.get("ip_address", "unknown"),
                        event_type=data.get("event_type", "unknown"),
                        timestamp=float(data.get("timestamp", 0.0)),
                    )
            except Exception as e:
                logger.error(f"Redis poll error: {e}")
                sleep(1)


def _on_anomaly_change(key, row, time, is_addition):
    """
    pw.io.subscribe callback — called whenever a row is added or retracted.
    We only act on additions (new anomaly detected).
    """
    if not is_addition:
        return
    ip = row.get("ip_address", "unknown")
    count = row.get("event_count", 0)
    logger.warning(f"FRAUD ALERT: High velocity detected for IP {ip} ({count} events/min)")
    try:
        r = redis_lib.from_url(settings.REDIS_URL, decode_responses=True)
        r.setex(f"blacklist:ip:{ip}", 3600, "velocity_abuse")
        logger.info(f"Blacklisted IP {ip} for 1 hour")
    except Exception as exc:
        logger.error(f"Could not write blacklist for {ip}: {exc}")


def build_pipeline():
    # 1. Connect to Redis via the custom subject
    subject = RedisConnectorSubject()
    events_table = pw.io.python.read(subject, schema=FraudEventSchema)

    # 2. Group by IP address to get continuous rolling count without watermark issues
    windowed = events_table.groupby(
        events_table.ip_address
    ).reduce(
        ip_address=pw.this._pw_instance,
        event_count=pw.reducers.count(),
    )

    # 3. Filter: flag IPs with > 5 requests in the window
    anomalies = windowed.filter(windowed.event_count > 5)

    # 4. Subscribe to results — pw.io.subscribe is the correct output API in 0.11.x
    pw.io.subscribe(anomalies, on_change=_on_anomaly_change)


if __name__ == "__main__":
    logger.info("Starting Pathway Fraud Stream...")
    build_pipeline()
    pw.run()
