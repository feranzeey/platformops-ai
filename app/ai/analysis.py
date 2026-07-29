"""
AI Investigation Engine - analysis.py

Analyzes Kubernetes logs, events, Prometheus metrics, and GitHub deployment
info to produce a root cause, severity rating, and remediation plan.
"""

# Thresholds used when reasoning about Prometheus metrics
CPU_HIGH_THRESHOLD = 85
MEMORY_HIGH_THRESHOLD = 85

# Event reasons that map to a known root cause and fix commands
KNOWN_ISSUES = {
    "CrashLoopBackOff": {
        "root_cause": "Container is repeatedly crashing after startup.",
        "severity": "HIGH",
        "recommendation": [
            "Inspect container logs for the crash reason.",
            "Check recent image or config changes.",
            "Verify environment variables and secrets are correctly mounted."
        ],
        "fix_commands": [
            "kubectl logs {pod} --previous",
            "kubectl describe pod {pod}",
            "kubectl rollout restart deployment {pod}"
        ]
    },
    "ImagePullBackOff": {
        "root_cause": "Kubernetes cannot pull the container image.",
        "severity": "HIGH",
        "recommendation": [
            "Verify the image name and tag are correct.",
            "Check registry credentials and imagePullSecrets.",
            "Confirm the image exists in the target registry."
        ],
        "fix_commands": [
            "kubectl describe pod {pod}",
            "kubectl get events --field-selector involvedObject.name={pod}",
            "kubectl edit deployment {pod}"
        ]
    },
    "ErrImagePull": {
        "root_cause": "Kubernetes cannot pull the container image.",
        "severity": "HIGH",
        "recommendation": [
            "Verify the image name and tag are correct.",
            "Check registry credentials and imagePullSecrets.",
            "Confirm the image exists in the target registry."
        ],
        "fix_commands": [
            "kubectl describe pod {pod}",
            "kubectl get events --field-selector involvedObject.name={pod}",
            "kubectl edit deployment {pod}"
        ]
    },
    "Failed": {
        "root_cause": "Deployment failed to reach a healthy state.",
        "severity": "HIGH",
        "recommendation": [
            "Review deployment rollout status.",
            "Check for failing readiness or liveness probes.",
            "Roll back to the last known-good revision if needed."
        ],
        "fix_commands": [
            "kubectl rollout status deployment {pod}",
            "kubectl describe deployment {pod}",
            "kubectl rollout undo deployment {pod}"
        ]
    },
    "Unhealthy": {
        "root_cause": "Readiness or liveness probe is failing.",
        "severity": "MEDIUM",
        "recommendation": [
            "Check the probe path, port, and timing configuration.",
            "Verify the application is listening and healthy internally.",
            "Review recent config or dependency changes."
        ],
        "fix_commands": [
            "kubectl describe pod {pod}",
            "kubectl logs {pod}",
            "kubectl exec -it {pod} -- curl localhost:<port>/healthz"
        ]
    },
    "OOMKilling": {
        "root_cause": "Container was terminated for exceeding its memory limit.",
        "severity": "HIGH",
        "recommendation": [
            "Increase the memory limit if usage is expected.",
            "Investigate the workload for a memory leak.",
            "Review recent traffic or load changes."
        ],
        "fix_commands": [
            "kubectl describe pod {pod}",
            "kubectl top pod {pod}",
            "kubectl edit deployment {pod}"
        ]
    }
}

DEFAULT_PREVENTION = [
    "Enable monitoring and alerting for this workload.",
    "Set resource requests and limits appropriately.",
    "Add pre-deployment health checks to CI/CD."
]


def _extract_affected_pod(events):
    """Return the pod name tied to the most relevant event, if any."""
    for event in events or []:
        involved = event.get("involvedObject", {}) if isinstance(event, dict) else {}
        if involved.get("kind") == "Pod" and involved.get("name"):
            return involved["name"]
    return "unknown"


def _match_known_issue(events):
    """Find the highest-priority known issue reflected in the event stream."""
    reasons = [e.get("reason") for e in (events or []) if isinstance(e, dict)]
    for reason, issue in KNOWN_ISSUES.items():
        if reason in reasons:
            return reason, issue
    return None, None


def _check_resource_exhaustion(metrics):
    """Flag CPU/memory exhaustion from Prometheus metrics, if present."""
    if not metrics:
        return None
    cpu = metrics.get("cpu_usage_percent")
    memory = metrics.get("memory_usage_percent")

    if cpu is not None and cpu >= CPU_HIGH_THRESHOLD:
        return {
            "root_cause": f"Node/pod CPU usage is critically high ({cpu}%).",
            "severity": "HIGH",
            "recommendation": [
                "Scale the deployment horizontally or vertically.",
                "Profile the application for CPU-intensive code paths.",
                "Review recent traffic spikes."
            ],
            "fix_commands": [
                "kubectl top pods",
                "kubectl get hpa",
                "kubectl scale deployment {pod} --replicas=<n>"
            ]
        }
    if memory is not None and memory >= MEMORY_HIGH_THRESHOLD:
        return {
            "root_cause": f"Node/pod memory usage is critically high ({memory}%).",
            "severity": "HIGH",
            "recommendation": [
                "Increase memory limits or scale the deployment.",
                "Investigate for memory leaks.",
                "Review recent traffic or load changes."
            ],
            "fix_commands": [
                "kubectl top pods",
                "kubectl describe pod {pod}",
                "kubectl edit deployment {pod}"
            ]
        }
    return None


def _correlate_github(github):
    """Note whether a recent commit may correlate with the incident."""
    if not github or not github.get("latest_commit"):
        return None
    return (
        f"Latest commit '{github.get('commit_message', 'unknown')}' by "
        f"{github.get('commit_author', 'unknown')} on {github.get('commit_date', 'unknown')} "
        f"may be related to this incident."
    )


def analyze_cluster(logs, events, metrics, github):
    """
    Analyze cluster logs, events, metrics, and GitHub deployment info to
    produce a root cause, severity, confidence, and remediation plan.
    """
    affected_pod = _extract_affected_pod(events)
    reason, issue = _match_known_issue(events)

    if issue is None:
        issue = _check_resource_exhaustion(metrics)

    github_note = _correlate_github(github)

    if issue is None:
        return {
            "incident_summary": "PlatformOps AI completed cluster analysis. No critical issue detected.",
            "affected_pod": affected_pod,
            "root_cause": "No critical issue detected.",
            "severity": "LOW",
            "confidence": "95%",
            "recommendation": [
                "Monitor cluster health.",
                "Review Kubernetes events.",
                "Verify deployment status."
            ],
            "prevention": DEFAULT_PREVENTION,
            "fix_commands": [
                "kubectl get pods -A",
                "kubectl describe pod {pod}".format(pod=affected_pod),
                "kubectl logs {pod}".format(pod=affected_pod)
            ]
        }

    summary_reason = reason if reason else "resource exhaustion"
    result = {
        "incident_summary": f"PlatformOps AI detected an issue: {summary_reason} on pod '{affected_pod}'.",
        "affected_pod": affected_pod,
        "root_cause": issue["root_cause"],
        "severity": issue["severity"],
        "confidence": "88%",
        "recommendation": issue["recommendation"],
        "prevention": DEFAULT_PREVENTION,
        "fix_commands": [cmd.format(pod=affected_pod) for cmd in issue["fix_commands"]]
    }

    if github_note:
        result["incident_summary"] += f" {github_note}"

    return result