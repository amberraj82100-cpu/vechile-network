import csv
import json
from datetime import datetime
from pathlib import Path

import pygame

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover
    plt = None

from models import Vehicle
from network import NRV2XSidelink

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"


class App:
    def __init__(self):
        pygame.init()
        self.width, self.height = 1280, 760
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("NR-V2X / PC5 V2V Research Test Bench")
        self.clock = pygame.time.Clock()

        with (BASE_DIR / "config.json").open("r", encoding="utf-8") as f:
            self.cfg = json.load(f)

        self._ensure_log_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = LOG_DIR / f"radio_events_{timestamp}.csv"
        self.latest_log_file = LOG_DIR / "latest_radio_log.csv"
        self.graph_file = LOG_DIR / "last_activity.png"
        self.radio_history = []

        self.batch_duration_s = 10.0
        self.batch_id = 0
        self.batch_elapsed = 0.0
        self.batch_start_time = None
        self.batch_log_rows = []
        self._start_new_batch()
        self._save_activity_graph()

        self.font = pygame.font.SysFont(None, 22)
        self.small_font = pygame.font.SysFont(None, 18)
        self.title_font = pygame.font.SysFont(None, 30)

        self.net = NRV2XSidelink(self.cfg)
        self.running = False
        self.cam_accumulator = 0.0
        self.selected_id = None
        self.status = "Ready"
        self.buttons = {}
        self.vehicle_rects = []

        self._seed()

    def _ensure_log_dir(self):
        LOG_DIR.mkdir(parents=True, exist_ok=True)

    def _start_new_batch(self):
        self._ensure_log_dir()
        self.batch_id += 1
        self.batch_elapsed = 0.0
        self.batch_start_time = datetime.now()
        self.batch_log_rows = []
        self.log_file = LOG_DIR / f"batch_{self.batch_id:03d}_{self.batch_start_time.strftime('%Y%m%d_%H%M%S')}.csv"
        self.latest_log_file = LOG_DIR / "latest_radio_log.csv"
        self._write_log_header()

    def _write_log_header(self):
        headers = [
            "batch_id",
            "batch_time_s",
            "timestamp",
            "sender",
            "receiver",
            "message_type",
            "delivered",
            "communication_range_m",
            "distance_m",
            "tx_power_dbm",
            "rsrp_dbm",
            "sinr_db",
            "mcs",
            "bler",
            "resource_id",
            "collision",
            "propagation_delay_ms",
            "hop_count",
            "sequence_number",
        ]
        with self.log_file.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
        with self.latest_log_file.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)

    def _flush_latest_log(self):
        with self.latest_log_file.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "batch_id", "batch_time_s", "timestamp", "sender", "receiver", "message_type", "delivered",
                "communication_range_m", "distance_m", "tx_power_dbm", "rsrp_dbm", "sinr_db", "mcs",
                "bler", "resource_id", "collision", "propagation_delay_ms", "hop_count", "sequence_number",
            ])
            writer.writerows(self.batch_log_rows)

    def _flush_last_radio_events(self):
        for sender, receiver, message, result in list(self.net.last_radio_events):
            self._append_radio_event(sender, receiver, message, result)

    def _append_radio_event(self, sender, receiver, message, result):
        row = [
            self.batch_id,
            round(self.batch_elapsed, 3),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            sender,
            receiver,
            type(message).__name__,
            int(bool(result.delivered)),
            round(float(self.cfg["simulation"]["communication_range_m"]), 3),
            round(float(result.distance_m), 3),
            round(float(self.cfg["radio"]["tx_power_dbm"]), 3),
            round(float(result.rsrp_dbm), 3),
            round(float(result.sinr_db), 3),
            result.mcs,
            round(float(result.bler), 4),
            result.resource_id,
            int(bool(result.collision)),
            round(float(result.propagation_delay_ms), 6),
            getattr(message, "hop_count", 0),
            getattr(message, "sequence_number", 0),
        ]
        with self.log_file.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(row)
        self.batch_log_rows.append(row)
        self.radio_history.append(row)
        self._flush_latest_log()
        self._save_activity_graph()

    def _finalize_batch(self):
        if not self.running:
            return
        self._ensure_log_dir()
        summary_path = LOG_DIR / f"batch_{self.batch_id:03d}_summary.txt"
        delivered = sum(1 for row in self.batch_log_rows if row[6] == 1)
        lost = sum(1 for row in self.batch_log_rows if row[6] == 0)
        collisions = sum(1 for row in self.batch_log_rows if row[15] == 1)
        summary_path.write_text(
            f"Batch {self.batch_id}\n"
            f"Duration: {self.batch_duration_s:.1f}s\n"
            f"Delivered: {delivered}\n"
            f"Lost: {lost}\n"
            f"Collisions: {collisions}\n",
            encoding="utf-8",
        )
        self.status = f"Batch {self.batch_id} complete"
        self._start_new_batch()

    def _save_activity_graph(self):
        self._ensure_log_dir()
        if plt is None:
            return
        delivered = sum(1 for row in self.radio_history if row[6] == 1)
        lost = sum(1 for row in self.radio_history if row[6] == 0)
        collisions = sum(1 for row in self.radio_history if row[15] == 1)

        fig, ax = plt.subplots(figsize=(7, 4))
        bars = ax.bar(["Delivered", "Lost", "Collisions"], [delivered, lost, collisions], color=["#3ddc97", "#f26b6b", "#ffbf69"])
        ax.set_title("Radio activity summary")
        ax.set_ylabel("Event count")
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height + 0.1, str(int(height)), ha="center", va="bottom")
        fig.tight_layout()
        fig.savefig(self.graph_file, dpi=160)
        plt.close(fig)

    def _seed(self):
        self.net = NRV2XSidelink(self.cfg)
        for i, (x, y, speed) in enumerate([(100, 200, 20), (180, 200, 18), (260, 200, 15)]):
            self.net.register(Vehicle(
                vehicle_id=f"V{i + 1}",
                x=x,
                y=y,
                speed=speed,
                acceleration=0.0,
                heading=0.0,
                lane="lane_1",
                tx_power_dbm=self.cfg["radio"]["tx_power_dbm"],
            ))
        self.selected_id = "V1"

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0
            running = self._handle_events()
            self._update(dt)
            self._draw()
            pygame.display.flip()
        pygame.quit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.toggle()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(event.pos)
        return True

    def _handle_click(self, pos):
        for name, rect in self.buttons.items():
            if rect.collidepoint(pos):
                getattr(self, name)()
                return

        for rect, vid in self.vehicle_rects:
            if rect.collidepoint(pos):
                self.selected_id = vid
                self.status = f"Selected {vid}"
                return

    def add_vehicle(self):
        i = 1
        while f"V{i}" in self.net.vehicles:
            i += 1
        self.net.register(Vehicle(
            vehicle_id=f"V{i}",
            x=100 + 60 * i,
            y=300,
            speed=15,
            acceleration=0,
            heading=0,
            lane="lane_1",
            tx_power_dbm=self.cfg["radio"]["tx_power_dbm"],
        ))
        if self.selected_id is None:
            self.selected_id = f"V{i}"
        self.status = f"Added {self.selected_id}"

    def remove_vehicle(self):
        if self.selected_id and self.selected_id in self.net.vehicles:
            self.net.vehicles.pop(self.selected_id, None)
            self.net.queues.pop(self.selected_id, None)
            self.net.dissemination.pop(self.selected_id, None)
            remaining = sorted(self.net.vehicles)
            self.selected_id = remaining[0] if remaining else None
            self.status = "Removed selected vehicle"

    def generate_cam(self):
        if not self.selected_id or self.selected_id not in self.net.vehicles:
            self.status = "Select a vehicle first"
            return
        delivered = self.net.generate_cam(self.selected_id)
        self._flush_last_radio_events()
        self.status = f"CAM from {self.selected_id}; deliveries: {delivered}"

    def save_activity_report(self):
        self._save_activity_graph()
        self.status = f"Saved radio activity graph to {self.graph_file.name}"

    def create_hazard(self):
        if not self.selected_id or self.selected_id not in self.net.vehicles:
            self.status = "Select a vehicle first"
            return
        delivered = self.net.generate_denm(self.selected_id, "ACCIDENT", 3)
        self._flush_last_radio_events()
        self.status = f"DENM from {self.selected_id}; deliveries: {delivered}"

    def reset(self):
        self.running = False
        self._seed()
        self.status = "Reset complete"

    def toggle(self):
        self.running = not self.running
        if self.running and self.batch_start_time is None:
            self._start_new_batch()
        self.status = "Running" if self.running else "Paused"

    def run_batch(self):
        self.running = True
        self._start_new_batch()
        self.status = f"Running batch {self.batch_id}"

    def _update(self, dt):
        if not self.running:
            return

        self.net.step(dt)
        self._flush_last_radio_events()
        self.batch_elapsed += dt
        self.cam_accumulator += dt
        if self.cam_accumulator >= self.cfg["cam"]["interval_s"]:
            for vid in list(self.net.vehicles):
                self.net.generate_cam(vid)
            self._flush_last_radio_events()
            self.cam_accumulator = 0.0
        if self.batch_elapsed >= self.batch_duration_s:
            self._finalize_batch()

    def _draw(self):
        self.screen.fill((14, 18, 24))

        left_w, right_w = 260, 310
        canvas_w = self.width - left_w - right_w
        canvas_h = self.height - 40

        pygame.draw.rect(self.screen, (28, 30, 36), (0, 0, left_w, self.height))
        pygame.draw.rect(self.screen, (22, 22, 26), (left_w, 0, canvas_w, canvas_h))
        pygame.draw.rect(self.screen, (28, 32, 42), (self.width - right_w, 0, right_w, self.height))

        title = self.title_font.render("NR-V2X / PC5 V2V Research Test Bench", True, (255, 255, 255))
        self.screen.blit(title, (12, 12))

        self.buttons = {}
        button_y = 70
        for label, handler in [
            ("Add Vehicle", "add_vehicle"),
            ("Remove Selected", "remove_vehicle"),
            ("Run / Pause", "toggle"),
            ("Batch Run", "run_batch"),
            ("Generate CAM", "generate_cam"),
            ("Create Hazard", "create_hazard"),
            ("Save Report", "save_activity_report"),
            ("Reset", "reset"),
        ]:
            rect = pygame.Rect(18, button_y, 220, 34)
            self.buttons[handler] = rect
            color = (55, 120, 220)
            if handler == "toggle":
                color = (76, 160, 90)
            if handler == "remove_vehicle":
                color = (190, 90, 90)
            if handler in {"generate_cam", "create_hazard"}:
                color = (228, 156, 62)
            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            render = self.font.render(label, True, (255, 255, 255))
            self.screen.blit(render, (rect.x + 14, rect.y + 8))
            button_y += 42

        self.vehicle_rects = []
        list_title = self.font.render("VEHICLES", True, (200, 220, 245))
        self.screen.blit(list_title, (20, 290))
        for idx, vid in enumerate(sorted(self.net.vehicles)):
            item_rect = pygame.Rect(18, 318 + idx * 28, 220, 22)
            is_selected = vid == self.selected_id
            pygame.draw.rect(self.screen, (58, 68, 88) if not is_selected else (70, 120, 180), item_rect, border_radius=6)
            render = self.small_font.render(vid, True, (255, 255, 255))
            self.screen.blit(render, (item_rect.x + 10, item_rect.y + 4))
            self.vehicle_rects.append((item_rect, vid))

        road_rect = pygame.Rect(left_w + 15, 20, canvas_w - 30, canvas_h - 24)
        pygame.draw.rect(self.screen, (45, 47, 52), road_rect, border_radius=10)
        road_top = road_rect.top + road_rect.height * 0.26
        road_bottom = road_rect.top + road_rect.height * 0.74
        pygame.draw.rect(self.screen, (30, 30, 30), (road_rect.left, road_top, road_rect.width, road_bottom - road_top), border_radius=4)
        for lane_y in [road_top + 40, road_top + 90, road_top + 140]:
            pygame.draw.line(self.screen, (120, 120, 120), (road_rect.left, lane_y), (road_rect.right, lane_y), 2)

        scale = 2.0
        for vid, v in self.net.vehicles.items():
            x = road_rect.left + v.x * scale
            y = road_rect.top + (road_rect.height / 2) + (v.y - 200) * 1.0
            radius = 10
            pygame.draw.circle(self.screen, (76, 160, 240), (int(x), int(y)), radius)
            pygame.draw.circle(self.screen, (255, 255, 255), (int(x), int(y)), radius, 1)
            if vid == self.selected_id:
                pygame.draw.circle(self.screen, (255, 255, 255), (int(x), int(y)), int(self.cfg["simulation"]["communication_range_m"] * scale), 2)
            label = self.small_font.render(vid, True, (255, 255, 255))
            self.screen.blit(label, (int(x) - 10, int(y) - 28))

        self.screen.blit(self.font.render(self.status, True, (230, 230, 230)), (left_w + 20, canvas_h - 24))
        if self.graph_file.exists():
            summary = self.small_font.render(f"Graph: {self.graph_file.name}", True, (190, 220, 255))
            self.screen.blit(summary, (left_w + 20, canvas_h - 48))
        log_path = self.small_font.render(f"Log: {self.latest_log_file.name}", True, (170, 225, 255))
        self.screen.blit(log_path, (left_w + 20, canvas_h - 72))
        timer = self.small_font.render(f"Batch: {self.batch_elapsed:.1f}s / {self.batch_duration_s:.1f}s", True, (255, 220, 160))
        self.screen.blit(timer, (left_w + 20, canvas_h - 96))

        metrics = self.net.metrics.as_dict()
        right_y = 18
        title = self.font.render("NR-V2X METRICS", True, (220, 220, 240))
        self.screen.blit(title, (self.width - right_w + 18, right_y))
        right_y += 30
        for key, value in metrics.items():
            line = self.small_font.render(f"{key}: {value}", True, (230, 230, 230))
            self.screen.blit(line, (self.width - right_w + 18, right_y))
            right_y += 20

        self.screen.blit(self.font.render("LAST RADIO EVENTS", True, (220, 220, 240)), (self.width - right_w + 18, right_y + 12))
        right_y += 32
        for sender, receiver, _, result in self.net.last_radio_events[-6:]:
            event_text = self.small_font.render(
                f"{sender}->{receiver} ok={int(result.delivered)} RSRP={result.rsrp_dbm:.1f} SINR={result.sinr_db:.1f} MCS={result.mcs} BLER={result.bler:.3f}",
                True,
                (220, 220, 220),
            )
            self.screen.blit(event_text, (self.width - right_w + 18, right_y))
            right_y += 18


if __name__ == "__main__":
    app = App()
    app.run()
