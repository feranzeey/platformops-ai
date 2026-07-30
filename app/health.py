def calculate_health(
    pods,
    deployments,
    nodes,
    events,
    metrics
):
    """
    Calculate an operational Kubernetes health score.

    Returns:
        score
        status
        running_pods
        healthy_deployments
        unhealthy_deployments
        details
    """

    # =====================================================
    # 1. DEPLOYMENT COUNTS
    # =====================================================

    healthy_deployments = 0
    unhealthy_deployments = 0

    for deployment in deployments or []:

        if deployment.get("status") == "Healthy":
            healthy_deployments += 1
        else:
            unhealthy_deployments += 1


    # =====================================================
    # 2. READY POD / REPLICA COUNT
    # =====================================================
    #
    # Your deployment data contains values such as:
    # "1/1"
    # "5/5"
    #
    # We use the ready replica count as a safe fallback
    # for the dashboard's Running Pods KPI.

    running_pods = 0

    for deployment in deployments or []:

        ready_value = str(
            deployment.get("ready", "")
        )

        if "/" in ready_value:

            try:

                ready_number = int(
                    ready_value.split("/")[0]
                )

                running_pods += ready_number

            except (ValueError, TypeError):
                pass


    # If your pod collector already provides a running count,
    # prefer that value.

    if isinstance(pods, dict):

        for key in [
            "running_count",
            "running_pods",
            "running"
        ]:

            value = pods.get(key)

            if isinstance(value, int):
                running_pods = value
                break


    # =====================================================
    # 3. POD HEALTH
    # =====================================================

    pod_points = 20

    problem_count = 0

    if isinstance(pods, dict):

        problem_count = int(
            pods.get("problem_count", 0) or 0
        )

    # A small number of unhealthy pods should not destroy
    # the entire cluster score.

    pod_points -= min(
        problem_count * 5,
        20
    )

    pod_points = max(
        pod_points,
        0
    )


    # =====================================================
    # 4. DEPLOYMENT HEALTH
    # =====================================================

    deployment_points = 25

    deployment_points -= min(
        unhealthy_deployments * 5,
        25
    )

    deployment_points = max(
        deployment_points,
        0
    )


    # =====================================================
    # 5. NODE HEALTH
    # =====================================================

    node_points = 20

    unhealthy_nodes = 0

    for node in nodes or []:

        status = str(
            node.get("status", "")
        ).lower()

        if status not in [
            "ready",
            "true"
        ]:

            unhealthy_nodes += 1

    node_points -= min(
        unhealthy_nodes * 10,
        20
    )

    node_points = max(
        node_points,
        0
    )


    # =====================================================
    # 6. KUBERNETES EVENT HEALTH
    # =====================================================
    #
    # Do not count every historical warning.
    #
    # A cluster can have hundreds of old warning events while
    # currently operating normally.
    #
    # Only meaningful failure events contribute heavily.

    event_points = 20

    serious_events = 0

    for event in events or []:

        reason = str(
            event.get("reason", "")
        ).lower()

        message = str(
            event.get("message", "")
        ).lower()

        combined = f"{reason} {message}"


        if any(keyword in combined for keyword in [
            "oomkilled",
            "failedscheduling",
            "failedmount",
            "imagepullbackoff",
            "errimagepull",
            "crashloopbackoff"
        ]):

            serious_events += 1


    event_points -= min(
        serious_events * 4,
        20
    )

    event_points = max(
        event_points,
        0
    )


    # =====================================================
    # 7. PROMETHEUS HEALTH
    # =====================================================

    prometheus_points = 15

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


        # CPU

        if cpu >= 95:

            prometheus_points -= 5

        elif cpu >= 85:

            prometheus_points -= 3

        elif cpu >= 70:

            prometheus_points -= 1


        # MEMORY

        if memory >= 95:

            prometheus_points -= 5

        elif memory >= 90:

            prometheus_points -= 3

        elif memory >= 80:

            prometheus_points -= 1


        # DISK

        if disk >= 95:

            prometheus_points -= 5

        elif disk >= 90:

            prometheus_points -= 3

        elif disk >= 80:

            prometheus_points -= 1


    except (
        TypeError,
        ValueError,
        AttributeError
    ):

        pass


    prometheus_points = max(
        prometheus_points,
        0
    )


    # =====================================================
    # 8. TOTAL HEALTH SCORE
    # =====================================================

    score = (
        pod_points
        + deployment_points
        + node_points
        + event_points
        + prometheus_points
    )


    score = max(
        0,
        min(score, 100)
    )


    # =====================================================
    # 9. HEALTH STATUS
    # =====================================================

    if score >= 90:

        status = "Healthy"

    elif score >= 70:

        status = "Warning"

    else:

        status = "Critical"


    # =====================================================
    # 10. COMPONENT DETAILS
    # =====================================================

    details = {

        "pods": pod_points,

        "deployments": deployment_points,

        "nodes": node_points,

        "events": event_points,

        "prometheus": prometheus_points

    }


    # =====================================================
    # 11. FINAL RESULT
    # =====================================================

    return {

        "score": score,

        "status": status,

        "running_pods": running_pods,

        "healthy_deployments": healthy_deployments,

        "unhealthy_deployments": unhealthy_deployments,

        "details": details

    }