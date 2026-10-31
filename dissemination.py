class DisseminationManager:
    def __init__(self, max_ttl=3, duplicate_filtering=True, forwarding=True):
        self.max_ttl = max_ttl
        self.duplicate_filtering = duplicate_filtering
        self.forwarding_enabled = forwarding
        self.seen = set()

    def valid(self, message, now):
        if message.hop_count >= self.max_ttl:
            return False, "ttl"
        if message.expiry_time <= now:
            return False, "expired"
        if self.duplicate_filtering and message.key() in self.seen:
            return False, "duplicate"
        return True, ""

    def mark_seen(self, message):
        self.seen.add(message.key())

    def should_forward(self, message, now):
        if not self.forwarding_enabled:
            return False
        return message.hop_count < self.max_ttl and message.expiry_time > now

    def prepare_forward(self, message):
        return message.copy_for_forward()
