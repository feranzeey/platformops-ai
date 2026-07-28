from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException


def get_events():
    """
    Retrieve Kubernetes events across all namespaces.

    Returns:
        list: Sorted event timeline for PlatformOps AI.
    """

    # -----------------------------------------
    # Load Kubernetes Configuration
    # -----------------------------------------

    try:
        config.load_kube_config()

    except ConfigException:
        config.load_incluster_config()

    v1 = client.CoreV1Api()

    # -----------------------------------------
    # Fetch Events
    # -----------------------------------------

    try:
        events = v1.list_event_for_all_namespaces()

    except Exception as e:
        print(f"Failed to fetch Kubernetes events: {e}")
        return []

    results = []

    # -----------------------------------------
    # Convert Events
    # -----------------------------------------

    for event in events.items:

        timestamp = (
            event.last_timestamp
            or event.event_time
            or event.first_timestamp
        )

        results.append({

            "namespace": event.metadata.namespace,

            "name": event.involved_object.name,

            "kind": event.involved_object.kind,

            "reason": event.reason,

            "message": event.message,

            "type": event.type,

            "count": (
                event.count
                or (
                    event.series.count
                    if event.series
                    else 1
                )
            ),

            "first_seen": str(event.first_timestamp),

            "last_seen": str(event.last_timestamp),

            "time": str(timestamp),

            # ---------------------------------
            # AI Timeline Fields
            # ---------------------------------

            "title": f"{event.reason}",

            "description": event.message,

            "severity": determine_event_severity(
                event.type,
                event.reason
            )
        })

    # -----------------------------------------
    # Sort newest first
    # -----------------------------------------

    results.sort(
        key=lambda x: x["time"],
        reverse=True
    )

    return results


def determine_event_severity(event_type, reason):
    """
    Assign a severity level to a Kubernetes event.
    """

    reason = (reason or "").lower()

    if (
        event_type == "Warning"
        or "failed" in reason
        or "backoff" in reason
        or "crashloop" in reason
        or "unhealthy" in reason
        or "oomkilled" in reason
    ):
        return "CRITICAL"

    if (
        "pulling" in reason
        or "scheduled" in reason
        or "created" in reason
    ):
        return "LOW"

    return "MEDIUM"