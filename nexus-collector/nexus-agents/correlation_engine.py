import json
from datetime import datetime, timedelta


CORRELATION_WINDOW_MINUTES = 2


def load_json_file(filename, default_value):
    """
    Safely loads a JSON file.
    If file does not exist or is empty, returns default value.
    """
    try:
        with open(filename, "r") as file:
            return json.load(file)
    except Exception:
        return default_value


def save_json_file(filename, data):
    """
    Saves data into a JSON file.
    """
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)


def parse_timestamp(timestamp):
    """
    Converts timestamp string into Python datetime object.
    Handles timestamps with or without microseconds.
    """
    if not timestamp:
        return None

    try:
        return datetime.fromisoformat(timestamp)
    except ValueError:
        return None


def happened_within_window(time_a, time_b, minutes):
    """
    Checks whether two alerts happened close to each other.
    Example:
    backend CPU spike at 10:00
    database restart at 10:01
    Difference = 1 minute
    So it is correlated.
    """
    if not time_a or not time_b:
        return False

    difference = abs(time_a - time_b)
    return difference <= timedelta(minutes=minutes)


def pods_are_connected(pod_a, pod_b, dependency_map):
    """
    Checks whether pod_a communicates with pod_b.

    Example dependency_map:
    {
        "frontend": ["backend"],
        "backend": ["database"]
    }

    This function checks both directions:
    - pod_a depends on pod_b
    - pod_b depends on pod_a
    """

    pod_a_dependencies = dependency_map.get(pod_a, [])
    pod_b_dependencies = dependency_map.get(pod_b, [])

    if pod_b in pod_a_dependencies:
        return True

    if pod_a in pod_b_dependencies:
        return True

    return False


def get_alert_type(alert):
    """
    Converts agent name into a simple alert type.
    """
    agent = alert.get("agent", "")

    if agent == "CPUAgent":
        return "cpu_spike"

    if agent == "MemoryAgent":
        return "memory_pressure"

    if agent == "RestartAgent":
        return "restart"

    if agent == "StatusAgent":
        return "status_issue"

    return "unknown"


def correlate_alerts(alerts, dependency_map):
    """
    Main correlation logic.

    Rule:
    If pod A has CPU/memory/status problem
    AND pod B restarted
    AND both happened within 2 minutes
    AND pod A communicates with pod B
    THEN create dependency impact insight.
    """

    correlations = []

    for alert_a in alerts:
        for alert_b in alerts:
            if alert_a == alert_b:
                continue

            pod_a = alert_a.get("pod")
            pod_b = alert_b.get("pod")

            namespace_a = alert_a.get("namespace")
            namespace_b = alert_b.get("namespace")

            if not pod_a or not pod_b:
                continue

            if pod_a == pod_b:
                continue

            if namespace_a != namespace_b:
                continue

            alert_a_type = get_alert_type(alert_a)
            alert_b_type = get_alert_type(alert_b)

            time_a = parse_timestamp(alert_a.get("timestamp"))
            time_b = parse_timestamp(alert_b.get("timestamp"))

            time_match = happened_within_window(
                time_a,
                time_b,
                CORRELATION_WINDOW_MINUTES
            )

            dependency_match = pods_are_connected(
                pod_a,
                pod_b,
                dependency_map
            )

            rule_match = (
                alert_a_type in ["cpu_spike", "memory_pressure", "status_issue"]
                and alert_b_type == "restart"
                and time_match
                and dependency_match
            )

            if rule_match:
                correlation = {
                    "type": "dependency_impact",
                    "severity": "high",
                    "namespace": namespace_a,
                    "source_pod": pod_a,
                    "related_pod": pod_b,
                    "source_alert": alert_a.get("message"),
                    "related_alert": alert_b.get("message"),
                    "message": (
                        f"{pod_a} had a {alert_a_type.replace('_', ' ')} "
                        f"within {CORRELATION_WINDOW_MINUTES} minutes of "
                        f"{pod_b} restart. Since these pods communicate, "
                        f"this may indicate dependency impact."
                    ),
                    "timestamp": datetime.utcnow().isoformat()
                }

                correlations.append(correlation)

    return remove_duplicate_correlations(correlations)


def remove_duplicate_correlations(correlations):
    """
    Removes duplicate correlation results.
    """
    seen = set()
    unique_correlations = []

    for item in correlations:
        key = (
            item["type"],
            item["namespace"],
            item["source_pod"],
            item["related_pod"]
        )

        if key not in seen:
            seen.add(key)
            unique_correlations.append(item)

    return unique_correlations


def main():
    alerts = load_json_file("alerts.json", [])
    dependency_map = load_json_file("dependencies.json", {})

    correlations = correlate_alerts(alerts, dependency_map)

    save_json_file("correlations.json", correlations)

    print("Correlation Engine Completed")
    print("-" * 70)

    if not correlations:
        print("No dependency correlations detected.")

    for correlation in correlations:
        print(
            f"[{correlation['severity'].upper()}] "
            f"{correlation['namespace']} | "
            f"{correlation['source_pod']} ↔ {correlation['related_pod']} | "
            f"{correlation['message']}"
        )


if __name__ == "__main__":
    main()
