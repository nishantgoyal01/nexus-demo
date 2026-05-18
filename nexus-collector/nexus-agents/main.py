import json
from datetime import datetime

from agents.cpu_agent import CPUAgent
from agents.memory_agent import MemoryAgent
from agents.restart_agent import RestartAgent
from agents.status_agent import StatusAgent
from correlation_engine import correlate_alerts, load_json_file, save_json_file


agents = [
    CPUAgent(),
    MemoryAgent(),
    RestartAgent(),
    StatusAgent()
]


def load_metrics():
    with open("pod_metrics.json", "r") as file:
        return json.load(file)


def save_alerts(alerts):
    with open("alerts.json", "w") as file:
        json.dump(alerts, file, indent=4)


def run_agents(metrics):
    alerts = []

    for metric in metrics:
        for agent in agents:
            result = agent.analyze(metric)

            if result:
                result["timestamp"] = datetime.utcnow().isoformat()
                alerts.append(result)

    return alerts


def main():
    metrics = load_metrics()
    alerts = run_agents(metrics)

    save_alerts(alerts)

    dependency_map = load_json_file("dependencies.json", {})
    correlations = correlate_alerts(alerts, dependency_map)
    save_json_file("correlations.json", correlations)

    print("Agent Analysis Completed")
    print("-" * 60)

    if not alerts:
        print("No alerts detected. All pods are healthy.")

    for alert in alerts:
        print(
            f"[{alert['severity'].upper()}] "
            f"{alert['agent']} | "
            f"{alert['namespace']}/{alert['pod']} | "
            f"{alert['message']}"
        )

    print("\nCorrelation Results")
    print("-" * 60)

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
