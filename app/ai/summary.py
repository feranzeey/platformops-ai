def generate_summary(report):

    deployments = report["deployments"]
    pods = report["pods"]["all"]

    healthy = 0
    unhealthy = 0
    critical = 0

    for deployment in deployments:

        if deployment["status"] == "Healthy":
            healthy += 1
        else:
            unhealthy += 1

        if deployment["restart_count"] >= 10:
            critical += 1

    health = report["health"]["score"]

    recommendation = "Cluster operating normally."

    if unhealthy:

        recommendation = (
            "Investigate unhealthy deployments before they "
            "affect application availability."
        )

    return {

        "health": health,

        "pods": len(pods),

        "healthy": healthy,

        "unhealthy": unhealthy,

        "critical": critical,

        "recommendation": recommendation

    }