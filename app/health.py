def calculate_health(
    pods,
    deployments,
    nodes,
    events,
    metrics
):

    score = 100

    details = {}

    # -----------------------
    # Pods (20 points)
    # -----------------------

    pod_points = 20

    if pods["problem_count"] > 0:
        pod_points -= min(
            pods["problem_count"] * 5,
            20
        )

    details["pods"] = max(pod_points, 0)

    # -----------------------
    # Deployments (25 points)
    # -----------------------

    deployment_points = 25

    for deployment in deployments:

        if deployment.get("status") != "Healthy":
            deployment_points -= 5

    deployment_points = max(deployment_points, 0)

    details["deployments"] = deployment_points

    # -----------------------
    # Nodes (20 points)
    # -----------------------

    node_points = 20

    for node in nodes:

        if node.get("status") == "NotReady":
            node_points -= 20

    details["nodes"] = max(node_points, 0)

    # -----------------------
    # Events (20 points)
    # -----------------------

    event_points = 20

    warning_events = 0

    for event in events:

        if event["type"] == "Warning":
            warning_events += 1

    event_points -= min(
        warning_events * 2,
        20
    )

    details["events"] = max(event_points, 0)

    # -----------------------
    # Prometheus (15 points)
    # -----------------------

    prometheus_points = 15

    try:

        cpu_results = metrics["cpu"]["data"]["result"]

        for item in cpu_results:

            if item["value"][1] == "0":
                prometheus_points -= 5

    except:
        pass

    prometheus_points = max(
        prometheus_points,
        0
    )

    details["prometheus"] = prometheus_points

    # -----------------------
    # Total Score
    # -----------------------

    score = (
        details["pods"]
        + details["deployments"]
        + details["nodes"]
        + details["events"]
        + details["prometheus"]
    )

    if score >= 90:
        status = "Healthy"

    elif score >= 70:
        status = "Warning"

    else:
        status = "Critical"

    return {

        "score": score,

        "status": status,

        "details": details
    }