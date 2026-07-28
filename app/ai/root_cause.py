def determine_root_cause(deployment):
    """
    Determine the most likely root cause of an unhealthy deployment.

    Returns:
        dict: Contains the detected cause, description, confidence,
        severity, impact, and recommended kubectl command.
    """

    restart_count = deployment.get("restart_count", 0)
    warning_events = deployment.get("warning_events", 0)
    unavailable = deployment.get("unavailable", 0)
    namespace = deployment.get("namespace", "default")
    name = deployment.get("name", "unknown")

    # -----------------------------
    # CrashLoopBackOff
    # -----------------------------
    if restart_count >= 5:

        return {
            "cause": "CrashLoopBackOff",
            "description": (
                "Containers are repeatedly crashing after startup."
            ),
            "confidence": "95%",
            "severity": "HIGH",
            "impact": (
                "The application is unstable and users may be "
                "unable to access the service."
            ),
            "recommended_action": (
                "Inspect pod logs, verify configuration, "
                "and restart the deployment."
            ),
            "command": (
                f"kubectl rollout restart deployment "
                f"{name} -n {namespace}"
            )
        }

    # -----------------------------
    # Kubernetes Warning Events
    # -----------------------------
    elif warning_events > 0:

        return {
            "cause": "Kubernetes Warning Events",
            "description": (
                "Multiple Kubernetes warning events were detected."
            ),
            "confidence": "90%",
            "severity": "HIGH",
            "impact": (
                "Scheduling or resource-related issues may be "
                "preventing the application from operating normally."
            ),
            "recommended_action": (
                "Review warning events and inspect cluster resources."
            ),
            "command": (
                f"kubectl get events -n {namespace} "
                "--sort-by=.metadata.creationTimestamp"
            )
        }

    # -----------------------------
    # Unavailable Replicas
    # -----------------------------
    elif unavailable > 0:

        return {
            "cause": "Unavailable Replicas",
            "description": (
                "One or more deployment replicas cannot become Ready."
            ),
            "confidence": "88%",
            "severity": "HIGH",
            "impact": (
                "Reduced application availability may affect users."
            ),
            "recommended_action": (
                "Inspect deployment status and readiness probes."
            ),
            "command": (
                f"kubectl describe deployment "
                f"{name} -n {namespace}"
            )
        }

    # -----------------------------
    # Unknown
    # -----------------------------
    return {
        "cause": "Unknown",
        "description": (
            "PlatformOps AI could not determine the exact root cause."
        ),
        "confidence": "60%",
        "severity": "MEDIUM",
        "impact": (
            "The deployment requires additional investigation."
        ),
        "recommended_action": (
            "Review deployment, pod logs, and cluster events manually."
        ),
        "command": (
            f"kubectl describe deployment "
            f"{name} -n {namespace}"
        )
    }