import time
from datetime import datetime, timezone

from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException


# ==========================================================
# Kubernetes Configuration
# ==========================================================

def _load_k8s_config():
    """
    Load Kubernetes configuration.

    Uses in-cluster configuration when running inside Kubernetes.
    Falls back to local kubeconfig when running locally.
    """

    try:
        config.load_incluster_config()

    except ConfigException:
        config.load_kube_config()


# ==========================================================
# Deployment Recovery Verification
# ==========================================================

def _wait_for_deployment_recovery(
    apps,
    core,
    name,
    namespace,
    target_generation,
    timeout=60,
    interval=2
):
    """
    Wait for the deployment rollout to complete and verify
    that the deployment and its pods are ready.
    """

    start_time = time.time()

    while time.time() - start_time < timeout:

        try:

            deployment = apps.read_namespaced_deployment(
                name=name,
                namespace=namespace
            )

            status = deployment.status
            spec = deployment.spec

            desired_replicas = spec.replicas or 0
            ready_replicas = status.ready_replicas or 0
            available_replicas = status.available_replicas or 0
            updated_replicas = status.updated_replicas or 0
            observed_generation = (
                status.observed_generation or 0
            )

            deployment_ready = (
                observed_generation >= target_generation
                and updated_replicas >= desired_replicas
                and ready_replicas >= desired_replicas
                and available_replicas >= desired_replicas
            )

            # --------------------------------------------------
            # Verify pod readiness
            # --------------------------------------------------

            pods_ready = True
            running_pods = 0

            selector = {}

            if (
                deployment.spec
                and deployment.spec.selector
                and deployment.spec.selector.match_labels
            ):

                selector = deployment.spec.selector.match_labels

            if selector:

                label_selector = ",".join(
                    f"{key}={value}"
                    for key, value in selector.items()
                )

                pods = core.list_namespaced_pod(
                    namespace=namespace,
                    label_selector=label_selector
                ).items

                if desired_replicas > 0:

                    running_pods = sum(
                        1
                        for pod in pods
                        if pod.status.phase == "Running"
                    )

                    ready_pods = 0

                    for pod in pods:

                        if pod.status.phase != "Running":
                            continue

                        conditions = (
                            pod.status.conditions or []
                        )

                        is_ready = any(
                            condition.type == "Ready"
                            and condition.status == "True"
                            for condition in conditions
                        )

                        if is_ready:
                            ready_pods += 1

                    pods_ready = (
                        running_pods >= desired_replicas
                        and ready_pods >= desired_replicas
                    )

            # --------------------------------------------------
            # Final recovery confirmation
            # --------------------------------------------------

            if deployment_ready and pods_ready:

                return {
                    "recovered": True,
                    "desired_replicas": desired_replicas,
                    "ready_replicas": ready_replicas,
                    "available_replicas": available_replicas,
                    "updated_replicas": updated_replicas,
                    "running_pods": running_pods
                }

        except Exception:
            pass

        time.sleep(interval)

    return {
        "recovered": False,
        "message": (
            "Deployment rollout did not reach the required "
            "ready state within the recovery timeout."
        )
    }


# ==========================================================
# Restart Deployment
# ==========================================================

def restart_deployment(name, namespace="default"):
    """
    Perform a rolling restart of a deployment and verify
    that Kubernetes successfully recovers it.
    """

    try:

        _load_k8s_config()

        apps = client.AppsV1Api()
        core = client.CoreV1Api()

        # --------------------------------------------------
        # Confirm deployment exists in the requested namespace
        # --------------------------------------------------

        deployment = apps.read_namespaced_deployment(
            name=name,
            namespace=namespace
        )

        target_generation = (
            deployment.metadata.generation or 0
        )

        # --------------------------------------------------
        # Trigger rolling restart
        # --------------------------------------------------

        timestamp = datetime.now(
            timezone.utc
        ).isoformat()

        body = {
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "kubectl.kubernetes.io/restartedAt": timestamp
                        }
                    }
                }
            }
        }

        patched_deployment = (
            apps.patch_namespaced_deployment(
                name=name,
                namespace=namespace,
                body=body
            )
        )

        target_generation = (
            patched_deployment.metadata.generation
            or target_generation
        )

        # --------------------------------------------------
        # Wait for recovery
        # --------------------------------------------------

        recovery = _wait_for_deployment_recovery(
            apps=apps,
            core=core,
            name=name,
            namespace=namespace,
            target_generation=target_generation
        )

        # --------------------------------------------------
        # Recovery confirmed
        # --------------------------------------------------

        if recovery.get("recovered"):

            desired = recovery.get(
                "desired_replicas",
                0
            )

            ready = recovery.get(
                "ready_replicas",
                0
            )

            return {
                "success": True,
                "action": "Restart Deployment",
                "deployment": name,
                "namespace": namespace,
                "status": "HEALTHY",
                "recovery_confirmed": True,
                "message": (
                    f"Deployment '{name}' restarted successfully "
                    f"in namespace '{namespace}'. "
                    f"Recovery confirmed: {ready}/{desired} "
                    f"replicas ready."
                )
            }

        # --------------------------------------------------
        # Restart happened but recovery failed
        # --------------------------------------------------

        return {
            "success": False,
            "action": "Restart Deployment",
            "deployment": name,
            "namespace": namespace,
            "status": "ACTION REQUIRED",
            "recovery_confirmed": False,
            "message": recovery.get(
                "message",
                "Deployment restart completed but recovery could not be confirmed."
            )
        }

    except Exception as e:

        return {
            "success": False,
            "action": "Restart Deployment",
            "deployment": name,
            "namespace": namespace,
            "status": "ACTION REQUIRED",
            "recovery_confirmed": False,
            "message": str(e)
        }


# ==========================================================
# Scale Deployment
# ==========================================================

def scale_deployment(name, replicas, namespace="default"):
    """
    Scale a deployment.
    """

    try:

        _load_k8s_config()

        apps = client.AppsV1Api()

        body = {
            "spec": {
                "replicas": replicas
            }
        }

        apps.patch_namespaced_deployment_scale(
            name=name,
            namespace=namespace,
            body=body
        )

        return {
            "success": True,
            "action": "Scale Deployment",
            "deployment": name,
            "namespace": namespace,
            "message": (
                f"Deployment '{name}' scaled to "
                f"{replicas} replicas."
            )
        }

    except Exception as e:

        return {
            "success": False,
            "action": "Scale Deployment",
            "deployment": name,
            "namespace": namespace,
            "message": str(e)
        }


# ==========================================================
# Delete Failed Pod
# ==========================================================

def delete_pod(name, namespace="default"):
    """
    Delete a pod.
    Kubernetes automatically recreates it when managed
    by a Deployment.
    """

    try:

        _load_k8s_config()

        core = client.CoreV1Api()

        core.delete_namespaced_pod(
            name=name,
            namespace=namespace
        )

        return {
            "success": True,
            "action": "Delete Failed Pod",
            "deployment": name,
            "namespace": namespace,
            "message": (
                f"Pod '{name}' deleted successfully."
            )
        }

    except Exception as e:

        return {
            "success": False,
            "action": "Delete Failed Pod",
            "deployment": name,
            "namespace": namespace,
            "message": str(e)
        }


# ==========================================================
# Pause Deployment
# ==========================================================

def pause_deployment(name, namespace="default"):
    """
    Pause rollout of a deployment.
    """

    try:

        _load_k8s_config()

        apps = client.AppsV1Api()

        body = {
            "spec": {
                "paused": True
            }
        }

        apps.patch_namespaced_deployment(
            name=name,
            namespace=namespace,
            body=body
        )

        return {
            "success": True,
            "action": "Pause Deployment",
            "deployment": name,
            "namespace": namespace,
            "message": (
                f"Deployment '{name}' has been paused."
            )
        }

    except Exception as e:

        return {
            "success": False,
            "action": "Pause Deployment",
            "deployment": name,
            "namespace": namespace,
            "message": str(e)
        }


# ==========================================================
# Resume Deployment
# ==========================================================

def resume_deployment(name, namespace="default"):
    """
    Resume a paused deployment.
    """

    try:

        _load_k8s_config()

        apps = client.AppsV1Api()

        body = {
            "spec": {
                "paused": False
            }
        }

        apps.patch_namespaced_deployment(
            name=name,
            namespace=namespace,
            body=body
        )

        return {
            "success": True,
            "action": "Resume Deployment",
            "deployment": name,
            "namespace": namespace,
            "message": (
                f"Deployment '{name}' resumed successfully."
            )
        }

    except Exception as e:

        return {
            "success": False,
            "action": "Resume Deployment",
            "deployment": name,
            "namespace": namespace,
            "message": str(e)
        }


# ==========================================================
# AI Auto Repair
# ==========================================================

def auto_repair(root_cause, deployment, namespace="default"):
    """
    PlatformOps AI automatically chooses
    the best repair action.
    """

    cause = root_cause.lower()

    if "crashloop" in cause:

        return restart_deployment(
            deployment,
            namespace
        )

    elif "unavailable" in cause:

        return restart_deployment(
            deployment,
            namespace
        )

    elif "warning" in cause:

        return restart_deployment(
            deployment,
            namespace
        )

    elif "replica" in cause:

        return scale_deployment(
            deployment,
            replicas=1,
            namespace=namespace
        )

    return {
        "success": False,
        "action": "Auto Repair",
        "deployment": deployment,
        "namespace": namespace,
        "message": (
            "PlatformOps AI could not determine "
            "an automatic repair."
        )
    }