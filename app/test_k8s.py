from k8s_service import (
    get_nodes,
    get_pods,
    get_deployments,
    get_services,
    get_namespaces,
)

print("===== NODES =====")
print(get_nodes())

print("===== PODS =====")
print(get_pods())

print("===== DEPLOYMENTS =====")
print(get_deployments())

print("===== SERVICES =====")
print(get_services())

print("===== NAMESPACES =====")
print(get_namespaces())