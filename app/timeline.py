from datetime import datetime


# ==========================================================
# Build AI Incident Timeline
# ==========================================================

def build_incident_timeline(events):
    """
    Converts Kubernetes events into a chronological timeline.
    """

    timeline = []

    for event in events:

        timestamp = (
            event.get("time")
            or event.get("last_seen")
            or event.get("first_seen")
            or ""
        )

        timeline.append({

            "time": timestamp,

            "namespace": event.get("namespace"),

            "resource": event.get("name"),

            "kind": event.get("kind"),

            "reason": event.get("reason"),

            "message": event.get("message"),

            "type": event.get("type"),

            "count": event.get("count", 1)

        })

    timeline.sort(
        key=lambda x: x["time"]
    )

    return timeline


# ==========================================================
# AI Timeline Summary
# ==========================================================

def summarize_timeline(timeline):
    """
    Generates an executive summary from the timeline.
    """

    if not timeline:

        return {

            "summary": "No Kubernetes events detected.",

            "critical": 0,

            "warnings": 0,

            "normal": 0

        }

    warnings = 0
    critical = 0
    normal = 0

    latest = timeline[-1]

    for event in timeline:

        event_type = (event.get("type") or "").lower()

        if event_type == "warning":

            warnings += 1

        elif event_type == "critical":

            critical += 1

        else:

            normal += 1

    summary = (

        f"PlatformOps AI analyzed "

        f"{len(timeline)} Kubernetes events. "

        f"{warnings} warning events detected. "

        f"Latest activity: "

        f"{latest.get('reason')} "

        f"on "

        f"{latest.get('resource')}."

    )

    return {

        "summary": summary,

        "critical": critical,

        "warnings": warnings,

        "normal": normal,

        "latest": latest

    }


# ==========================================================
# AI Incident Story
# ==========================================================

def generate_incident_story(timeline):
    """
    Produces a readable incident story for the dashboard.
    """

    if not timeline:

        return []

    story = []

    for event in timeline:

        story.append({

            "time": event["time"],

            "title": event["reason"],

            "description": event["message"]

        })

    return story