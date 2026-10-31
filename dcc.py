class DCCController:
    """
    Simple adaptive CAM generation policy.

    This is an experimental congestion-control abstraction, not a direct
    implementation of a specific ETSI/3GPP DCC algorithm.
    """

    def __init__(self, cfg):
        self.cfg = cfg

    def rate_hz(self, channel_load):
        if not self.cfg["enabled"]:
            return self.cfg["low_rate_hz"], "DISABLED"

        if channel_load < self.cfg["low_load"]:
            return self.cfg["low_rate_hz"], "LOW"
        if channel_load < self.cfg["medium_load"]:
            return self.cfg["medium_rate_hz"], "MEDIUM"
        return self.cfg["high_rate_hz"], "HIGH"
