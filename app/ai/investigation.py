from ai.root_cause import determine_root_cause


def investigate_deployment(deployment):
    """
    Analyze a Kubernetes deployment and generate an AI investigation report.

    Returns:
        dict: AI investigation report for unhealthy deployments.
        None: If the deployment is healthy.
    """

    # ---------------------------------------------------
    # Skip Healthy Deployments
    # ---------------------------------------------------

    if deployment.get("status") == "Healthy":
        return None

    # ---------------------------------------------------
    # Deployment Information
    # ---------------------------------------------------

    name = deployment.get("name", "Unknown")
    namespace = deployment.get("namespace", "default")

    ready = deployment.get("ready", "0/0")
    unavailable = deployment.get("unavailable", 0)
    restart_count = deployment.get("restart_count", 0)
    warning_events = deployment.get("warning_events", 0)
    conditions = deployment.get("conditions", [])

    # ---------------------------------------------------
    # AI Root Cause Analysis
    # ---------------------------------------------------

    analysis = determine_root_cause(deployment)

    # ---------------------------------------------------
    # Collect Evidence
    # ---------------------------------------------------

    evidence = [

        f"Ready Replicas: {ready}",

        f"Unavailable Replicas: {unavailable}",

        f"Container Restart Count: {restart_count}",

        f"Recent Warning Events: {warning_events}"

    ]

    if conditions:

        evidence.append("Deployment Conditions:")

        for condition in conditions:

            evidence.append(
                f"- {condition.get('type', 'Unknown')} | "
                f"Status: {condition.get('status', 'Unknown')} | "
                f"Reason: {condition.get('reason', 'N/A')}"
            )

    # ---------------------------------------------------
    # AI Recommendations
    # ---------------------------------------------------

    recommendations = []

    if restart_count >= 5:

        recommendations.extend([

            "Inspect pod logs for application startup failures.",

            "Verify ConfigMaps and Secrets.",

            "Check environment variables.",

            "Verify the container image exists."

        ])

    if warning_events > 0:

        recommendations.extend([

            "Review Kubernetes warning events.",

            "Inspect scheduler decisions.",

            "Check cluster resource availability."

        ])

    if unavailable > 0:

        recommendations.extend([

            "Verify readiness and liveness probes.",

            "Check node resource utilization.",

            "Restart the deployment if required."

        ])

    if not recommendations:

        recommendations.append(
            "Continue monitoring deployment health."
        )

    # Remove duplicate recommendations
    recommendations = list(dict.fromkeys(recommendations))

    # ---------------------------------------------------
    # Suggested kubectl Commands
    # ---------------------------------------------------

    commands = [

        f"kubectl describe deployment {name} -n {namespace}",

        f"kubectl get pods -n {namespace}",

        f"kubectl get events -n {namespace} --sort-by=.lastTimestamp",

        f"kubectl logs -n {namespace} <pod-name>",

        f"kubectl describe pod <pod-name> -n {namespace}",

        f"kubectl rollout status deployment {name} -n {namespace}",

        analysis["command"]

    ]

    # Remove duplicate commands
    commands = list(dict.fromkeys(commands))

    # ---------------------------------------------------
    # AI Investigation Report
    # ---------------------------------------------------

    return {

        "title": name,

        "issue": analysis["cause"],

        "description": analysis["description"],

        "impact": analysis["impact"],

        "severity": analysis["severity"],

        "confidence": analysis["confidence"],

        "recommended_action": analysis["recommended_action"],

        "evidence": evidence,

        "recommendations": recommendations,

        "command": "\n".join(commands)

    }