"""
GHOSTTRACE v4.0 — Terminal Phone Intelligence Suite
Educational / simulation UI. Uses public OSINT data only.
Does NOT perform real hacking, GPS tracking, wiretapping, or carrier intrusion.
"""

import hashlib
import json
import os
import random
import re
import string
import webbrowser
from datetime import datetime
from tkinter import (
    Tk, Toplevel, Label, Button, Entry, Frame, Text, Scrollbar,
    END, filedialog, StringVar, Canvas, messagebox,
)
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import folium
import phonenumbers
import pycountry
from phonenumbers import geocoder, carrier, timezone

from intel_engine import (
    LEGAL_INTERCEPT_STEPS,
    analyze_imei,
    assess_location_confidence,
    geocode_region,
    get_region_description,
)
import terminal_sfx


class Theme:
    BG = "#000000"
    BG_PANEL = "#0a0a0a"
    BG_INPUT = "#050505"
    GREEN = "#00ff41"
    GREEN_DIM = "#00aa2a"
    CYAN = "#00ffff"
    RED = "#ff0040"
    AMBER = "#ffaa00"
    GRAY = "#333333"
    GRAY_TEXT = "#666666"
    FONT = ("Consolas", 11)
    FONT_SM = ("Consolas", 9)
    FONT_LG = ("Consolas", 14, "bold")
    FONT_XL = ("Consolas", 18, "bold")


BANNER = r"""
 ██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗████████╗██████╗  █████╗  ██████╗███████╗
██╔════╝ ██║  ██║██╔═══██╗██╔════╝╚══██╔══╝╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██╔════╝
██║  ███╗███████║██║   ██║███████╗   ██║      ██║   ██████╔╝███████║██║     █████╗
██║   ██║██╔══██║██║   ██║╚════██║   ██║      ██║   ██╔══██╗██╔══██║██║     ██╔══╝
╚██████╔╝██║  ██║╚██████╔╝███████║   ██║      ██║   ██║  ██║██║  ██║╚██████╗███████╗
 ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝      ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝
                         v4.0 // SIGINT TERMINAL // EDUCATIONAL DEMO ONLY
"""

SCAN_STEPS = [
    ("[*] Initializing encrypted tunnel .................", 100),
    ("[*] Spoofing carrier handshake [HLR/VLR] ..........", 150),
    ("[*] Injecting SS7 probe packet [SIMULATED] ........", 160),
    ("[*] Querying ITU-T E.164 numbering plan ...........", 180),
    ("[*] Resolving MCC/MNC operator registry ...........", 150),
    ("[*] Decoding IMEI TAC allocation [if provided] ....", 170),
    ("[*] Assessing location confidence tier ............", 140),
    ("[*] Geocoding region via OSM Nominatim ..........", 200),
    ("[*] Cross-referencing public OSINT databases ......", 150),
    ("[!] Live GPS/wiretap channels: BLOCKED (no warrant)", 120),
    ("[+] TARGET PROFILE COMPILED — dumping intel .......", 80),
]


class HackerPhoneTracker:
    HISTORY_FILE = "ghosttrace_targets.json"
    DISCLAIMER_FILE = ".ghosttrace_disclaimer_seen"

    COUNTRY_COORDS = {
        "Tanzania": (-6.369028, 34.888822),
        "Kenya": (-1.286389, 36.817223),
        "Uganda": (0.347596, 32.582520),
        "Nigeria": (9.081999, 8.675277),
        "South Africa": (-30.559482, 22.937506),
        "United States": (37.090240, -95.712891),
        "United Kingdom": (55.378051, -3.435973),
        "India": (20.593684, 78.962880),
        "China": (35.861660, 104.195397),
        "Germany": (51.165691, 10.451526),
        "France": (46.227638, 2.213749),
        "Canada": (56.130366, -106.346771),
        "Australia": (-25.274398, 133.775136),
        "Brazil": (-14.235004, -51.925280),
        "Japan": (36.204824, 138.252924),
        "Mexico": (23.634501, -102.552784),
        "Russia": (61.524010, 105.318756),
        "Indonesia": (-0.789275, 113.921327),
        "Pakistan": (30.375321, 69.345116),
        "Philippines": (12.879721, 121.774017),
        "Egypt": (26.820553, 30.802498),
        "Saudi Arabia": (23.885942, 45.079162),
        "United Arab Emirates": (23.424076, 53.847818),
        "Singapore": (1.352083, 103.819836),
        "Malaysia": (4.210484, 101.975766),
        "Thailand": (15.870032, 100.992541),
        "Vietnam": (14.058324, 108.277199),
        "Turkey": (38.963745, 35.243322),
        "Italy": (41.871940, 12.567380),
        "Spain": (40.463667, -3.749220),
        "Netherlands": (52.132633, 5.291266),
        "Poland": (51.919438, 19.145136),
        "Argentina": (-38.416097, -63.616672),
        "Colombia": (4.570868, -74.297333),
        "Ghana": (7.946527, -1.023194),
        "Ethiopia": (9.145000, 40.489673),
        "Morocco": (31.791702, -7.092620),
        "Israel": (31.046051, 34.851612),
        "South Korea": (35.907757, 127.766922),
        "Bangladesh": (23.684994, 90.356331),
        "Rwanda": (-1.940278, 29.873888),
        "Zimbabwe": (-19.015438, 29.154857),
    }

    def __init__(self, root):
        self.window = root
        self.window.title("GHOSTTRACE // SIGINT TERMINAL")
        self.window.geometry("980x820")
        self.window.configure(bg=Theme.BG)
        self.window.minsize(920, 750)

        base = os.path.dirname(__file__)
        self.history_path = os.path.join(base, self.HISTORY_FILE)
        self.disclaimer_path = os.path.join(base, self.DISCLAIMER_FILE)
        self.targets = self._load_history()
        self.current_data = {}
        self.scanning = False
        self.cursor_visible = True
        self.session_id = self._gen_session_id()
        self.sound_on = True
        terminal_sfx.set_enabled(True)

        self._build_ui()
        self._start_cursor_blink()
        self.window.after(400, self._show_presentation_disclaimer)
        self.window.after(800, self._run_boot_sequence)

    def _gen_session_id(self):
        return "".join(random.choices(string.hexdigits[:16], k=16)).upper()

    def _load_history(self):
        if not os.path.exists(self.history_path):
            return []
        try:
            with open(self.history_path, encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def _save_history(self):
        try:
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(self.targets[-100:], f, indent=2)
        except OSError:
            pass

    @staticmethod
    def sanitize(phone):
        cleaned = re.sub(r"[^\d+]", "", phone.strip())
        if cleaned and not cleaned.startswith("+"):
            cleaned = "+" + cleaned
        return cleaned

    def _show_presentation_disclaimer(self):
        if os.path.exists(self.disclaimer_path):
            return
        messagebox.showinfo(
            "GHOSTTRACE — Educational Demo",
            "PRESENTATION MODE\n\n"
            "This tool SIMULATES a hacker terminal for learning.\n\n"
            "REAL data shown:\n"
            "  • Country / area from phone number (OSINT)\n"
            "  • Carrier, timezone, device model from IMEI TAC\n\n"
            "NOT available (requires warrant + carrier):\n"
            "  • Live GPS location\n"
            "  • Wiretapping / call interception\n"
            "  • Subscriber name or address\n\n"
            "Use [LEGAL PATH] to see how real investigations work.",
        )
        try:
            with open(self.disclaimer_path, "w") as f:
                f.write("seen")
        except OSError:
            pass

    def _build_ui(self):
        self.scan_canvas = Canvas(self.window, bg=Theme.BG, highlightthickness=0, height=3)
        self.scan_canvas.pack(fill="x")
        self._animate_scanline()

        header = Frame(self.window, bg=Theme.BG)
        header.pack(fill="x", padx=12, pady=(4, 0))
        Label(header, text="GHOSTTRACE SIGINT TERMINAL", fg=Theme.GREEN,
              font=Theme.FONT_XL, bg=Theme.BG).pack(side="left")
        Label(header, text=f"SESSION:{self.session_id}", fg=Theme.GRAY_TEXT,
              font=Theme.FONT_SM, bg=Theme.BG).pack(side="right", padx=(0, 8))

        self.sound_btn = Button(
            header, text="[ SFX: ON ]", bg=Theme.BG, fg=Theme.AMBER,
            font=Theme.FONT_SM, relief="flat", highlightthickness=1,
            highlightbackground=Theme.GRAY, cursor="hand2",
            command=self._toggle_sound,
        )
        self.sound_btn.pack(side="right")

        Label(self.window, text="[ EDUCATIONAL SIMULATION — PUBLIC OSINT ONLY — NO LIVE GPS/WIRETAP ]",
              fg=Theme.RED, font=Theme.FONT_SM, bg=Theme.BG).pack(anchor="w", padx=12)

        term_frame = Frame(self.window, bg=Theme.GREEN, padx=1, pady=1)
        term_frame.pack(fill="both", expand=True, padx=12, pady=6)
        inner = Frame(term_frame, bg=Theme.BG_PANEL)
        inner.pack(fill="both", expand=True)
        scroll = Scrollbar(inner)
        scroll.pack(side="right", fill="y")
        self.terminal = Text(inner, bg=Theme.BG_PANEL, fg=Theme.GREEN, font=Theme.FONT,
                             insertbackground=Theme.GREEN, relief="flat", wrap="word",
                             yscrollcommand=scroll.set, state="disabled", height=10, padx=10, pady=8)
        self.terminal.pack(fill="both", expand=True)
        scroll.config(command=self.terminal.yview)
        for tag, color in [("green", Theme.GREEN), ("dim", Theme.GREEN_DIM),
                           ("cyan", Theme.CYAN), ("red", Theme.RED),
                           ("amber", Theme.AMBER), ("gray", Theme.GRAY_TEXT)]:
            self.terminal.tag_config(tag, foreground=color)

        # Dual input: MSISDN + IMEI
        input_frame = Frame(self.window, bg=Theme.BG, padx=12)
        input_frame.pack(fill="x", pady=2)

        row1 = Frame(input_frame, bg=Theme.BG)
        row1.pack(fill="x")
        Label(row1, text="root@ghosttrace:~$ target --msisdn", fg=Theme.GREEN,
              font=Theme.FONT_SM, bg=Theme.BG).pack(side="left")
        self.phone_entry = Entry(row1, width=22, font=Theme.FONT_SM, bg=Theme.BG_INPUT,
                                 fg=Theme.GREEN, insertbackground=Theme.GREEN, relief="flat",
                                 highlightthickness=1, highlightbackground=Theme.GREEN_DIM)
        self.phone_entry.pack(side="left", padx=6, ipady=3)
        self.phone_entry.bind("<Return>", lambda e: self.initiate_scan())

        Label(row1, text="--imei", fg=Theme.CYAN, font=Theme.FONT_SM, bg=Theme.BG).pack(side="left", padx=(12, 0))
        self.imei_entry = Entry(row1, width=20, font=Theme.FONT_SM, bg=Theme.BG_INPUT,
                                fg=Theme.CYAN, insertbackground=Theme.CYAN, relief="flat",
                                highlightthickness=1, highlightbackground=Theme.GRAY)
        self.imei_entry.pack(side="left", padx=6, ipady=3)

        self.scan_btn = Button(row1, text="[ EXECUTE TRACE ]", bg=Theme.BG, fg=Theme.GREEN,
                               font=("Consolas", 9, "bold"), relief="flat",
                               highlightthickness=1, highlightbackground=Theme.GREEN,
                               cursor="hand2", command=self.initiate_scan)
        self.scan_btn.pack(side="left", padx=4)

        btn_row = Frame(self.window, bg=Theme.BG, padx=12, pady=4)
        btn_row.pack(fill="x")
        for text, cmd in [
            ("GEO OVERLAY", self.show_map),
            ("EXFIL DATA", self.export_data),
            ("TARGET ARCHIVE", self.show_archive),
            ("LEGAL PATH", self.show_legal_path),
            ("WIPE CONSOLE", self.wipe_console),
            ("PURGE", self.clear_input),
        ]:
            Button(btn_row, text=f"[ {text} ]", bg=Theme.BG, fg=Theme.CYAN,
                   font=Theme.FONT_SM, relief="flat", highlightthickness=1,
                   highlightbackground=Theme.GRAY, cursor="hand2", command=cmd).pack(side="left", padx=2)

        # Confidence bar
        conf_frame = Frame(self.window, bg=Theme.BG_PANEL, padx=12, pady=6)
        conf_frame.pack(fill="x", padx=12)
        Label(conf_frame, text="LOCATION CONFIDENCE:", fg=Theme.GRAY_TEXT,
              font=Theme.FONT_SM, bg=Theme.BG_PANEL).pack(side="left")
        self.confidence_var = StringVar(value="NO TARGET")
        Label(conf_frame, textvariable=self.confidence_var, fg=Theme.AMBER,
              font=Theme.FONT_SM, bg=Theme.BG_PANEL).pack(side="left", padx=8)
        self.confidence_bar = Canvas(conf_frame, width=200, height=14, bg=Theme.BG,
                                     highlightthickness=0)
        self.confidence_bar.pack(side="left", padx=4)
        self._draw_confidence_bar(0)
        Label(conf_frame, text="LIVE GPS: ████ BLOCKED (needs warrant)",
              fg=Theme.RED, font=Theme.FONT_SM, bg=Theme.BG_PANEL).pack(side="right")

        # Intel panels — two columns
        panels = Frame(self.window, bg=Theme.BG)
        panels.pack(fill="x", padx=12, pady=(0, 6))

        self.phone_intel_vars = self._make_intel_vars()
        self.imei_intel_vars = self._make_imei_vars()
        self._build_intel_panel(panels, "▸ MSISDN INTELLIGENCE", self.phone_intel_vars, Theme.GREEN, "left")
        self._build_intel_panel(panels, "▸ IMEI DEVICE INTEL", self.imei_intel_vars, Theme.CYAN, "right")

        status_frame = Frame(self.window, bg=Theme.BG_PANEL, padx=12, pady=4)
        status_frame.pack(fill="x", side="bottom")
        self.status_var = StringVar(value="STANDBY")
        Label(status_frame, textvariable=self.status_var, fg=Theme.GREEN,
              font=Theme.FONT_SM, bg=Theme.BG_PANEL, anchor="w").pack(side="left")
        self.progress_var = StringVar(value="")
        Label(status_frame, textvariable=self.progress_var, fg=Theme.GREEN_DIM,
              font=Theme.FONT_SM, bg=Theme.BG_PANEL, anchor="e").pack(side="right")

    def _make_intel_vars(self):
        keys = ["e164", "valid", "country", "region", "carrier", "type",
                "timezone", "local_time", "iso", "accuracy", "geocode_src"]
        return {k: StringVar(value="—") for k in keys}

    def _make_imei_vars(self):
        keys = ["imei", "luhn", "tac", "brand", "model", "serial",
                "live_loc", "note"]
        return {k: StringVar(value="—") for k in keys}

    def _build_intel_panel(self, parent, title, vars_dict, accent, side):
        outer = Frame(parent, bg=accent, padx=1, pady=1)
        outer.pack(side=side, fill="both", expand=True, padx=3)
        inner = Frame(outer, bg=Theme.BG_PANEL, padx=8, pady=6)
        inner.pack(fill="both", expand=True)
        Label(inner, text=title, fg=accent, font=Theme.FONT_SM, bg=Theme.BG_PANEL).pack(anchor="w")
        labels = list(vars_dict.keys())
        display = {
            "e164": "E.164", "valid": "VALIDITY", "country": "COUNTRY",
            "region": "AREA/CITY", "carrier": "OPERATOR", "type": "LINE TYPE",
            "timezone": "TIMEZONE", "local_time": "LOCAL TIME", "iso": "ISO",
            "accuracy": "ACCURACY RADIUS", "geocode_src": "GEOCODE SRC",
            "imei": "IMEI", "luhn": "LUHN CHECK", "tac": "TAC CODE",
            "brand": "BRAND", "model": "MODEL", "serial": "SERIAL",
            "live_loc": "LIVE LOCATION", "note": "NOTE",
        }
        for key in labels:
            row = Frame(inner, bg=Theme.BG_PANEL)
            row.pack(fill="x", pady=1)
            Label(row, text=f" {display.get(key, key.upper())}:", fg=Theme.GRAY_TEXT,
                  font=("Consolas", 8), bg=Theme.BG_PANEL, width=16, anchor="w").pack(side="left")
            Label(row, textvariable=vars_dict[key], fg=accent,
                  font=("Consolas", 8, "bold"), bg=Theme.BG_PANEL, anchor="w",
                  wraplength=320).pack(side="left", fill="x", expand=True)

    def _draw_confidence_bar(self, pct):
        self.confidence_bar.delete("all")
        w = 200
        fill_w = int(w * pct / 100)
        self.confidence_bar.create_rectangle(0, 0, w, 14, fill=Theme.BG, outline=Theme.GRAY)
        color = Theme.GREEN if pct < 50 else Theme.AMBER
        if fill_w:
            self.confidence_bar.create_rectangle(0, 0, fill_w, 14, fill=color, outline="")

    def _toggle_sound(self):
        self.sound_on = not self.sound_on
        terminal_sfx.set_enabled(self.sound_on)
        label = "[ SFX: ON ]" if self.sound_on else "[ SFX: OFF ]"
        color = Theme.AMBER if self.sound_on else Theme.GRAY_TEXT
        self.sound_btn.config(text=label, fg=color)
        if self.sound_on:
            terminal_sfx.toggle_click()

    def _animate_scanline(self):
        w = self.scan_canvas.winfo_width() or 960
        self.scan_canvas.delete("scan")
        y = getattr(self, "_scan_y", 0)
        self.scan_canvas.create_line(0, y % 3, w, y % 3, fill=Theme.GREEN_DIM, tags="scan")
        self._scan_y = y + 1
        self.window.after(80, self._animate_scanline)

    def _start_cursor_blink(self):
        base = self.status_var.get().rstrip("█")
        self.status_var.set(base + ("█" if self.cursor_visible else ""))
        self.cursor_visible = not self.cursor_visible
        self.window.after(530, self._start_cursor_blink)

    def _log(self, text, tag="green", newline=True):
        self.terminal.config(state="normal")
        self.terminal.insert(END, text + ("\n" if newline else ""), tag)
        self.terminal.see(END)
        self.terminal.config(state="disabled")

    def _log_typed(self, text, tag="green", char_delay=12, on_done=None, sfx=False):
        char_count = [0]

        def type_char(i=0):
            if i < len(text):
                self.terminal.config(state="normal")
                self.terminal.insert(END, text[i], tag)
                self.terminal.see(END)
                self.terminal.config(state="disabled")
                if sfx and text[i] not in (" ", "."):
                    char_count[0] += 1
                    if char_count[0] % 4 == 0:
                        terminal_sfx.key_tick()
                self.window.after(char_delay, lambda: type_char(i + 1))
            else:
                self.terminal.config(state="normal")
                self.terminal.insert(END, "\n")
                self.terminal.config(state="disabled")
                if on_done:
                    on_done()
        type_char()

    def _run_boot_sequence(self):
        self.scanning = True
        self.scan_btn.config(state="disabled")
        terminal_sfx.boot_line()
        lines = [
            (BANNER, "green"),
            (f"[SYS] Session: {self.session_id}", "cyan"),
            (f"[SYS] Timestamp: {datetime.now():%Y-%m-%d %H:%M:%S}", "dim"),
            ("[SYS] OSINT engine ............................ OK", "dim"),
            ("[SYS] IMEI TAC decoder ........................ OK", "dim"),
            ("[SYS] Location confidence module .............. OK", "dim"),
            ("[SYS] Legal intercept reference DB .......... OK", "dim"),
            ("[!]  Live GPS / wiretap: PERMANENTLY BLOCKED", "red"),
            ("[+]  Awaiting MSISDN and/or IMEI input.", "green"),
        ]

        def show(idx=0):
            if idx >= len(lines):
                self.scanning = False
                self.scan_btn.config(state="normal")
                self.status_var.set("STANDBY — AWAITING TARGET")
                terminal_sfx.boot_ready()
                return
            text, tag = lines[idx]
            if text == BANNER:
                self._log(text, tag)
                terminal_sfx.boot_line()
                self.window.after(150, lambda: show(idx + 1))
            else:
                terminal_sfx.boot_line()
                self._log_typed(text, tag, on_done=lambda: show(idx + 1), sfx=True)
        show()

    def _get_number_type(self, parsed):
        types = {
            phonenumbers.PhoneNumberType.MOBILE: "MOBILE/GSM",
            phonenumbers.PhoneNumberType.FIXED_LINE: "PSTN/FIXED",
            phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "HYBRID",
            phonenumbers.PhoneNumberType.TOLL_FREE: "TOLL-FREE",
            phonenumbers.PhoneNumberType.VOIP: "VOIP/SIP",
        }
        return types.get(phonenumbers.number_type(parsed), "UNKNOWN")

    def _get_local_time(self, tz_list):
        if not tz_list:
            return "N/A"
        try:
            return datetime.now(ZoneInfo(tz_list[0])).strftime("%Y-%m-%d %H:%M:%S %Z")
        except ZoneInfoNotFoundError:
            return "N/A"

    def _analyze_phone(self, phone_input):
        parsed = phonenumbers.parse(phone_input)
        is_valid = phonenumbers.is_valid_number(parsed)
        e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        region = get_region_description(parsed)
        country = region
        iso = phonenumbers.region_code_for_number(parsed) or "XX"
        confidence = assess_location_confidence(parsed, region, iso)
        geo = geocode_region(region, iso)

        tz_list = list(timezone.time_zones_for_number(parsed))
        return {
            "phone": phone_input,
            "hash": hashlib.sha256(e164.encode()).hexdigest()[:32].upper(),
            "valid": is_valid,
            "e164": e164,
            "country": country,
            "region": region,
            "carrier": carrier.name_for_number(parsed, "en") or "UNRESOLVED",
            "type": self._get_number_type(parsed),
            "timezone": ", ".join(tz_list) if tz_list else "N/A",
            "local_time": self._get_local_time(tz_list),
            "iso": iso,
            "confidence": confidence,
            "geocode": geo,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _display_phone_intel(self, data):
        c = data["confidence"]
        self.phone_intel_vars["e164"].set(data["e164"])
        self.phone_intel_vars["valid"].set("CONFIRMED" if data["valid"] else "REJECTED")
        self.phone_intel_vars["country"].set(data["country"].upper())
        self.phone_intel_vars["region"].set(data["region"].upper())
        self.phone_intel_vars["carrier"].set(data["carrier"].upper())
        self.phone_intel_vars["type"].set(data["type"])
        self.phone_intel_vars["timezone"].set(data["timezone"])
        self.phone_intel_vars["local_time"].set(data["local_time"])
        self.phone_intel_vars["iso"].set(data["iso"])
        self.phone_intel_vars["accuracy"].set(c["accuracy"])
        geo = data.get("geocode")
        if geo:
            self.phone_intel_vars["geocode_src"].set(
                f"{geo['lat']:.4f}, {geo['lng']:.4f} ({geo['source']})"
            )
        else:
            self.phone_intel_vars["geocode_src"].set("OFFLINE / UNRESOLVED")
        self.confidence_var.set(c["label"])
        self._draw_confidence_bar(c["bar_pct"])

    def _display_imei_intel(self, imei_data):
        if not imei_data or not imei_data.get("imei"):
            for v in self.imei_intel_vars.values():
                v.set("—")
            return
        self.imei_intel_vars["imei"].set(imei_data["imei"])
        self.imei_intel_vars["luhn"].set(
            "PASS" if imei_data["luhn_valid"] else "FAIL"
        )
        self.imei_intel_vars["tac"].set(imei_data["tac"])
        self.imei_intel_vars["brand"].set(imei_data["brand"].upper())
        self.imei_intel_vars["model"].set(imei_data["model"].upper())
        self.imei_intel_vars["serial"].set(imei_data["serial"] or "—")
        self.imei_intel_vars["live_loc"].set(imei_data["live_location"])
        note = imei_data["location_note"]
        if not imei_data.get("device_known") and imei_data.get("lookup_hint"):
            note = imei_data["lookup_hint"]
        self.imei_intel_vars["note"].set(note)

    def initiate_scan(self):
        if self.scanning:
            return

        phone = self.sanitize(self.phone_entry.get())
        imei_raw = self.imei_entry.get().strip()

        if (not phone or phone == "+") and not imei_raw:
            self._log("[!] ERROR: Provide MSISDN and/or IMEI.", "red")
            terminal_sfx.scan_error()
            return

        self.scanning = True
        self.scan_btn.config(state="disabled")
        self.status_var.set("TRACING TARGET")
        terminal_sfx.scan_tick()
        cmd = f"target --msisdn {phone}" if phone and phone != "+" else "target --imei-only"
        if imei_raw:
            cmd += f" --imei {imei_raw[:8]}..."
        self._log(f"\nroot@ghosttrace:~$ {cmd}", "cyan")

        def run_step(idx=0):
            if idx >= len(SCAN_STEPS):
                self._finalize_scan(phone, imei_raw)
                return
            line, delay = SCAN_STEPS[idx]
            pct = int((idx + 1) / len(SCAN_STEPS) * 100)
            self.progress_var.set(f"[{'#' * (pct // 5)}{'.' * (20 - pct // 5)}] {pct}%")
            tag = "green" if line.startswith("[+]") else ("red" if line.startswith("[!]") else "dim")
            if line.startswith("[!]"):
                terminal_sfx.scan_warning()
            elif line.startswith("[+]"):
                terminal_sfx.scan_success()
            else:
                terminal_sfx.scan_step()
            self._log_typed(line, tag, char_delay=6, sfx=True,
                             on_done=lambda: self.window.after(delay, lambda: run_step(idx + 1)))
        run_step()

    def _finalize_scan(self, phone, imei_raw):
        try:
            data = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            imei_data = analyze_imei(imei_raw) if imei_raw else None

            if phone and phone != "+":
                phone_data = self._analyze_phone(phone)
                data.update(phone_data)
                self._display_phone_intel(phone_data)
            else:
                for v in self.phone_intel_vars.values():
                    v.set("—")
                self.confidence_var.set("PHONE NOT PROVIDED")
                self._draw_confidence_bar(0)

            self._display_imei_intel(imei_data)
            if imei_data:
                data["imei_intel"] = imei_data

            self.current_data = data
            self.targets.append(data.copy())
            self._save_history()

            self._log("═" * 62, "cyan")
            self._log("  INTELLIGENCE DUMP COMPLETE", "cyan")
            self._log("═" * 62, "cyan")

            if phone and phone != "+":
                c = data["confidence"]
                self._log(f"  MSISDN   :: {data['e164']}", "green")
                self._log(f"  REGION   :: {data['region']}", "green")
                self._log(f"  OPERATOR :: {data['carrier']}", "green")
                self._log(f"  CONFIDENCE :: {c['label']} ({c['accuracy']})", "amber")
                self._log(f"  DETAIL   :: {c['detail']}", "dim")
                if data.get("geocode"):
                    g = data["geocode"]
                    self._log(f"  GEOCODE  :: {g['lat']:.4f}, {g['lng']:.4f}", "cyan")

            if imei_data and imei_data.get("imei"):
                self._log(f"  IMEI     :: {imei_data['imei']}", "cyan")
                self._log(f"  TAC      :: {imei_data['tac']}", "cyan")
                self._log(f"  DEVICE   :: {imei_data['brand']} {imei_data['model']}", "cyan")
                self._log(f"  LUHN     :: {'PASS' if imei_data['luhn_valid'] else 'FAIL'}", "cyan")
                if not imei_data.get("device_known") and imei_data.get("lookup_hint"):
                    self._log(f"  HINT     :: {imei_data['lookup_hint']}", "amber")
                self._log(f"  LIVE GPS :: {imei_data['live_location']}", "red")

            self._log("═" * 62, "cyan")
            self._log("[!] SIMULATION: No wiretap. No live GPS. OSINT only.", "red")
            self._log("[+] Press [LEGAL PATH] to show real investigation workflow.", "amber")
            self.status_var.set("TRACE COMPLETE")
            self.progress_var.set("[████████████████████] 100%")
            terminal_sfx.scan_success()

        except phonenumbers.phonenumberutil.NumberParseException:
            self._log("[!] TRACE FAILED — Invalid MSISDN.", "red")
            self.status_var.set("TRACE FAILED")
            self.progress_var.set("")
            terminal_sfx.scan_error()
        finally:
            self.scanning = False
            self.scan_btn.config(state="normal")

    def _resolve_coords(self):
        data = self.current_data
        if not data:
            return (20, 0), "UNKNOWN", 2, "NO DATA"

        if data.get("geocode"):
            g = data["geocode"]
            return (g["lat"], g["lng"]), g.get("display", data.get("region", "?")), 8, g["source"]

        iso = data.get("iso", "")
        if iso and iso != "XX":
            country_obj = pycountry.countries.get(alpha_2=iso)
            if country_obj:
                name = getattr(country_obj, "common_name", None) or country_obj.name
                if name in self.COUNTRY_COORDS:
                    return self.COUNTRY_COORDS[name], name, 5, "Country centroid (low confidence)"

        country = data.get("country", "")
        for name, coord in self.COUNTRY_COORDS.items():
            if name.lower() in country.lower():
                return coord, name, 5, "Country centroid (low confidence)"

        return (20, 0), country or "UNKNOWN", 2, "Fallback"

    def show_map(self):
        if not self.current_data or not self.current_data.get("e164"):
            self._log("[!] Run phone trace first for geo overlay.", "red")
            return

        self._log("[*] Rendering geolocation overlay ...", "dim")
        coords, region, zoom, src = self._resolve_coords()
        data = self.current_data
        c = data.get("confidence", {})

        map_obj = folium.Map(location=coords, zoom_start=zoom, tiles="CartoDB dark_matter")

        popup = f"""
        <div style="font-family:monospace;background:#000;color:#00ff41;padding:12px;">
        <b>GHOSTTRACE GEO OVERLAY</b><hr>
        TARGET: {data.get('e164', 'N/A')}<br>
        REGION: {region}<br>
        CONFIDENCE: {c.get('label', 'N/A')}<br>
        ACCURACY: {c.get('accuracy', 'N/A')}<br>
        SOURCE: {src}<br>
        <span style="color:#ff0040;">NOT LIVE GPS — OSINT ESTIMATE ONLY</span>
        </div>
        """

        folium.Marker(location=coords, popup=folium.Popup(popup, max_width=340),
                      tooltip=data.get("e164", ""), icon=folium.Icon(
                          color="green", icon="crosshairs", prefix="fa")).add_to(map_obj)

        radius = 50000 if c.get("level", 1) >= 2 else 250000
        folium.Circle(location=coords, radius=radius, color="#00ff41",
                      fill=True, fill_opacity=0.1,
                      popup=f"Uncertainty radius ~{c.get('accuracy', '?')}").add_to(map_obj)

        path = os.path.join(os.path.dirname(__file__), "ghosttrace_map.html")
        map_obj.save(path)
        webbrowser.open("file://" + os.path.abspath(path))
        self._log(f"[+] Geo overlay: {region} [{src}]", "green")

    def show_legal_path(self):
        win = Toplevel(self.window)
        win.title("GHOSTTRACE // LEGAL INTERCEPT PATHWAY")
        win.geometry("720x520")
        win.configure(bg=Theme.BG)

        Label(win, text="▸ HOW REAL TRACKING ACTUALLY WORKS", fg=Theme.CYAN,
              font=Theme.FONT_LG, bg=Theme.BG).pack(pady=10)
        Label(win, text="(For presentation — legal vs illegal methods)",
              fg=Theme.GRAY_TEXT, font=Theme.FONT_SM, bg=Theme.BG).pack()

        frame = Frame(win, bg=Theme.GREEN, padx=1, pady=1)
        frame.pack(fill="both", expand=True, padx=12, pady=8)
        inner = Frame(frame, bg=Theme.BG_PANEL)
        inner.pack(fill="both", expand=True)
        scroll = Scrollbar(inner)
        scroll.pack(side="right", fill="y")
        txt = Text(inner, bg=Theme.BG_PANEL, fg=Theme.GREEN, font=Theme.FONT_SM,
                   relief="flat", wrap="word", yscrollcommand=scroll.set, padx=12, pady=10)
        txt.pack(fill="both", expand=True)
        scroll.config(command=txt.yview)

        for step in LEGAL_INTERCEPT_STEPS:
            legal_color = Theme.RED if "ILLEGAL" in step["legal"] else Theme.GREEN
            block = (
                f"\n[{step['phase']}] {step['title']}\n"
                f"    Status : {step['status']}\n"
                f"    Legal  : {step['legal']}\n"
                f"    Detail : {step['detail']}\n"
            )
            txt.insert(END, block)
            # color last line legal tag
        txt.config(state="disabled")

        self._log("[*] Legal intercept pathway displayed.", "cyan")
        Button(win, text="[ CLOSE ]", bg=Theme.BG, fg=Theme.GRAY_TEXT,
               command=win.destroy).pack(pady=8)

    def export_data(self):
        if not self.current_data:
            self._log("[!] Nothing to exfiltrate.", "red")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Intel dump", "*.txt"), ("JSON", "*.json")],
            initialfilename=f"ghosttrace_{datetime.now():%Y%m%d_%H%M%S}",
        )
        if not path:
            return
        if path.lower().endswith(".json"):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.current_data, f, indent=2, default=str)
        else:
            d = self.current_data
            c = d.get("confidence", {})
            lines = [
                "GHOSTTRACE INTELLIGENCE EXFILTRATION",
                f"Session: {self.session_id}",
                f"Timestamp: {datetime.now():%Y-%m-%d %H:%M:%S}",
                "",
                "=== MSISDN ===",
                f"E.164: {d.get('e164', 'N/A')}",
                f"Region: {d.get('region', 'N/A')}",
                f"Operator: {d.get('carrier', 'N/A')}",
                f"Confidence: {c.get('label', 'N/A')}",
                f"Accuracy: {c.get('accuracy', 'N/A')}",
                "",
                "=== IMEI ===",
            ]
            imei = d.get("imei_intel", {})
            if imei:
                lines += [
                    f"IMEI: {imei.get('imei', 'N/A')}",
                    f"Device: {imei.get('brand', '?')} {imei.get('model', '?')}",
                    f"Luhn: {'PASS' if imei.get('luhn_valid') else 'FAIL'}",
                    f"Live location: {imei.get('live_location', 'BLOCKED')}",
                ]
            lines += ["", "DISCLAIMER: Educational OSINT simulation only."]
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
        self._log(f"[+] Exfiltrated → {path}", "green")

    def show_archive(self):
        if not self.targets:
            self._log("[!] Archive empty.", "amber")
            return
        win = Toplevel(self.window)
        win.title("TARGET ARCHIVE")
        win.geometry("700x400")
        win.configure(bg=Theme.BG)
        txt = Text(win, bg=Theme.BG_PANEL, fg=Theme.GREEN, font=Theme.FONT_SM)
        txt.pack(fill="both", expand=True, padx=12, pady=12)
        for t in reversed(self.targets):
            txt.insert(END, f"[{t.get('timestamp', '?')}] {t.get('e164', '—')} "
                            f"| {t.get('region', '?')} | IMEI:{t.get('imei_intel', {}).get('imei', '—')}\n")
        Button(win, text="CLOSE", command=win.destroy).pack(pady=6)

    def wipe_console(self):
        self.terminal.config(state="normal")
        self.terminal.delete("1.0", END)
        self.terminal.config(state="disabled")
        self._log("[SYS] Console wiped.", "dim")

    def clear_input(self):
        self.phone_entry.delete(0, END)
        self.imei_entry.delete(0, END)
        for v in {**self.phone_intel_vars, **self.imei_intel_vars}.values():
            v.set("—")
        self.current_data = {}
        self.confidence_var.set("NO TARGET")
        self._draw_confidence_bar(0)
        self.progress_var.set("")
        self.status_var.set("STANDBY — AWAITING TARGET")


if __name__ == "__main__":
    root = Tk()
    app = HackerPhoneTracker(root)
    root.mainloop()
