import json
import os
import re
import webbrowser
from datetime import datetime
from tkinter import (
    Tk, Toplevel, Label, Button, Entry, Frame, messagebox,
    StringVar, Text, Scrollbar, END, filedialog, ttk
)
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import folium
import phonenumbers
import pycountry
from phonenumbers import geocoder, carrier, timezone


class EnhancedPhoneTracker:
    """Advanced Phone Number Tracker with multiple features"""

    HISTORY_FILE = "tracker_history.json"
    MAX_HISTORY = 200

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
        "Bangladesh": (23.684994, 90.356331),
        "Egypt": (26.820553, 30.802498),
        "Philippines": (12.879721, 121.774017),
        "Vietnam": (14.058324, 108.277199),
        "Turkey": (38.963745, 35.243322),
        "Thailand": (15.870032, 100.992541),
        "Italy": (41.871940, 12.567380),
        "Spain": (40.463667, -3.749220),
        "Poland": (51.919438, 19.145136),
        "Argentina": (-38.416097, -63.616672),
        "Colombia": (4.570868, -74.297333),
        "Morocco": (31.791702, -7.092620),
        "Saudi Arabia": (23.885942, 45.079162),
        "Malaysia": (4.210484, 101.975766),
        "Ghana": (7.946527, -1.023194),
        "Nepal": (28.394857, 84.124008),
        "Rwanda": (-1.940278, 29.873888),
        "Zimbabwe": (-19.015438, 29.154857),
        "Zambia": (-13.133897, 27.849332),
        "Ethiopia": (9.145000, 40.489673),
        "Netherlands": (52.132633, 5.291266),
        "Belgium": (50.503887, 4.469936),
        "Sweden": (60.128161, 18.643501),
        "Norway": (60.472024, 8.468946),
        "Denmark": (56.263920, 9.501785),
        "Finland": (61.924110, 25.748151),
        "Ireland": (53.142367, -7.692054),
        "Portugal": (39.399872, -8.224454),
        "Greece": (39.074208, 21.824312),
        "Switzerland": (46.818188, 8.227512),
        "Austria": (47.516231, 14.550072),
        "Singapore": (1.352083, 103.819836),
        "Hong Kong": (22.396428, 114.109497),
        "New Zealand": (-40.900557, 174.885971),
        "Israel": (31.046051, 34.851612),
        "United Arab Emirates": (23.424076, 53.847818),
        "Qatar": (25.354826, 51.183884),
        "Kuwait": (29.311660, 47.481766),
        "South Korea": (35.907757, 127.766922),
        "Taiwan": (23.697810, 120.960515),
        "Ukraine": (48.379433, 31.165580),
        "Romania": (45.943161, 24.966760),
        "Czech Republic": (49.817492, 15.472962),
        "Hungary": (47.162494, 19.503304),
        "Chile": (-35.675147, -71.542969),
        "Peru": (-9.189967, -75.015152),
        "Venezuela": (6.423750, -66.589730),
        "Ecuador": (-1.831239, -78.183406),
        "Bolivia": (-16.290154, -63.588653),
        "Paraguay": (-23.442503, -58.443832),
        "Uruguay": (-32.522779, -55.765835),
        "Cuba": (21.521757, -77.781167),
        "Dominican Republic": (18.735693, -70.162651),
        "Puerto Rico": (18.220833, -66.590149),
        "Jamaica": (18.109581, -77.297508),
        "Trinidad and Tobago": (10.691803, -61.222503),
        "Costa Rica": (9.748917, -83.753428),
        "Panama": (8.537981, -80.782127),
        "Guatemala": (15.783471, -90.230759),
        "Honduras": (15.199999, -86.241905),
        "El Salvador": (13.794185, -88.896530),
        "Nicaragua": (12.865416, -85.207229),
        "Algeria": (28.033886, 1.659626),
        "Tunisia": (33.886917, 9.537499),
        "Libya": (26.335100, 17.228331),
        "Sudan": (12.862807, 30.217636),
        "South Sudan": (6.876992, 31.306979),
        "Angola": (-11.202692, 17.873887),
        "Mozambique": (-18.665695, 35.529562),
        "Madagascar": (-18.766947, 46.869107),
        "Cameroon": (7.369722, 12.354722),
        "Ivory Coast": (7.539989, -5.547080),
        "Senegal": (14.497401, -14.452362),
        "Mali": (17.570692, -3.996166),
        "Burkina Faso": (12.238333, -1.561593),
        "Niger": (17.607789, 8.081666),
        "Chad": (15.454166, 18.732207),
        "Somalia": (5.152149, 46.199616),
        "Afghanistan": (33.939110, 67.709953),
        "Iraq": (33.223191, 43.679291),
        "Iran": (32.427908, 53.688046),
        "Jordan": (30.585164, 36.238414),
        "Lebanon": (33.854721, 35.862285),
        "Syria": (34.802075, 38.996815),
        "Yemen": (15.552727, 48.516388),
        "Oman": (21.473533, 55.975413),
        "Bahrain": (26.066700, 50.557700),
        "Sri Lanka": (7.873054, 80.771797),
        "Myanmar": (21.916221, 95.955974),
        "Cambodia": (12.565679, 104.990963),
        "Laos": (19.856270, 102.495496),
        "Mongolia": (46.862496, 103.846656),
        "Kazakhstan": (48.019573, 66.923684),
        "Uzbekistan": (41.377491, 64.585262),
        "Azerbaijan": (40.143105, 47.576927),
        "Georgia": (42.315407, 43.356892),
        "Armenia": (40.069099, 45.038189),
        "Belarus": (53.709807, 27.953389),
        "Lithuania": (55.169438, 23.881275),
        "Latvia": (56.879635, 24.603189),
        "Estonia": (58.595272, 25.013607),
        "Slovakia": (48.669026, 19.699024),
        "Slovenia": (46.151241, 14.995463),
        "Croatia": (45.100000, 15.200000),
        "Serbia": (44.016521, 21.005859),
        "Bulgaria": (42.733883, 25.485830),
        "Albania": (41.153332, 20.168331),
        "North Macedonia": (41.608635, 21.745275),
        "Bosnia and Herzegovina": (43.915886, 17.679076),
        "Montenegro": (42.708678, 19.374390),
        "Iceland": (64.963051, -19.020835),
        "Luxembourg": (49.815273, 6.129583),
        "Malta": (35.937496, 14.375416),
        "Cyprus": (35.126413, 33.429859),
        "Fiji": (-17.713371, 178.065032),
        "Papua New Guinea": (-6.314993, 143.955550),
    }

    QUICK_PREFIXES = [
        ("+1 (US/CA)", "+1"),
        ("+44 (UK)", "+44"),
        ("+91 (India)", "+91"),
        ("+255 (Tanzania)", "+255"),
        ("+254 (Kenya)", "+254"),
        ("+256 (Uganda)", "+256"),
        ("+234 (Nigeria)", "+234"),
        ("+27 (South Africa)", "+27"),
        ("+49 (Germany)", "+49"),
        ("+33 (France)", "+33"),
        ("+86 (China)", "+86"),
        ("+81 (Japan)", "+81"),
        ("+61 (Australia)", "+61"),
        ("+55 (Brazil)", "+55"),
        ("+52 (Mexico)", "+52"),
    ]

    def __init__(self, root):
        self.window = root
        self.window.title("Enhanced Phone Number Tracker")
        self.window.geometry("720x780")
        self.window.configure(bg="#0f0f23")
        self.window.minsize(680, 700)

        self.history_path = os.path.join(os.path.dirname(__file__), self.HISTORY_FILE)
        self.tracking_history = self._load_history()
        self.current_data = {}
        self.last_location = None
        self.last_region_code = None

        self.build_ui()

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
                json.dump(self.tracking_history[-self.MAX_HISTORY :], f, indent=2)
        except OSError:
            pass

    @staticmethod
    def sanitize_phone_input(phone_input):
        cleaned = re.sub(r"[^\d+]", "", phone_input.strip())
        if cleaned and not cleaned.startswith("+"):
            cleaned = "+" + cleaned
        return cleaned

    def build_ui(self):
        header_frame = Frame(self.window, bg="#0f0f23")
        header_frame.pack(fill="x", pady=15)

        Label(
            header_frame,
            text="ENHANCED PHONE TRACKER",
            fg="#00d4ff",
            font=("Consolas", 26, "bold"),
            bg="#0f0f23",
        ).pack()

        Label(
            header_frame,
            text="Carrier, timezone, region, batch lookup & persistent history",
            fg="#666",
            font=("Consolas", 10),
            bg="#0f0f23",
        ).pack()

        input_frame = Frame(self.window, bg="#1a1a3e", padx=20, pady=15)
        input_frame.pack(fill="x", padx=30, pady=10)

        Label(
            input_frame,
            text="Enter Phone Number (with country code):",
            fg="#a8d8ea",
            font=("Consolas", 11),
            bg="#1a1a3e",
        ).pack(anchor="w")

        prefix_row = Frame(input_frame, bg="#1a1a3e")
        prefix_row.pack(fill="x", pady=(6, 0))

        Label(
            prefix_row,
            text="Quick prefix:",
            fg="#888",
            font=("Consolas", 9),
            bg="#1a1a3e",
        ).pack(side="left")

        self.prefix_var = StringVar()
        prefix_menu = ttk.Combobox(
            prefix_row,
            textvariable=self.prefix_var,
            values=[label for label, _ in self.QUICK_PREFIXES],
            state="readonly",
            width=18,
            font=("Consolas", 9),
        )
        prefix_menu.pack(side="left", padx=6)
        prefix_menu.bind("<<ComboboxSelected>>", self._apply_prefix)

        entry_row = Frame(input_frame, bg="#1a1a3e")
        entry_row.pack(fill="x", pady=8)

        self.phone_entry = Entry(
            entry_row,
            width=30,
            font=("Consolas", 14),
            justify="center",
            relief="flat",
            bg="#2d2d5a",
            fg="white",
            insertbackground="white",
        )
        self.phone_entry.pack(side="left", ipady=8, padx=(0, 10))
        self.phone_entry.bind("<Return>", lambda e: self.track_number())

        Button(
            entry_row,
            text="TRACK",
            bg="#00d4ff",
            fg="black",
            font=("Consolas", 11, "bold"),
            relief="flat",
            padx=25,
            pady=6,
            cursor="hand2",
            command=self.track_number,
        ).pack(side="left")

        btn_frame = Frame(self.window, bg="#0f0f23")
        btn_frame.pack(pady=10)

        buttons = [
            ("Show on Map", "#fc5185", self.show_map),
            ("Export Report", "#4ecca3", self.export_report),
            ("Copy Results", "#9b59b6", self.copy_results),
            ("Batch Track", "#3498db", self.batch_track),
            ("View History", "#f39c12", self.view_history),
            ("Clear", "#666", self.clear_results),
        ]

        for text, color, cmd in buttons:
            Button(
                btn_frame,
                text=text,
                bg=color,
                fg="white" if color not in ("#f39c12", "#00d4ff") else "black",
                font=("Consolas", 9, "bold"),
                relief="flat",
                padx=10,
                pady=5,
                cursor="hand2",
                command=cmd,
            ).pack(side="left", padx=3)

        results_container = Frame(self.window, bg="#0f0f23")
        results_container.pack(fill="both", expand=True, padx=30, pady=10)

        Label(
            results_container,
            text="TRACKING RESULTS",
            fg="#00d4ff",
            font=("Consolas", 12, "bold"),
            bg="#0f0f23",
        ).pack(anchor="w", pady=(0, 5))

        canvas_frame = Frame(results_container, bg="#1a1a3e")
        canvas_frame.pack(fill="both", expand=True)

        scrollbar = Scrollbar(canvas_frame)
        scrollbar.pack(side="right", fill="y")

        self.results_frame = Frame(canvas_frame, bg="#1a1a3e", padx=25, pady=20)
        self.results_frame.pack(fill="both", expand=True)

        self.result_vars = {
            "valid": StringVar(value="-"),
            "possible": StringVar(value="-"),
            "international": StringVar(value="-"),
            "national": StringVar(value="-"),
            "e164": StringVar(value="-"),
            "country": StringVar(value="-"),
            "region": StringVar(value="-"),
            "country_code": StringVar(value="-"),
            "iso_region": StringVar(value="-"),
            "carrier": StringVar(value="-"),
            "timezone": StringVar(value="-"),
            "local_time": StringVar(value="-"),
            "type": StringVar(value="-"),
        }

        labels = [
            ("Valid Number", "valid"),
            ("Possible Number", "possible"),
            ("International Format", "international"),
            ("National Format", "national"),
            ("E.164 Format", "e164"),
            ("Country/Region", "country"),
            ("Area/Region Detail", "region"),
            ("Country Code", "country_code"),
            ("ISO Region Code", "iso_region"),
            ("Carrier/Provider", "carrier"),
            ("Timezone(s)", "timezone"),
            ("Local Time (now)", "local_time"),
            ("Number Type", "type"),
        ]

        for label_text, var_key in labels:
            row = Frame(self.results_frame, bg="#1a1a3e")
            row.pack(fill="x", pady=3)

            Label(
                row,
                text=f"{label_text}:",
                fg="#888",
                font=("Consolas", 10),
                bg="#1a1a3e",
                width=20,
                anchor="w",
            ).pack(side="left")

            Label(
                row,
                textvariable=self.result_vars[var_key],
                fg="#00ff88",
                font=("Consolas", 10, "bold"),
                bg="#1a1a3e",
                anchor="w",
                wraplength=420,
                justify="left",
            ).pack(side="left", fill="x", expand=True)

        self.status_var = StringVar(
            value=f"Ready - {len(self.tracking_history)} entries in history"
        )
        Label(
            self.window,
            textvariable=self.status_var,
            fg="#666",
            font=("Consolas", 9),
            bg="#0f0f23",
            anchor="w",
        ).pack(fill="x", padx=30, pady=10)

    def _apply_prefix(self, _event=None):
        selected = self.prefix_var.get()
        for label, prefix in self.QUICK_PREFIXES:
            if label == selected:
                current = self.phone_entry.get().strip()
                digits = re.sub(r"\D", "", current)
                prefix_digits = prefix.lstrip("+")
                if digits.startswith(prefix_digits):
                    self.phone_entry.delete(0, "end")
                    self.phone_entry.insert(0, prefix + digits[len(prefix_digits) :])
                else:
                    self.phone_entry.delete(0, "end")
                    self.phone_entry.insert(0, prefix)
                break

    def get_number_type(self, parsed_number):
        number_type = phonenumbers.number_type(parsed_number)
        types = {
            phonenumbers.PhoneNumberType.MOBILE: "Mobile",
            phonenumbers.PhoneNumberType.FIXED_LINE: "Fixed Line (Landline)",
            phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "Fixed Line or Mobile",
            phonenumbers.PhoneNumberType.TOLL_FREE: "Toll Free",
            phonenumbers.PhoneNumberType.PREMIUM_RATE: "Premium Rate",
            phonenumbers.PhoneNumberType.VOIP: "VoIP (Internet)",
            phonenumbers.PhoneNumberType.PERSONAL_NUMBER: "Personal Number",
            phonenumbers.PhoneNumberType.PAGER: "Pager",
            phonenumbers.PhoneNumberType.UAN: "UAN (Universal Access)",
            phonenumbers.PhoneNumberType.VOICEMAIL: "Voicemail",
            phonenumbers.PhoneNumberType.SHARED_COST: "Shared Cost",
        }
        return types.get(number_type, "Unknown")

    def _get_local_time(self, tz_list):
        if not tz_list:
            return "Unknown"
        try:
            now = datetime.now(ZoneInfo(tz_list[0]))
            return now.strftime("%Y-%m-%d %H:%M:%S %Z")
        except ZoneInfoNotFoundError:
            return "Unknown"

    def _parse_and_analyze(self, phone_input):
        parsed = phonenumbers.parse(phone_input)
        is_valid = phonenumbers.is_valid_number(parsed)
        is_possible = phonenumbers.is_possible_number(parsed)

        international = phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
        )
        national = phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.NATIONAL
        )
        e164 = phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.E164
        )

        country = geocoder.description_for_number(parsed, "en") or "Unknown"
        region_code = phonenumbers.region_code_for_number(parsed) or "Unknown"
        region_detail = country
        if region_code != "Unknown":
            country_obj = pycountry.countries.get(alpha_2=region_code)
            if country_obj:
                official = getattr(country_obj, "official_name", country_obj.name)
                if official and official.lower() != country.lower():
                    region_detail = f"{country} ({official})"
        country_code = f"+{parsed.country_code}"

        carrier_name = carrier.name_for_number(parsed, "en") or "Unknown/Not Available"
        tz_list = list(timezone.time_zones_for_number(parsed))
        tz_str = ", ".join(tz_list) if tz_list else "Unknown"
        num_type = self.get_number_type(parsed)
        local_time = self._get_local_time(tz_list)

        return {
            "phone": phone_input,
            "valid": is_valid,
            "possible": is_possible,
            "international": international,
            "national": national,
            "e164": e164,
            "country": country,
            "region": region_detail,
            "country_code": country_code,
            "iso_region": region_code,
            "carrier": carrier_name,
            "timezone": tz_str,
            "local_time": local_time,
            "type": num_type,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _display_results(self, data):
        self.result_vars["valid"].set("Yes" if data["valid"] else "No")
        self.result_vars["possible"].set("Yes" if data["possible"] else "No")
        self.result_vars["international"].set(data["international"])
        self.result_vars["national"].set(data["national"])
        self.result_vars["e164"].set(data["e164"])
        self.result_vars["country"].set(data["country"])
        self.result_vars["region"].set(data["region"])
        self.result_vars["country_code"].set(data["country_code"])
        self.result_vars["iso_region"].set(data["iso_region"])
        self.result_vars["carrier"].set(data["carrier"])
        self.result_vars["timezone"].set(data["timezone"])
        self.result_vars["local_time"].set(data["local_time"])
        self.result_vars["type"].set(data["type"])

        self.last_location = data["country"]
        self.last_region_code = data["iso_region"]
        self.current_data = data

    def track_number(self, phone_override=None):
        phone_input = self.sanitize_phone_input(
            phone_override if phone_override else self.phone_entry.get()
        )

        if not phone_input or phone_input == "+":
            messagebox.showwarning("Warning", "Please enter a phone number!")
            return

        if phone_override is None:
            self.phone_entry.delete(0, "end")
            self.phone_entry.insert(0, phone_input)

        self.status_var.set(f"Tracking {phone_input}...")
        self.window.update()

        try:
            data = self._parse_and_analyze(phone_input)
            self._display_results(data)

            self.tracking_history.append(data.copy())
            self._save_history()

            self.status_var.set(
                f"Tracked: {data['international']} | History: {len(self.tracking_history)}"
            )

        except phonenumbers.phonenumberutil.NumberParseException as e:
            error_msg = str(e)
            if "Invalid country code" in error_msg:
                messagebox.showerror(
                    "Error",
                    "Invalid country code! Include + and a valid country code.",
                )
            elif "not a number" in error_msg.lower():
                messagebox.showerror("Error", "This doesn't appear to be a valid phone number.")
            else:
                messagebox.showerror("Error", f"Could not parse number:\n{error_msg}")
            self.status_var.set("Error - Invalid phone number")
            if phone_override is None:
                self.clear_results(keep_input=True)

    def _resolve_coords(self):
        if self.last_region_code and self.last_region_code != "Unknown":
            country_obj = pycountry.countries.get(alpha_2=self.last_region_code)
            if country_obj:
                name = getattr(country_obj, "common_name", None) or country_obj.name
                if name in self.COUNTRY_COORDS:
                    return self.COUNTRY_COORDS[name], name, 5

        if self.last_location:
            for country, coord in self.COUNTRY_COORDS.items():
                if (
                    country.lower() in self.last_location.lower()
                    or self.last_location.lower() in country.lower()
                ):
                    return coord, country, 5

        return (20, 0), self.last_location or "Unknown", 2

    def show_map(self):
        if not self.current_data:
            messagebox.showwarning("Warning", "Please track a number first!")
            return

        self.status_var.set("Generating map...")
        self.window.update()

        coords, matched_country, zoom = self._resolve_coords()

        map_obj = folium.Map(
            location=coords,
            zoom_start=zoom,
            tiles="CartoDB dark_matter",
        )

        popup_html = f"""
        <div style="font-family: Arial; min-width: 220px;">
            <h4 style="color: #00d4ff; margin: 0;">{matched_country}</h4>
            <hr style="margin: 5px 0;">
            <p><b>Phone:</b> {self.current_data.get('international', 'N/A')}</p>
            <p><b>Region:</b> {self.current_data.get('region', 'N/A')}</p>
            <p><b>Carrier:</b> {self.current_data.get('carrier', 'N/A')}</p>
            <p><b>Type:</b> {self.current_data.get('type', 'N/A')}</p>
            <p><b>Timezone:</b> {self.current_data.get('timezone', 'N/A')}</p>
            <p><b>Local Time:</b> {self.current_data.get('local_time', 'N/A')}</p>
        </div>
        """

        folium.Marker(
            location=coords,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=f"{matched_country} — click for details",
            icon=folium.Icon(color="red", icon="phone", prefix="fa"),
        ).add_to(map_obj)

        folium.Circle(
            location=coords,
            radius=150000,
            color="#00d4ff",
            fill=True,
            fill_opacity=0.15,
            popup="Approximate country-level area (not GPS location)",
        ).add_to(map_obj)

        map_path = os.path.join(os.path.dirname(__file__), "phone_location_map.html")
        map_obj.save(map_path)
        webbrowser.open("file://" + os.path.abspath(map_path))

        self.status_var.set(f"Map opened for {matched_country}")

    def _build_report_text(self, data):
        return f"""
================================================================================
                    PHONE NUMBER TRACKING REPORT
================================================================================

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Tracked At: {data.get('timestamp', 'N/A')}

--------------------------------------------------------------------------------
PHONE NUMBER INFORMATION
--------------------------------------------------------------------------------

Phone Number:        {data.get('phone', 'N/A')}
International:       {data.get('international', 'N/A')}
National:            {data.get('national', 'N/A')}
E.164:               {data.get('e164', 'N/A')}
Valid Number:        {'Yes' if data.get('valid') else 'No'}
Possible Number:     {'Yes' if data.get('possible') else 'No'}

--------------------------------------------------------------------------------
LOCATION INFORMATION
--------------------------------------------------------------------------------

Country/Region:      {data.get('country', 'N/A')}
Area/Region Detail:  {data.get('region', 'N/A')}
Country Code:        {data.get('country_code', 'N/A')}
ISO Region Code:     {data.get('iso_region', 'N/A')}
Timezone(s):         {data.get('timezone', 'N/A')}
Local Time:          {data.get('local_time', 'N/A')}

--------------------------------------------------------------------------------
CARRIER INFORMATION
--------------------------------------------------------------------------------

Carrier/Provider:    {data.get('carrier', 'N/A')}
Number Type:         {data.get('type', 'N/A')}

--------------------------------------------------------------------------------
DISCLAIMER
--------------------------------------------------------------------------------

This report contains publicly available information derived from the phone
number format. It does NOT provide real-time location tracking or personal
information. This tool is for educational purposes only.

================================================================================
                    END OF REPORT
================================================================================
"""

    def export_report(self):
        if not self.current_data:
            messagebox.showwarning("Warning", "No data to export! Track a number first.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("JSON files", "*.json"),
                ("All files", "*.*"),
            ],
            initialfilename=(
                f"phone_report_{self.current_data.get('e164', 'unknown').replace('+', '')}"
            ),
        )

        if not file_path:
            return

        try:
            if file_path.lower().endswith(".json"):
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(self.current_data, f, indent=2)
            else:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self._build_report_text(self.current_data))
            messagebox.showinfo("Success", f"Report saved to:\n{file_path}")
            self.status_var.set("Report exported successfully")
        except OSError as e:
            messagebox.showerror("Error", f"Could not save report:\n{e}")

    def copy_results(self):
        if not self.current_data:
            messagebox.showwarning("Warning", "No results to copy! Track a number first.")
            return

        lines = [
            f"{label}: {self.result_vars[key].get()}"
            for label, key in [
                ("Valid", "valid"),
                ("Possible", "possible"),
                ("International", "international"),
                ("National", "national"),
                ("E.164", "e164"),
                ("Country", "country"),
                ("Region", "region"),
                ("Country Code", "country_code"),
                ("ISO Region", "iso_region"),
                ("Carrier", "carrier"),
                ("Timezone", "timezone"),
                ("Local Time", "local_time"),
                ("Type", "type"),
            ]
        ]
        text = "\n".join(lines)
        self.window.clipboard_clear()
        self.window.clipboard_append(text)
        self.status_var.set("Results copied to clipboard")

    def batch_track(self):
        dialog = Toplevel(self.window)
        dialog.title("Batch Phone Tracker")
        dialog.geometry("520x380")
        dialog.configure(bg="#1a1a3e")
        dialog.transient(self.window)
        dialog.grab_set()

        Label(
            dialog,
            text="BATCH TRACKING",
            fg="#00d4ff",
            font=("Consolas", 14, "bold"),
            bg="#1a1a3e",
        ).pack(pady=10)

        Label(
            dialog,
            text="Enter one number per line (with country code):",
            fg="#a8d8ea",
            font=("Consolas", 10),
            bg="#1a1a3e",
        ).pack(anchor="w", padx=20)

        text_frame = Frame(dialog, bg="#1a1a3e")
        text_frame.pack(fill="both", expand=True, padx=20, pady=10)

        scrollbar = Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        batch_text = Text(
            text_frame,
            bg="#0f0f23",
            fg="white",
            font=("Consolas", 10),
            yscrollcommand=scrollbar.set,
            insertbackground="white",
        )
        batch_text.pack(fill="both", expand=True)
        scrollbar.config(command=batch_text.yview)
        batch_text.insert("1.0", "+14155552671\n+447911123456\n+255712345678")

        result_label = Label(
            dialog,
            text="",
            fg="#00ff88",
            font=("Consolas", 9),
            bg="#1a1a3e",
            wraplength=460,
            justify="left",
        )
        result_label.pack(padx=20, pady=(0, 10))

        def run_batch():
            raw = batch_text.get("1.0", END).strip()
            numbers = [line.strip() for line in raw.splitlines() if line.strip()]
            if not numbers:
                messagebox.showwarning("Warning", "Enter at least one phone number.")
                return

            success, failed = 0, []
            for num in numbers:
                phone = self.sanitize_phone_input(num)
                try:
                    data = self._parse_and_analyze(phone)
                    self.tracking_history.append(data.copy())
                    success += 1
                except phonenumbers.phonenumberutil.NumberParseException:
                    failed.append(num)

            self._save_history()
            if numbers:
                last_phone = self.sanitize_phone_input(numbers[-1])
                try:
                    data = self._parse_and_analyze(last_phone)
                    self._display_results(data)
                    self.phone_entry.delete(0, "end")
                    self.phone_entry.insert(0, last_phone)
                except phonenumbers.phonenumberutil.NumberParseException:
                    pass

            summary = f"Batch complete: {success} tracked, {len(failed)} failed."
            if failed:
                summary += f" Failed: {', '.join(failed[:5])}"
                if len(failed) > 5:
                    summary += f" (+{len(failed) - 5} more)"
            result_label.config(text=summary)
            self.status_var.set(summary)

        btn_row = Frame(dialog, bg="#1a1a3e")
        btn_row.pack(pady=10)

        Button(
            btn_row,
            text="Run Batch",
            bg="#3498db",
            fg="white",
            font=("Consolas", 10, "bold"),
            relief="flat",
            padx=15,
            command=run_batch,
        ).pack(side="left", padx=5)

        Button(
            btn_row,
            text="Close",
            bg="#666",
            fg="white",
            font=("Consolas", 10, "bold"),
            relief="flat",
            padx=15,
            command=dialog.destroy,
        ).pack(side="left", padx=5)

    def view_history(self):
        if not self.tracking_history:
            messagebox.showinfo("History", "No tracking history yet.")
            return

        history_window = Toplevel(self.window)
        history_window.title("Tracking History")
        history_window.geometry("750x450")
        history_window.configure(bg="#1a1a3e")

        Label(
            history_window,
            text="TRACKING HISTORY",
            fg="#00d4ff",
            font=("Consolas", 16, "bold"),
            bg="#1a1a3e",
        ).pack(pady=10)

        search_row = Frame(history_window, bg="#1a1a3e")
        search_row.pack(fill="x", padx=20)

        Label(
            search_row,
            text="Search:",
            fg="#888",
            font=("Consolas", 10),
            bg="#1a1a3e",
        ).pack(side="left")

        search_var = StringVar()
        search_entry = Entry(
            search_row,
            textvariable=search_var,
            font=("Consolas", 10),
            bg="#2d2d5a",
            fg="white",
            insertbackground="white",
            relief="flat",
        )
        search_entry.pack(side="left", fill="x", expand=True, padx=8, ipady=4)

        tree_frame = Frame(history_window, bg="#1a1a3e")
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("time", "phone", "country", "carrier", "type")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=12)
        tree.heading("time", text="Time")
        tree.heading("phone", text="Phone")
        tree.heading("country", text="Country")
        tree.heading("carrier", text="Carrier")
        tree.heading("type", text="Type")
        tree.column("time", width=130)
        tree.column("phone", width=150)
        tree.column("country", width=120)
        tree.column("carrier", width=130)
        tree.column("type", width=100)

        vsb = Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        def populate(filter_text=""):
            tree.delete(*tree.get_children())
            query = filter_text.lower()
            for i, entry in enumerate(reversed(self.tracking_history)):
                values = (
                    entry.get("timestamp", ""),
                    entry.get("international", ""),
                    entry.get("country", ""),
                    entry.get("carrier", ""),
                    entry.get("type", ""),
                )
                if query and not any(query in str(v).lower() for v in values):
                    continue
                tree.insert("", "end", iid=str(len(self.tracking_history) - 1 - i), values=values)

        def on_search(*_args):
            populate(search_var.get())

        search_var.trace_add("write", on_search)
        populate()

        def retrack_selected():
            selected = tree.selection()
            if not selected:
                messagebox.showinfo("History", "Select an entry to re-track.")
                return
            idx = int(selected[0])
            entry = self.tracking_history[idx]
            phone = entry.get("phone") or entry.get("e164", "")
            history_window.destroy()
            self.track_number(phone_override=phone)

        def export_all():
            path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfilename="tracking_history_export.json",
            )
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self.tracking_history, f, indent=2)
                messagebox.showinfo("Exported", f"History saved to:\n{path}")

        def clear_history():
            if messagebox.askyesno("Clear History", "Delete all tracking history?"):
                self.tracking_history.clear()
                self._save_history()
                history_window.destroy()
                self.status_var.set("History cleared")

        btn_row = Frame(history_window, bg="#1a1a3e")
        btn_row.pack(pady=10)

        for text, color, cmd in [
            ("Re-track Selected", "#00d4ff", retrack_selected),
            ("Export All", "#4ecca3", export_all),
            ("Clear History", "#fc5185", clear_history),
            ("Close", "#666", history_window.destroy),
        ]:
            Button(
                btn_row,
                text=text,
                bg=color,
                fg="black" if color == "#00d4ff" else "white",
                font=("Consolas", 9, "bold"),
                relief="flat",
                padx=12,
                pady=5,
                command=cmd,
            ).pack(side="left", padx=4)

    def clear_results(self, keep_input=False):
        if not keep_input:
            self.phone_entry.delete(0, "end")
        for var in self.result_vars.values():
            var.set("-")
        self.last_location = None
        self.last_region_code = None
        self.current_data = {}
        self.status_var.set(
            f"Cleared - {len(self.tracking_history)} entries in history"
        )


if __name__ == "__main__":
    root = Tk()
    app = EnhancedPhoneTracker(root)
    root.mainloop()
