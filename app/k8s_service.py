def get_deployments():
    deployments = apps.list_deployment_for_all_namespaces().items

    results = []

    for deployment in deployments:

        desired = deployment.spec.replicas or 0
        available = deployment.status.available_replicas or 0
        ready = deployment.status.ready_replicas or 0
        updated = deployment.status.updated_replicas or 0
        unavailable = deployment.status.unavailable_replicas or 0

        created = deployment.metadata.creation_timestamp

        age = ""
        if created:
            age = str(datetime.now(timezone.utc) - created).split(".")[0]

        # -----------------------------
        # Deployment Conditions
        # -----------------------------

        conditions = []

        if deployment.status.conditions:
            for condition in deployment.status.conditions:
                conditions.append({
                    "type": condition.type,
                    "status": condition.status,
                    "reason": condition.reason,
                    "message": condition.message
                })

        # -----------------------------
        # Restart Count
        # -----------------------------

        restart_count = 0

        try:
            pods = v1.list_namespaced_pod(
                deployment.metadata.namespace,
                label_selector=",".join(
                    [
                        f"{k}={v}"
                        for k, v in deployment.spec.selector.match_labels.items()
                    ]
                )
            ).items

            for pod in pods:

                if pod.status.container_statuses:

                    for container in pod.status.container_statuses:
                        restart_count += container.restart_count

        except Exception:
            restart_count = 0

        # -----------------------------
        # Warning Events
        # -----------------------------

        warning_events = 0

        try:
            events = v1.list_namespaced_event(
                deployment.metadata.namespace
            ).items

            for event in events:

                if (
                    event.type == "Warning"
                    and deployment.metadata.name in event.involved_object.name
                ):
                    warning_events += 1

        except Exception:
            warning_events = 0

        results.append({

            "namespace": deployment.metadata.namespace,

            "name": deployment.metadata.name,

            "desired": desired,

            "ready": f"{ready}/{desired}",

            "available": available,

            "updated": updated,

            "unavailable": unavailable,

            "restart_count": restart_count,

            "warning_events": warning_events,

            "conditions": conditions,

            "age": age,

            "status": (
                "Healthy"
                if available == desired
                else "Unhealthy"
            )
        })

    return results