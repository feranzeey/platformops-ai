import os
import yaml
from datetime import datetime, timezone

from flask import Flask, render_template, request

from k8s_service import (
    get_pods,
    get_deployments,
    get_services,
    get_nodes,
    get_namespaces
)

from events import get_events
from prometheus import get_metrics
from github_service import get_latest_commit
from ai import analyze_cluster
from health import calculate_health
from severity import calculate_severity
from repair import restart_deployment

app = Flask(__name__)

INCIDENTS_DIR = "incidents"


def save_incident(pod_name, problem, root_cause, action, status="resolved"):
    """
    Persist a single incident to a YAML file under incidents/,
    named by today's date. Multiple incidents on the same day are
    appended as a list.
    """

    os.makedirs(INCIDENTS_DIR, exist_ok=True)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filepath = os.path.join(INCIDENTS_DIR, f"{today}.yaml")

    entry = {
        "incident": {"pod": pod_name},
        "problem": problem,
        "rootcause": root_cause,
        "action": action,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    existing = []

    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            loaded = yaml.safe_load(f)
            if isinstance(loaded, list):
                existing = loaded
            elif loaded:
                existing = [loaded]

    existing.append(entry)

    with open(filepath, "w") as f:
        yaml.dump(existing, f, sort_keys=False)


def load_incident_timeline(limit=10):
    """
    Read all incident YAML files and return a flat, most-recent-first
    list of incidents for display on the dashboard.
    """

    if not os.path.isdir(INCIDENTS_DIR):
        return []

    timeline = []

    for filename in sorted(os.listdir(INCIDENTS_DIR), reverse=True):

        if not filename.endswith(".yaml"):
            continue

        filepath = os.path.join(INCIDENTS_DIR, filename)

        with open(filepath, "r") as f:
            loaded = yaml.safe_load(f) or []

        if isinstance(loaded, dict):
            loaded = [loaded]

        for item in loaded:
            item["date"] = filename.replace(".yaml", "")
            timeline.append(item)

    timeline.sort(key=lambda i: i.get("timestamp", ""), reverse=True)

    return timeline[:limit]


@app.route("/", methods=["GET", "POST"])
def home():

    report = None

    if request.method == "POST":

        # ------------------------
        # Kubernetes Resources
        # ------------------------

        pods = get_pods()
        deployments = get_deployments()
        services = get_services()
        nodes = get_nodes()
        namespaces = get_namespaces()
        events = get_events()

        # ------------------------
        # Prometheus Metrics
        # ------------------------

        metrics = get_metrics()

        # ------------------------
        # GitHub Activity
        # ------------------------

        github = get_latest_commit()

        # ------------------------
        # Cluster Health
        # ------------------------

        health = calculate_health(
            pods,
            deployments,
            nodes,
            events,
            metrics
        )

        # ------------------------
        # Incident Severity
        # ------------------------

        severity = calculate_severity(
            logs=pods["logs"],
            events=events,
            metrics=metrics
        )

        # ------------------------
        # AI Incident Analysis
        # ------------------------

        analysis = analyze_cluster(
            logs=pods["logs"],
            events=events,
            metrics=metrics,
            github=github
        )

        # Add calculated severity to AI response
        analysis["severity"] = severity

        # ------------------------
        # Log this analysis to the incident timeline
        # (only when the AI actually found a problem worth recording)
        # ------------------------

        if severity != "LOW":
            save_incident(
                pod_name=analysis.get("affected_pod", "unknown"),
                problem=analysis.get("root_cause", "Unclassified issue"),
                root_cause=analysis.get("root_cause", "Unknown"),
                action="Analyzed by PlatformOps AI",
                status="open"
            )

        # ------------------------
        # Dashboard Report
        # ------------------------

        report = {
            "pods": pods,
            "deployments": deployments,
            "services": services,
            "nodes": nodes,
            "namespaces": namespaces,
            "events": events,
            "metrics": metrics,
            "github": github,
            "health": health,
            "analysis": analysis,
            "severity": severity,
            "timeline": load_incident_timeline()
        }

    return render_template(
        "index.html",
        report=report
    )


@app.route("/repair/<deployment>")
def repair(deployment):

    message = restart_deployment(deployment)

    save_incident(
        pod_name=deployment,
        problem="Manual/AI-triggered repair",
        root_cause="See most recent AI analysis",
        action=message,
        status="resolved"
    )

    return message


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )