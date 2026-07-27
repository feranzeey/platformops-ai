def analyze_cluster(logs, events, metrics, github):

    severity = "LOW"
    confidence = 70

    incident_summary = []
    root_causes = []
    recommendations = []
    prevention = []
    fix_commands = []

    # ------------------------
    # Analyze Pod Logs
    # ------------------------

    if logs:

        log_text = logs.lower()

        if "crashloopbackoff" in log_text:

            severity = "HIGH"
            confidence = max(confidence, 95)

            incident_summary.append(
                "Pods are repeatedly crashing."
            )

            root_causes.append(
                "Application is repeatedly crashing (CrashLoopBackOff)."
            )

            recommendations.append(
                "Inspect the application logs."
            )

            fix_commands.append(
                "kubectl logs <pod-name> --previous"
            )

        if "imagepullbackoff" in log_text or "errimagepull" in log_text:

            severity = "HIGH"
            confidence = max(confidence, 95)

            incident_summary.append(
                "Container image cannot be pulled."
            )

            root_causes.append(
                "Container image is unavailable or registry authentication failed."
            )

            recommendations.append(
                "Verify image name, tag and registry credentials."
            )

            fix_commands.append(
                "kubectl describe pod <pod-name>"
            )

        if (
            "no matches for kind" in log_text
            and "applicationset" in log_text
        ):

            severity = "HIGH"
            confidence = 99

            incident_summary.append(
                "ApplicationSet controller failed."
            )

            root_causes.append(
                "ApplicationSet CRD is missing or incompatible."
            )

            recommendations.extend([
                "Install or upgrade the ApplicationSet CRD.",
                "Restart the ApplicationSet controller."
            ])

            prevention.append(
                "Validate CRDs before upgrading ArgoCD."
            )

        if "timed out waiting for cache to be synced" in log_text:

            severity = "HIGH"
            confidence = max(confidence, 98)

            incident_summary.append(
                "Controller cache synchronization failed."
            )

            root_causes.append(
                "Controller failed to synchronize Kubernetes caches."
            )

            recommendations.append(
                "Verify Kubernetes API connectivity."
            )

        if "database" in log_text:

            severity = "MEDIUM"

            incident_summary.append(
                "Database connectivity issue detected."
            )

            root_causes.append(
                "Database connection failure."
            )

            recommendations.append(
                "Verify database availability."
            )

        if "timeout" in log_text:

            incident_summary.append(
                "Application timeout detected."
            )

            root_causes.append(
                "Network or backend timeout."
            )

            recommendations.append(
                "Check network latency and backend services."
            )

        if "oomkilled" in log_text:

            severity = "HIGH"

            incident_summary.append(
                "Container exceeded memory limit."
            )

            root_causes.append(
                "Container was terminated due to insufficient memory."
            )

            recommendations.append(
                "Increase memory requests and limits."
            )

            prevention.append(
                "Monitor memory usage with Prometheus alerts."
            )

    # ------------------------
    # Analyze Kubernetes Events
    # ------------------------

    for event in events:

        reason = str(event.get("reason", "")).lower()
        message = str(event.get("message", "")).lower()

        if "backoff" in reason:

            severity = "HIGH"
            confidence = max(confidence, 95)

            incident_summary.append(
                "CrashLoopBackOff detected."
            )

            root_causes.append(
                "Container keeps restarting."
            )

            recommendations.append(
                "Inspect failing pod logs."
            )

        if "failedscheduling" in reason:

            severity = "HIGH"

            incident_summary.append(
                "Pods cannot be scheduled."
            )

            root_causes.append(
                "Insufficient cluster resources."
            )

            recommendations.append(
                "Check node CPU, memory and taints."
            )

        if "failedmount" in reason:

            severity = "HIGH"

            incident_summary.append(
                "Persistent volume mount failed."
            )

            root_causes.append(
                "Storage volume could not be mounted."
            )

            recommendations.append(
                "Verify PVC and StorageClass."
            )

        if "unhealthy" in reason:

            severity = "MEDIUM"

            incident_summary.append(
                "Health probes are failing."
            )

            root_causes.append(
                "Readiness/Liveness probe failure."
            )

            recommendations.append(
                "Review probe configuration."
            )

        if "oomkilled" in message:

            severity = "HIGH"

            incident_summary.append(
                "Container ran out of memory."
            )

            root_causes.append(
                "Memory limit exceeded."
            )

            recommendations.append(
                "Increase memory allocation."
            )

    # ------------------------
    # Analyze Prometheus Metrics
    # ------------------------

    try:

        cpu_results = metrics["cpu"]["data"]["result"]

        for item in cpu_results:

            job = item["metric"].get("job", "unknown")
            value = float(item["value"][1])

            if value == 0:

                incident_summary.append(
                    f"Service '{job}' appears unavailable."
                )

                recommendations.append(
                    f"Verify the '{job}' deployment."
                )

            elif value > 90:

                severity = "HIGH"

                incident_summary.append(
                    f"High CPU usage detected on '{job}'."
                )

                recommendations.append(
                    "Investigate CPU-intensive workloads."
                )

    except Exception:
        pass

    # ------------------------
    # Analyze GitHub Activity
    # ------------------------

    if github and not github.get("error"):

        incident_summary.append(
            "Recent deployment detected."
        )

        recommendations.append(
            f'Recent commit by {github["author"]}: "{github["message"]}". Verify whether this deployment introduced the issue.'
        )

    # ------------------------
    # Healthy Cluster
    # ------------------------

    if not root_causes:

        severity = "LOW"
        confidence = 98

        incident_summary.append(
            "Cluster operating normally."
        )

        root_causes.append(
            "No critical Kubernetes issues detected."
        )

        recommendations.append(
            "No immediate action required."
        )

        prevention.append(
            "Continue monitoring cluster health."
        )

    # ------------------------
    # Remove Duplicates
    # ------------------------

    incident_summary = list(dict.fromkeys(incident_summary))
    root_causes = list(dict.fromkeys(root_causes))
    recommendations = list(dict.fromkeys(recommendations))
    prevention = list(dict.fromkeys(prevention))
    fix_commands = list(dict.fromkeys(fix_commands))

    # ------------------------
    # Return AI Analysis
    # ------------------------

    return {
        "incident_summary": " | ".join(incident_summary),
        "severity": severity,
        "root_cause": " | ".join(root_causes),
        "confidence": f"{confidence}%",
        "recommendation": recommendations,
        "prevention": prevention,
        "fix_commands": fix_commands
    }