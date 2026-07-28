from datetime import datetime, timezone

from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException


# ==========================================================
# Load Kubernetes Configuration
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
# Restart Deployment
# ==========================================================

def restart_deployment(name, namespace="default"):
    """
    Perform a rolling restart of a deployment.
    """

    try:

        _load_k8s_config()

        apps = client.AppsV1Api()

        timestamp = datetime.now(timezone.utc).isoformat()

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

        apps.patch_namespaced_deployment(
            name=name,
            namespace=namespace,
            body=body
        )

        return {
            "success": True,
            "action": "Restart Deployment",
            "deployment": name,
            "namespace": namespace,
            "message": (
                f"Deployment '{name}' restarted successfully."
            )
        }

    except Exception as e:

        return {
            "success": False,
            "action": "Restart Deployment",
            "deployment": name,
            "namespace": namespace,
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
                f"Deployment scaled to {replicas} replicas."
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
            "PlatformOps AI could not determine an automatic repair."
        )
    }