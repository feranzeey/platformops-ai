from datetime import datetime


def generate_incident_report(investigation):
    """
    Generate a professional AI incident report.
    """

    report = {
        "title": "PlatformOps AI Incident Report",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        "application": investigation["title"],

        "severity": investigation["severity"],

        "issue": investigation["issue"],

        "impact": investigation["impact"],

        "confidence": investigation.get("confidence", "Unknown"),

        "evidence": investigation["evidence"],

        "commands": investigation["command"].split("\n")
    }

    return report