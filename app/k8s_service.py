from datetime import datetime, timezone

from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException

# ---------------------------------------------------
# Load Kubernetes Configuration
# ---------------------------------------------------

try:
    config.load_incluster_config()
except ConfigException:
    config.load_kube_config()

v1 = client.CoreV1Api()
apps = client.AppsV1Api()


# ---------------------------------------------------
# Pods
# ---------------------------------------------------

def get_pods():

    pods = v1.list_pod_for_all_namespaces().items

    problems = []
    logs = []

    healthy = 0

    for pod in pods:

        namespace = pod.metadata.namespace
        name = pod.metadata.name

        phase = pod.status.phase

        reason = ""

        if pod.status.container_statuses:

            for container in pod.status.container_statuses:

                waiting = container.state.waiting

                if waiting:
                    reason = waiting.reason

        if phase == "Running" and reason == "":
            healthy += 1
            continue

        try:

            log = v1.read_namespaced_pod_log(
                name=name,
                namespace=namespace,
                tail_lines=20
            )

            logs.append(
                f"\n===== {namespace}/{name} =====\n{log}"
            )

        except Exception:

            pass

        problems.append({

            "namespace": namespace,
            "name": name,
            "phase": phase,
            "reason": reason or phase,
            "node": pod.spec.node_name,
            "host_ip": pod.status.host_ip,
            "pod_ip": pod.status.pod_ip

        })

    return {

        "total": len(pods),
        "healthy": healthy,
        "problem_count": len(problems),
        "problems": problems,
        "logs": "\n".join(logs)

    }


# ---------------------------------------------------
# Deployments
# ---------------------------------------------------

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

        conditions = []

        if deployment.status.conditions:

            for condition in deployment.status.conditions:

                conditions.append({

                    "type": condition.type,
                    "status": condition.status,
                    "reason": condition.reason,
                    "message": condition.message

                })

        restart_count = 0

        try:

            selector = ",".join(
                f"{k}={v}"
                for k, v in deployment.spec.selector.match_labels.items()
            )

            pods = v1.list_namespaced_pod(
                namespace=deployment.metadata.namespace,
                label_selector=selector
            ).items

            for pod in pods:

                if pod.status.container_statuses:

                    for container in pod.status.container_statuses:

                        restart_count += container.restart_count

        except Exception:

            restart_count = 0

        warning_events = 0

        try:

            events = v1.list_namespaced_event(
                deployment.metadata.namespace
            ).items

            for event in events:

                if (
                    event.type == "Warning"
                    and event.involved_object
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


# ---------------------------------------------------
# Services
# ---------------------------------------------------

def get_services():

    services = v1.list_service_for_all_namespaces().items

    results = []

    for service in services:

        ports = []

        if service.spec.ports:

            for port in service.spec.ports:

                ports.append(str(port.port))

        results.append({

            "namespace": service.metadata.namespace,
            "name": service.metadata.name,
            "type": service.spec.type,
            "cluster_ip": service.spec.cluster_ip,
            "ports": ", ".join(ports)

        })

    return results


# ---------------------------------------------------
# Nodes
# ---------------------------------------------------

def get_nodes():

    nodes = v1.list_node().items

    results = []

    for node in nodes:

        status = "Unknown"

        for condition in node.status.conditions:

            if condition.type == "Ready":

                status = "Ready" if condition.status == "True" else "Not Ready"

        labels = node.metadata.labels

        role = "Worker"

        if "node-role.kubernetes.io/control-plane" in labels:
            role = "Control Plane"

        elif "node-role.kubernetes.io/master" in labels:
            role = "Master"

        results.append({

            "name": node.metadata.name,
            "status": status,
            "roles": role,
            "version": node.status.node_info.kubelet_version

        })

    return results


# ---------------------------------------------------
# Namespaces
# ---------------------------------------------------

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