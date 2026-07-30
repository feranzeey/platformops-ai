def calculate_severity(logs, events, metrics):
    """
    Calculate the current overall cluster severity.

    Severity is based primarily on:
    - Recent application/runtime logs
    - The most recent Kubernetes events
    - Current Prometheus utilization

    Returns:
        LOW
        MEDIUM
        HIGH
        CRITICAL
    """

    score = 0

    # =====================================================
    # 1. LOG SIGNALS
    # =====================================================

    log_text = str(logs or "").lower()

    critical_keywords = [
        "oomkilled",
        "panic",
        "fatal",
        "segmentation fault",
        "failedmount",
        "failedscheduling",
    ]

    high_keywords = [
        "crashloopbackoff",
        "errimagepull",
        "imagepullbackoff",
        "back-off restarting",
        "backoff restarting",
    ]

    medium_keywords = [
        "connection refused",
        "unhealthy",
        "timeout",
    ]

    # Add each severity group only once so repeated
    # log lines do not inflate the score.
    if any(keyword in log_text for keyword in critical_keywords):
        score += 30

    elif any(keyword in log_text for keyword in high_keywords):
        score += 20

    elif any(keyword in log_text for keyword in medium_keywords):
        score += 5

    # =====================================================
    # 2. RECENT KUBERNETES EVENTS
    # =====================================================

    # Only inspect the most recent events.
    # This prevents old cluster history from permanently
    # forcing the dashboard into HIGH/CRITICAL.
    recent_events = (events or [])[-10:]

    critical_events = 0
    high_events = 0
    medium_events = 0

    for event in recent_events:

        reason = str(
            event.get("reason", "")
        ).lower()

        message = str(
            event.get("message", "")
        ).lower()

        combined = f"{reason} {message}"

        # -----------------------------------------
        # CRITICAL
        # -----------------------------------------

        if any(keyword in combined for keyword in [
            "oomkilled",
            "failedmount",
            "failedscheduling",
            "container runtime",
            "nodepressure",
        ]):
            critical_events += 1

        # -----------------------------------------
        # HIGH
        # -----------------------------------------

        elif any(keyword in combined for keyword in [
            "crashloopbackoff",
            "imagepullbackoff",
            "errimagepull",
            "back-off restarting failed container",
            "failed to pull image",
            "container failed",
        ]):
            high_events += 1

        # -----------------------------------------
        # MEDIUM
        # -----------------------------------------

        elif any(keyword in combined for keyword in [
            "readiness probe failed",
            "liveness probe failed",
            "startup probe failed",
            "unhealthy",
            "connection refused",
            "timeout",
        ]):
            medium_events += 1

    # Limit the contribution from repeated recent events.
    score += min(critical_events * 20, 40)
    score += min(high_events * 10, 20)
    score += min(medium_events * 2, 10)

    # =====================================================
    # 3. CURRENT PROMETHEUS METRICS
    # =====================================================

    try:

        cpu = float(
            metrics.get("cpu", 0)
        )

        memory = float(
            metrics.get("memory", 0)
        )

        disk = float(
            metrics.get("disk", 0)
        )

        # -----------------------------------------
        # CPU
        # -----------------------------------------

        if cpu >= 95:
            score += 20

        elif cpu >= 90:
            score += 12

        elif cpu >= 80:
            score += 5

        # -----------------------------------------
        # MEMORY
        # -----------------------------------------

        if memory >= 95:
            score += 20

        elif memory >= 90:
            score += 12

        elif memory >= 80:
            score += 5

        # -----------------------------------------
        # DISK
        # -----------------------------------------

        if disk >= 95:
            score += 20

        elif disk >= 90:
            score += 12

        elif disk >= 80:
            score += 5

    except (
        TypeError,
        ValueError,
        AttributeError
    ):
        pass

    # =====================================================
    # 4. FINAL SEVERITY
    # =====================================================

    if score >= 60:
        return "CRITICAL"

    if score >= 35:
        return "HIGH"

    if score >= 15:
        return "MEDIUM"

    return "LOW"