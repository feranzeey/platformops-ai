from datetime import datetime, timezone

from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException


def load_config():
    """
    Load Kubernetes configuration.

    - Uses in-cluster configuration when running inside Kubernetes.
    - Falls back to the local kubeconfig when running locally.
    """
    try:
        config.load_incluster_config()
    except ConfigException:
        config.load_kube_config()


load_config()

v1 = client.CoreV1Api()
apps = client.AppsV1Api()


def get_pods():
    pods = v1.list_pod_for_all_namespaces().items

    problem_pods = []
    logs = ""

    for pod in pods:

        phase = pod.status.phase
        reason = ""

        if pod.status.container_statuses:
            for container in pod.status.container_statuses:

                if container.state.waiting:
                    reason = container.state.waiting.reason or ""

                elif container.state.terminated:
                    reason = container.state.terminated.reason or ""

                if reason:
                    break

        unhealthy = (
            phase != "Running"
            or reason in [
                "CrashLoopBackOff",
                "ImagePullBackOff",
                "ErrImagePull",
                "CreateContainerConfigError",
                "ContainerCreating",
            ]
        )

        if unhealthy:

            problem_pods.append({
                "namespace": pod.metadata.namespace,
                "name": pod.metadata.name,
                "phase": phase,
                "reason": reason
            })

            try:
                logs = v1.read_namespaced_pod_log(
                    name=pod.metadata.name,
                    namespace=pod.metadata.namespace,
                    tail_lines=200
                )
            except Exception:
                logs = ""

            break

    return {
        "total": len(pods),
        "healthy": len(pods) - len(problem_pods),
        "problem_count": len(problem_pods),
        "problems": problem_pods,
        "logs": logs
    }


def get_deployments():
    deployments = apps.list_deployment_for_all_namespaces().items

    results = []

    for deployment in deployments:

        desired = deployment.spec.replicas or 0
        available = deployment.status.available_replicas or 0
        updated = deployment.status.updated_replicas or 0

        created = deployment.metadata.creation_timestamp

        age = ""
        if created:
            age = str(datetime.now(timezone.utc) - created).split(".")[0]

        results.append({
            "namespace": deployment.metadata.namespace,
            "name": deployment.metadata.name,
            "ready": f"{available}/{desired}",
            "up_to_date": updated,
            "available": available,
            "age": age,
            "status": "Healthy" if available == desired else "Unhealthy"
        })

    return results


def get_services():
    services = v1.list_service_for_all_namespaces().items

    results = []

    for service in services:

        created = service.metadata.creation_timestamp

        age = ""
        if created:
            age = str(datetime.now(timezone.utc) - created).split(".")[0]

        ports = ",".join(
            f"{p.port}/{p.protocol}"
            for p in service.spec.ports
        )

        results.append({
            "namespace": service.metadata.namespace,
            "name": service.metadata.name,
            "type": service.spec.type,
            "cluster_ip": service.spec.cluster_ip,
            "ports": ports,
            "age": age
        })

    return results


def get_nodes():
    nodes = v1.list_node().items

    results = []

    for node in nodes:

        status = "NotReady"

        for condition in node.status.conditions:
            if condition.type == "Ready":
                status = "Ready" if condition.status == "True" else "NotReady"

        created = node.metadata.creation_timestamp

        age = ""
        if created:
            age = str(datetime.now(timezone.utc) - created).split(".")[0]

        roles = node.metadata.labels.get(
            "kubernetes.io/role",
            node.metadata.labels.get(
                "node-role.kubernetes.io/control-plane",
                ""
            )
        )

        results.append({
            "name": node.metadata.name,
            "status": status,
            "roles": roles,
            "age": age,
            "version": node.status.node_info.kubelet_version
        })

    return results


def get_namespaces():
    namespaces = v1.list_namespace().items

    results = []

    for namespace in namespaces:

        created = namespace.metadata.creation_timestamp

        age = ""
        if created:
            age = str(datetime.now(timezone.utc) - created).split(".")[0]

        results.append({
            "name": namespace.metadata.name,
            "status": namespace.status.phase,
            "age": age
        })

    return results