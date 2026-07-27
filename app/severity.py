def calculate_severity(logs, events, metrics):
    """
    Calculate overall cluster severity.

    Returns:
        LOW
        MEDIUM
        HIGH
        CRITICAL
    """

    score = 0

    # ------------------------
    # Analyze Logs
    # ------------------------

    if logs:

        log_text = logs.lower()

        high_keywords = [
            "crashloopbackoff",
            "imagepullbackoff",
            "errimagepull",
            "oomkilled",
            "failedmount",
            "failedscheduling",
            "panic",
            "fatal",
            "segmentation fault"
        ]

        medium_keywords = [
            "timeout",
            "database",
            "connection refused",
            "unhealthy",
            "warning"
        ]

        for keyword in high_keywords:
            if keyword in log_text:
                score += 25

        for keyword in medium_keywords:
            if keyword in log_text:
                score += 10

    # ------------------------
    # Analyze Kubernetes Events
    # ------------------------

    for event in events:

        reason = str(event.get("reason", "")).lower()
        message = str(event.get("message", "")).lower()

        if any(keyword in reason for keyword in [
            "backoff",
            "failedscheduling",
            "failedmount"
        ]):
            score += 20

        if any(keyword in message for keyword in [
            "oomkilled",
            "imagepullbackoff",
            "errimagepull"
        ]):
            score += 20

        if "unhealthy" in reason:
            score += 10

    # ------------------------
    # Analyze Prometheus Metrics
    # ------------------------

    try:
        cpu_results = metrics["cpu"]["data"]["result"]

        for item in cpu_results:

            cpu = float(item["value"][1])

            if cpu >= 95:
                score += 30
            elif cpu >= 85:
                score += 20
            elif cpu >= 70:
                score += 10

    except Exception:
        pass

    # ------------------------
    # Final Severity
    # ------------------------

    if score >= 80:
        return "CRITICAL"

    if score >= 50:
        return "HIGH"

    if score >= 20:
        return "MEDIUM"

    return "LOW"