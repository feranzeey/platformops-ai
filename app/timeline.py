from datetime import datetime, timezone


# =====================================================
# EVENT SEVERITY
# =====================================================

def _get_event_severity(reason, message):
    """
    Determine the severity of an individual Kubernetes event.
    """

    text = f"{reason} {message}".lower()

    # -------------------------------------------------
    # CRITICAL
    # -------------------------------------------------

    if any(keyword in text for keyword in [
        "oomkilled",
        "failedscheduling",
        "failedmount",
        "crashloopbackoff",
        "errimagepull",
        "imagepullbackoff",
        "back-off restarting failed container",
        "container failed",
    ]):
        return "CRITICAL"

    # -------------------------------------------------
    # HIGH
    # -------------------------------------------------

    if any(keyword in text for keyword in [
        "failed to pull image",
        "connection refused",
        "container runtime",
    ]):
        return "HIGH"

    # -------------------------------------------------
    # MEDIUM
    # -------------------------------------------------

    if any(keyword in text for keyword in [
        "liveness probe failed",
        "readiness probe failed",
        "startup probe failed",
        "unhealthy",
        "timeout",
    ]):
        return "MEDIUM"

    # -------------------------------------------------
    # LOW
    # -------------------------------------------------

    return "LOW"


# =====================================================
# EVENT ICON
# =====================================================

def _get_event_icon(severity):
    """
    Return a visual indicator for the timeline.
    """

    if severity == "CRITICAL":
        return "🔴"

    if severity == "HIGH":
        return "🟠"

    if severity == "MEDIUM":
        return "🟡"

    return "🔵"


# =====================================================
# BUILD INCIDENT TIMELINE
# =====================================================

def build_incident_timeline(events):
    """
    Convert raw Kubernetes events into a normalized
    and readable timeline.
    """

    timeline = []

    for event in events or []:

        reason = str(
            event.get("reason", "")
        )

        message = str(
            event.get("message", "")
        )

        namespace = event.get(
            "namespace",
            "default"
        )

        resource = event.get(
            "resource",
            event.get(
                "name",
                "Unknown"
            )
        )

        kind = event.get(
            "kind",
            event.get(
                "type",
                "Resource"
            )
        )

        # =================================================
        # TIMESTAMP
        # =================================================

        raw_time = (
            event.get("time")
            or event.get("timestamp")
            or event.get("lastTimestamp")
            or event.get("event_time")
            or ""
        )

        parsed_time = raw_time

        if raw_time:

            try:

                parsed = datetime.fromisoformat(
                    str(raw_time).replace(
                        "Z",
                        "+00:00"
                    )
                )

                parsed_time = parsed.isoformat()

            except (
                ValueError,
                TypeError
            ):

                parsed_time = str(
                    raw_time
                )

        # =================================================
        # EVENT SEVERITY
        # =================================================

        severity = _get_event_severity(
            reason,
            message
        )

        icon = _get_event_icon(
            severity
        )

        # =================================================
        # EVENT NAME
        # =================================================

        event_name = (
            reason
            if reason
            else "Kubernetes Event"
        )

        timeline.append({

            "time": parsed_time,

            "namespace": str(
                namespace
            ),

            "resource": str(
                resource
            ),

            "kind": str(
                kind
            ),

            "event": event_name,

            "message": message,

            "severity": severity,

            "icon": icon

        })

    # =====================================================
    # SORT CHRONOLOGICALLY
    # =====================================================

    def sort_key(item):

        value = item.get(
            "time",
            ""
        )

        try:

            return datetime.fromisoformat(
                str(value).replace(
                    "Z",
                    "+00:00"
                )
            )

        except (
            ValueError,
            TypeError
        ):

            return datetime.min.replace(
                tzinfo=timezone.utc
            )

    timeline.sort(
        key=sort_key
    )

    # =====================================================
    # LIMIT DISPLAYED TIMELINE
    # =====================================================

    # Keep only the latest 20 events so the dashboard
    # remains readable.

    if len(timeline) > 20:

        timeline = timeline[-20:]

    return timeline


# =====================================================
# SUMMARIZE TIMELINE
# =====================================================

def summarize_timeline(timeline):
    """
    Generate a current-state summary from the timeline.

    Important:
    Historical critical events do not automatically make
    the current timeline CRITICAL. The latest event is the
    primary signal for current state.
    """

    timeline = timeline or []

    total_events = len(
        timeline
    )

    if total_events == 0:

        return {

            "summary":
                "No Kubernetes events were detected.",

            "current_state":
                "No recent activity",

            "severity":
                "LOW",

            "events":
                0

        }

    # =====================================================
    # LATEST EVENT
    # =====================================================

    latest = timeline[-1]

    latest_event = str(
        latest.get(
            "event",
            "Recent activity"
        )
    )

    latest_message = str(
        latest.get(
            "message",
            ""
        )
    )

    latest_resource = str(
        latest.get(
            "resource",
            "cluster"
        )
    )

    latest_namespace = str(
        latest.get(
            "namespace",
            "default"
        )
    )

    latest_severity = str(
        latest.get(
            "severity",
            "LOW"
        )
    ).upper()

    latest_text = (
        f"{latest_event} "
        f"{latest_message} "
        f"{latest_resource}"
    ).lower()

    # =====================================================
    # DETERMINE CURRENT STATE
    # =====================================================

    if any(keyword in latest_text for keyword in [
        "crashloopbackoff",
        "imagepullbackoff",
        "errimagepull",
        "back-off restarting",
        "failedscheduling",
        "failedmount",
        "oomkilled",
    ]):

        current_state = (
            f"Active incident detected in "
            f"{latest_namespace}"
        )

        severity = latest_severity

    elif any(keyword in latest_text for keyword in [
        "successfully pulled",
        "container started",
        "container created",
        "became leader",
        "updated sync status",
        "resourceupdated",
    ]):

        current_state = (
            f"Recent activity progressing "
            f"in {latest_namespace}"
        )

        severity = "LOW"

    elif any(keyword in latest_text for keyword in [
        "readiness probe failed",
        "liveness probe failed",
        "startup probe failed",
        "unhealthy",
        "timeout",
        "connection refused",
    ]):

        current_state = (
            f"Operational warning detected "
            f"in {latest_namespace}"
        )

        severity = "MEDIUM"

    else:

        current_state = (
            f"Monitoring activity in "
            f"{latest_namespace}"
        )

        severity = "LOW"

    # =====================================================
    # SUMMARY
    # =====================================================

    if severity == "CRITICAL":

        summary = (
            f"PlatformOps AI analyzed "
            f"{total_events} recent Kubernetes events "
            f"and detected an active critical issue."
        )

    elif severity == "HIGH":

        summary = (
            f"PlatformOps AI analyzed "
            f"{total_events} recent Kubernetes events "
            f"and detected an active high-priority issue."
        )

    elif severity == "MEDIUM":

        summary = (
            f"PlatformOps AI analyzed "
            f"{total_events} recent Kubernetes events "
            f"and detected operational warnings."
        )

    else:

        summary = (
            f"PlatformOps AI analyzed "
            f"{total_events} recent Kubernetes events. "
            f"Current cluster activity is stable."
        )

    return {

        "summary": summary,

        "current_state": current_state,

        "severity": severity,

        "events": total_events

    }


# =====================================================
# GENERATE INCIDENT STORY
# =====================================================

def generate_incident_story(timeline):
    """
    Generate a concise human-readable incident story.
    """

    timeline = timeline or []

    if not timeline:

        return (
            "No recent Kubernetes activity was "
            "available for incident reconstruction."
        )

    latest = timeline[-1]

    latest_event = latest.get(
        "event",
        "Recent activity"
    )

    latest_resource = latest.get(
        "resource",
        "cluster"
    )

    latest_namespace = latest.get(
        "namespace",
        "default"
    )

    latest_severity = str(
        latest.get(
            "severity",
            "LOW"
        )
    ).upper()

    if latest_severity == "CRITICAL":

        return (
            f"PlatformOps AI detected an active "
            f"critical issue involving "
            f"{latest_resource} in "
            f"{latest_namespace}. "
            f"The latest event was "
            f"'{latest_event}'."
        )

    if latest_severity == "HIGH":

        return (
            f"PlatformOps AI detected an active "
            f"high-priority issue involving "
            f"{latest_resource} in "
            f"{latest_namespace}. "
            f"The latest event was "
            f"'{latest_event}'."
        )

    if latest_severity == "MEDIUM":

        return (
            f"PlatformOps AI detected an operational "
            f"warning involving "
            f"{latest_resource} in "
            f"{latest_namespace}. "
            f"The latest event was "
            f"'{latest_event}'."
        )

    return (
        f"PlatformOps AI reconstructed "
        f"{len(timeline)} recent Kubernetes events. "
        f"Current activity appears stable, with the "
        f"latest event being "
        f"'{latest_event}' involving "
        f"{latest_resource}."
    )