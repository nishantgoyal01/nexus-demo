class StatusAgent:
    def __init__(self):
        self.name = "StatusAgent"

    def analyze(self, metric):
        status = metric.get("status", "Unknown")
        pod = metric.get("pod")
        namespace = metric.get("namespace")

        if status != "Running":
            return {
                "agent": self.name,
                "severity": "critical",
                "pod": pod,
                "namespace": namespace,
                "message": f"{pod} is not running. Current status: {status}."
            }

        return None
