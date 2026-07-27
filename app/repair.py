from datetime import datetime, timezone

from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException


def _load_k8s_config():
    """
    Use in-cluster config when running as a pod (Step 9 deployment),
    fall back to local kubeconfig when running on a laptop (dev/Minikube).
    """
    try:
        config.load_incluster_config()
    except ConfigException:
        config.load_kube_config()


def restart_deployment(name, namespace="default"):
    """
    Trigger a rolling restart of a deployment by patching its pod
    template annotations. Equivalent to:

        kubectl rollout restart deployment <name>
    """

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

    return f"{name} restarted successfully."