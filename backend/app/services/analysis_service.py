from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Event, Incident


def analyze_incident(db: Session, incident: Incident) -> dict[str, object]:
    """Produce transparent, deterministic hypotheses from stored incident evidence."""
    now = datetime.now(timezone.utc)
    events = list(
        db.scalars(
            select(Event)
            .where(
                Event.organization_id == incident.organization_id,
                Event.service == incident.service,
                Event.received_at >= now - timedelta(hours=24),
            )
            .order_by(Event.received_at.desc())
            .limit(500)
        ).all()
    )

    if not events:
        return {
            "incident_id": incident.id,
            "summary": "There is not enough event data to generate a useful analysis.",
            "anomaly": {"detected": False, "current_window_events": 0, "baseline_mean": 0.0, "z_score": 0.0},
            "hypotheses": [],
            "limitations": ["No matching events were found in the last 24 hours."],
        }

    event_types = Counter(event.event_type for event in events)
    severities = Counter(event.severity for event in events)
    deployments = Counter(
        str(event.attributes.get("deployment"))
        for event in events
        if event.attributes.get("deployment") is not None
    )
    regions = Counter(
        str(event.attributes.get("region"))
        for event in events
        if event.attributes.get("region") is not None
    )

    current_start = now - timedelta(minutes=15)
    current_count = sum(1 for event in events if _utc(event.received_at) >= current_start)
    baseline_counts = []
    for window in range(1, 17):
        end = now - timedelta(minutes=15 * (window - 1))
        start = end - timedelta(minutes=15)
        if window == 1:
            continue
        baseline_counts.append(
            sum(1 for event in events if start <= _utc(event.received_at) < end)
        )
    mean = sum(baseline_counts) / len(baseline_counts) if baseline_counts else 0.0
    variance = (
        sum((value - mean) ** 2 for value in baseline_counts) / len(baseline_counts)
        if baseline_counts else 0.0
    )
    stddev = variance ** 0.5
    z_score = (current_count - mean) / stddev if stddev > 0 else (float(current_count) if current_count > 0 else 0.0)
    anomaly_detected = current_count >= 3 and current_count > mean + max(2.0 * stddev, 2.0)

    hypotheses: list[dict[str, object]] = []
    if deployments:
        deployment, count = deployments.most_common(1)[0]
        if count >= 2:
            hypotheses.append({
                "type": "deployment_correlation",
                "title": f"Repeated events are associated with deployment {deployment}",
                "confidence": "low",
                "evidence": [f"{count} of {len(events)} matching service events carry this deployment label."],
                "caveat": "Correlation is not proof that the deployment caused the incident.",
            })
    if event_types:
        event_type, count = event_types.most_common(1)[0]
        hypotheses.append({
            "type": "dominant_error_pattern",
            "title": f"Most frequent event pattern: {event_type}",
            "confidence": "low" if count < 3 else "moderate",
            "evidence": [f"{count} of {len(events)} matching service events have this event type."],
            "caveat": "Inspect traces and recent changes before confirming a root cause.",
        })
    if regions:
        region, count = regions.most_common(1)[0]
        if count >= 2:
            hypotheses.append({
                "type": "regional_concentration",
                "title": f"Events are concentrated in region {region}",
                "confidence": "low",
                "evidence": [f"{count} events carry this region label."],
                "caveat": "Missing region attributes may bias this observation.",
            })
    if anomaly_detected:
        hypotheses.append({
            "type": "event_rate_anomaly",
            "title": "Event volume is elevated in the latest 15-minute window",
            "confidence": "moderate",
            "evidence": [
                f"{current_count} events in the latest 15 minutes versus a prior-window mean of {mean:.2f}.",
                f"Approximate standardized deviation: {z_score:.2f}.",
            ],
            "caveat": "This simple baseline is directional and is not a trained anomaly model.",
        })

    return {
        "incident_id": incident.id,
        "summary": (
            f"Reviewed {len(events)} events for {incident.service} from the last 24 hours. "
            f"Most common severity: {severities.most_common(1)[0][0]}."
        ),
        "anomaly": {
            "detected": anomaly_detected,
            "current_window_events": current_count,
            "baseline_mean": round(mean, 2),
            "z_score": round(z_score, 2),
            "window_minutes": 15,
        },
        "hypotheses": hypotheses,
        "limitations": [
            "These are evidence-based hypotheses, not confirmed root causes.",
            "No source code, deployment diff, distributed trace, or infrastructure metrics were inspected.",
        ],
    }


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
