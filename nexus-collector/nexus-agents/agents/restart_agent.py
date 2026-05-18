class RestartAgent:
    def __init__(self):
        self.name = "RestartAgent"
        self.warning_threshold = 1
        self.critical_threshold = 3

    def analyze(self, metric):
        restarts = metric.get("restarts", metric.get("restart_count", 0))
        pod = metric.get("pod")
        namespace = metric.get("namespace")

        if restarts >= self.critical_threshold:
            return {
                "agent": self.name,
                "severity": "critical",
                "pod": pod,
                "namespace": namespace,
                "message": f"{pod} has restarted {restarts} times. Possible crash loop."
            }

        if restarts >= self.warning_threshold:
            return {
                "agent": self.name,
                "severity": "warning",
                "pod": pod,
                "namespace": namespace,
                "message": f"{pod} has restarted {restarts} time(s). Check container stability."
            }

        return None
