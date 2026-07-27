from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException


def get_events():
    """
    Retrieve Kubernetes events from all namespaces.
    """

    # Load Kubernetes configuration
    try:
        config.load_kube_config()
    except ConfigException:
        # Use this when running inside a Kubernetes cluster
        config.load_incluster_config()

    v1 = client.CoreV1Api()

    events = v1.list_event_for_all_namespaces()

    results = []

    for event in events.items:
        results.append({
            "namespace": event.metadata.namespace,
            "name": event.involved_object.name,
            "kind": event.involved_object.kind,
            "reason": event.reason,
            "message": event.message,
            "type": event.type,
            "count": event.count,
            "first_seen": str(event.first_timestamp),
            "last_seen": str(event.last_timestamp),
            "time": str(
                event.last_timestamp
                or event.event_time
                or event.first_timestamp
            )
        })

    return results