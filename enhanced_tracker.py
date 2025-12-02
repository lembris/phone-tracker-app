import phonenumbers
from phonenumbers import geocoder, carrier, timezone
import folium
import webbrowser
import os
from datetime import datetime
from tkinter import (
    Tk, Label, Button, Entry, Frame, messagebox, 
    StringVar, Text, Scrollbar, END, filedialog
)


class EnhancedPhoneTracker:
    """Advanced Phone Number Tracker with multiple features"""
    
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
    }

    def __init__(self, root):
        self.window = root
        self.window.title("Enhanced Phone Number Tracker")
        self.window.geometry("700x700")
        self.window.configure(bg="#0f0f23")
        self.window.resizable(False, False)
        
        self.tracking_history = []
        self.current_data = {}
        
        self.build_ui()

    def build_ui(self):
        """Build the user interface"""
        # Header
        header_frame = Frame(self.window, bg="#0f0f23")
        header_frame.pack(fill="x", pady=15)
        
        Label(
            header_frame,
            text="ENHANCED PHONE TRACKER",
            fg="#00d4ff",
            font=("Consolas", 28, "bold"),
            bg="#0f0f23",
        ).pack()
        
        Label(
            header_frame,
            text="Track carrier, location, timezone & more",
            fg="#666",
            font=("Consolas", 10),
            bg="#0f0f23",
        ).pack()

        # Input Section
        input_frame = Frame(self.window, bg="#1a1a3e", padx=20, pady=15)
        input_frame.pack(fill="x", padx=30, pady=10)

        Label(
            input_frame,
            text="Enter Phone Number (with country code):",
            fg="#a8d8ea",
            font=("Consolas", 11),
            bg="#1a1a3e",
        ).pack(anchor="w")

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
            insertbackground="white"
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

        # Buttons Row
        btn_frame = Frame(self.window, bg="#0f0f23")
        btn_frame.pack(pady=10)

        buttons = [
            ("Show on Map", "#fc5185", self.show_map),
            ("Export Report", "#4ecca3", self.export_report),
            ("View History", "#f39c12", self.view_history),
            ("Clear", "#666", self.clear_results),
        ]

        for text, color, cmd in buttons:
            Button(
                btn_frame,
                text=text,
                bg=color,
                fg="white" if color != "#f39c12" else "black",
                font=("Consolas", 10, "bold"),
                relief="flat",
                padx=12,
                pady=5,
                cursor="hand2",
                command=cmd,
            ).pack(side="left", padx=4)

        # Results Section
        results_container = Frame(self.window, bg="#0f0f23")
        results_container.pack(fill="both", expand=True, padx=30, pady=10)

        Label(
            results_container,
            text="TRACKING RESULTS",
            fg="#00d4ff",
            font=("Consolas", 12, "bold"),
            bg="#0f0f23",
        ).pack(anchor="w", pady=(0, 5))

        self.results_frame = Frame(results_container, bg="#1a1a3e", padx=25, pady=20)
        self.results_frame.pack(fill="both", expand=True)

        # Result Labels
        self.result_vars = {
            "valid": StringVar(value="-"),
            "international": StringVar(value="-"),
            "national": StringVar(value="-"),
            "country": StringVar(value="-"),
            "country_code": StringVar(value="-"),
            "carrier": StringVar(value="-"),
            "timezone": StringVar(value="-"),
            "type": StringVar(value="-"),
            "possible": StringVar(value="-"),
        }

        labels = [
            ("Valid Number", "valid"),
            ("International Format", "international"),
            ("National Format", "national"),
            ("Country/Region", "country"),
            ("Country Code", "country_code"),
            ("Carrier/Provider", "carrier"),
            ("Timezone(s)", "timezone"),
            ("Number Type", "type"),
            ("Possible Number", "possible"),
        ]

        for i, (label_text, var_key) in enumerate(labels):
            row = Frame(self.results_frame, bg="#1a1a3e")
            row.pack(fill="x", pady=4)

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
            ).pack(side="left", fill="x", expand=True)

        # Status Bar
        self.status_var = StringVar(value="Ready - Enter a phone number to begin")
        Label(
            self.window,
            textvariable=self.status_var,
            fg="#666",
            font=("Consolas", 9),
            bg="#0f0f23",
            anchor="w",
        ).pack(fill="x", padx=30, pady=10)

        self.last_location = None

    def get_number_type(self, parsed_number):
        """Get human-readable number type"""
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

    def track_number(self):
        """Track phone number and extract all information"""
        phone_input = self.phone_entry.get().strip()

        if not phone_input:
            messagebox.showwarning("Warning", "Please enter a phone number!")
            return

        # Add + if missing
        if not phone_input.startswith("+"):
            phone_input = "+" + phone_input

        self.status_var.set(f"Tracking {phone_input}...")
        self.window.update()

        try:
            # Parse the phone number
            parsed = phonenumbers.parse(phone_input)

            # Validation
            is_valid = phonenumbers.is_valid_number(parsed)
            is_possible = phonenumbers.is_possible_number(parsed)
            
            self.result_vars["valid"].set("Yes" if is_valid else "No")
            self.result_vars["possible"].set("Yes" if is_possible else "No")

            # Formats
            international = phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
            )
            national = phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.NATIONAL
            )
            self.result_vars["international"].set(international)
            self.result_vars["national"].set(national)

            # Country info
            country = geocoder.description_for_number(parsed, "en")
            country_code = f"+{parsed.country_code}"
            self.result_vars["country"].set(country if country else "Unknown")
            self.result_vars["country_code"].set(country_code)
            self.last_location = country

            # Carrier
            carrier_name = carrier.name_for_number(parsed, "en")
            self.result_vars["carrier"].set(carrier_name if carrier_name else "Unknown/Not Available")

            # Timezone
            tz = timezone.time_zones_for_number(parsed)
            tz_str = ", ".join(tz) if tz else "Unknown"
            self.result_vars["timezone"].set(tz_str)

            # Number type
            num_type = self.get_number_type(parsed)
            self.result_vars["type"].set(num_type)

            # Store current data
            self.current_data = {
                "phone": phone_input,
                "valid": is_valid,
                "international": international,
                "national": national,
                "country": country,
                "country_code": country_code,
                "carrier": carrier_name or "Unknown",
                "timezone": tz_str,
                "type": num_type,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            # Add to history
            self.tracking_history.append(self.current_data.copy())

            self.status_var.set(f"Successfully tracked: {international}")

        except phonenumbers.phonenumberutil.NumberParseException as e:
            error_msg = str(e)
            if "Invalid country code" in error_msg:
                messagebox.showerror("Error", "Invalid country code! Make sure to include + and country code.")
            elif "not a number" in error_msg.lower():
                messagebox.showerror("Error", "This doesn't appear to be a valid phone number.")
            else:
                messagebox.showerror("Error", f"Could not parse number:\n{error_msg}")
            self.status_var.set("Error - Invalid phone number")
            self.clear_results()

    def show_map(self):
        """Generate and open an interactive map"""
        if not self.last_location:
            messagebox.showwarning("Warning", "Please track a number first!")
            return

        self.status_var.set("Generating map...")
        self.window.update()

        # Find coordinates
        coords = None
        matched_country = None
        for country, coord in self.COUNTRY_COORDS.items():
            if country.lower() in self.last_location.lower() or self.last_location.lower() in country.lower():
                coords = coord
                matched_country = country
                break

        if not coords:
            coords = (20, 0)
            zoom = 2
            matched_country = self.last_location
        else:
            zoom = 5

        # Create map with dark theme
        map_obj = folium.Map(
            location=coords, 
            zoom_start=zoom,
            tiles="CartoDB dark_matter"
        )

        # Add marker
        popup_html = f"""
        <div style="font-family: Arial; min-width: 200px;">
            <h4 style="color: #00d4ff; margin: 0;">{matched_country}</h4>
            <hr style="margin: 5px 0;">
            <p><b>Phone:</b> {self.current_data.get('international', 'N/A')}</p>
            <p><b>Carrier:</b> {self.current_data.get('carrier', 'N/A')}</p>
            <p><b>Type:</b> {self.current_data.get('type', 'N/A')}</p>
            <p><b>Timezone:</b> {self.current_data.get('timezone', 'N/A')}</p>
        </div>
        """
        
        folium.Marker(
            location=coords,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"Click for details - {matched_country}",
            icon=folium.Icon(color="red", icon="phone", prefix="fa"),
        ).add_to(map_obj)

        # Add circle for approximate area
        folium.Circle(
            location=coords,
            radius=150000,
            color="#00d4ff",
            fill=True,
            fill_opacity=0.15,
            popup="Approximate coverage area",
        ).add_to(map_obj)

        # Save and open
        map_path = os.path.join(os.path.dirname(__file__), "phone_location_map.html")
        map_obj.save(map_path)
        webbrowser.open("file://" + os.path.abspath(map_path))
        
        self.status_var.set(f"Map opened for {matched_country}")

    def export_report(self):
        """Export tracking report to a text file"""
        if not self.current_data:
            messagebox.showwarning("Warning", "No data to export! Track a number first.")
            return

        report = f"""
================================================================================
                    PHONE NUMBER TRACKING REPORT
================================================================================

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

--------------------------------------------------------------------------------
PHONE NUMBER INFORMATION
--------------------------------------------------------------------------------

Phone Number:        {self.current_data.get('phone', 'N/A')}
International:       {self.current_data.get('international', 'N/A')}
National:            {self.current_data.get('national', 'N/A')}
Valid Number:        {'Yes' if self.current_data.get('valid') else 'No'}

--------------------------------------------------------------------------------
LOCATION INFORMATION
--------------------------------------------------------------------------------

Country/Region:      {self.current_data.get('country', 'N/A')}
Country Code:        {self.current_data.get('country_code', 'N/A')}
Timezone(s):         {self.current_data.get('timezone', 'N/A')}

--------------------------------------------------------------------------------
CARRIER INFORMATION
--------------------------------------------------------------------------------

Carrier/Provider:    {self.current_data.get('carrier', 'N/A')}
Number Type:         {self.current_data.get('type', 'N/A')}

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

        # Ask where to save
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfilename=f"phone_report_{self.current_data.get('phone', 'unknown').replace('+', '')}.txt"
        )
        
        if file_path:
            with open(file_path, "w") as f:
                f.write(report)
            messagebox.showinfo("Success", f"Report saved to:\n{file_path}")
            self.status_var.set(f"Report exported successfully")

    def view_history(self):
        """View tracking history"""
        if not self.tracking_history:
            messagebox.showinfo("History", "No tracking history yet.")
            return

        # Create history window
        history_window = Tk()
        history_window.title("Tracking History")
        history_window.geometry("600x400")
        history_window.configure(bg="#1a1a3e")

        Label(
            history_window,
            text="TRACKING HISTORY",
            fg="#00d4ff",
            font=("Consolas", 16, "bold"),
            bg="#1a1a3e",
        ).pack(pady=10)

        # Text area with scrollbar
        text_frame = Frame(history_window, bg="#1a1a3e")
        text_frame.pack(fill="both", expand=True, padx=20, pady=10)

        scrollbar = Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        text_area = Text(
            text_frame,
            bg="#0f0f23",
            fg="#00ff88",
            font=("Consolas", 10),
            yscrollcommand=scrollbar.set,
            wrap="word",
        )
        text_area.pack(fill="both", expand=True)
        scrollbar.config(command=text_area.yview)

        # Populate history
        for i, entry in enumerate(reversed(self.tracking_history), 1):
            text_area.insert(END, f"--- Entry #{len(self.tracking_history) - i + 1} ---\n")
            text_area.insert(END, f"Time: {entry.get('timestamp', 'N/A')}\n")
            text_area.insert(END, f"Phone: {entry.get('international', 'N/A')}\n")
            text_area.insert(END, f"Country: {entry.get('country', 'N/A')}\n")
            text_area.insert(END, f"Carrier: {entry.get('carrier', 'N/A')}\n")
            text_area.insert(END, f"Type: {entry.get('type', 'N/A')}\n\n")

        text_area.config(state="disabled")

        Button(
            history_window,
            text="Close",
            bg="#fc5185",
            fg="white",
            font=("Consolas", 10, "bold"),
            command=history_window.destroy,
        ).pack(pady=10)

        history_window.mainloop()

    def clear_results(self):
        """Clear all results"""
        self.phone_entry.delete(0, "end")
        for var in self.result_vars.values():
            var.set("-")
        self.last_location = None
        self.current_data = {}
        self.status_var.set("Cleared - Ready for new search")


if __name__ == "__main__":
    root = Tk()
    app = EnhancedPhoneTracker(root)
    root.mainloop()
