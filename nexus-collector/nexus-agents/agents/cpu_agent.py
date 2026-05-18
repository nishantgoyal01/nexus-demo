class CPUAgent:
    def __init__(self):
        self.name = "CPUAgent"
        self.warning_threshold = 70
        self.critical_threshold = 85

    def analyze(self, metric):
        cpu = metric.get("cpu", metric.get("cpu_millicores", 0))
        pod = metric.get("pod")
        namespace = metric.get("namespace")

        if cpu >= self.critical_threshold:
            return {
                "agent": self.name,
                "severity": "critical",
                "pod": pod,
                "namespace": namespace,
                "message": f"CPU spike detected in {pod}. CPU usage is {cpu}%."
            }

        if cpu >= self.warning_threshold:
            return {
                "agent": self.name,
                "severity": "warning",
                "pod": pod,
                "namespace": namespace,
                "message": f"High CPU usage in {pod}. CPU usage is {cpu}%."
            }

        return None
