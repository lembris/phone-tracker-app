"""
Police Phone Tracker - Case Management System
For authorized law enforcement use only.
"""

import sqlite3
import hashlib
import os
import phonenumbers
from phonenumbers import geocoder, carrier, timezone
from datetime import datetime
from tkinter import (
    Tk, Label, Button, Entry, Frame, messagebox, StringVar,
    Text, Scrollbar, END, Toplevel, ttk, Listbox, SINGLE
)
from tkinter.filedialog import asksaveasfilename
import folium
import webbrowser


class Database:
    """SQLite Database Handler"""
    
    def __init__(self, db_path="police_tracker.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Officers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS officers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                badge_number TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                rank TEXT,
                department TEXT,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        # Cases table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_number TEXT UNIQUE NOT NULL,
                phone_number TEXT NOT NULL,
                imei TEXT,
                victim_name TEXT,
                victim_contact TEXT,
                victim_address TEXT,
                incident_date DATE,
                incident_location TEXT,
                description TEXT,
                status TEXT DEFAULT 'Open',
                assigned_officer_id INTEGER,
                country TEXT,
                carrier TEXT,
                phone_type TEXT,
                timezone TEXT,
                last_known_location TEXT,
                carrier_response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (assigned_officer_id) REFERENCES officers(id)
            )
        ''')
        
        # Audit log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                officer_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (officer_id) REFERENCES officers(id)
            )
        ''')
        
        # Case notes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS case_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER,
                officer_id INTEGER,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (case_id) REFERENCES cases(id),
                FOREIGN KEY (officer_id) REFERENCES officers(id)
            )
        ''')
        
        # Create default admin if not exists
        cursor.execute("SELECT * FROM officers WHERE badge_number = 'ADMIN001'")
        if not cursor.fetchone():
            admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute('''
                INSERT INTO officers (badge_number, name, rank, department, password_hash)
                VALUES (?, ?, ?, ?, ?)
            ''', ("ADMIN001", "System Administrator", "Admin", "IT Department", admin_hash))
        
        conn.commit()
        conn.close()
    
    def verify_officer(self, badge_number, password):
        """Verify officer login"""
        conn = self.get_connection()
        cursor = conn.cursor()
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute('''
            SELECT id, name, rank, department FROM officers 
            WHERE badge_number = ? AND password_hash = ? AND is_active = 1
        ''', (badge_number, password_hash))
        result = cursor.fetchone()
        conn.close()
        return result
    
    def log_action(self, officer_id, action, details=""):
        """Log officer actions for audit"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO audit_log (officer_id, action, details)
            VALUES (?, ?, ?)
        ''', (officer_id, action, details))
        conn.commit()
        conn.close()
    
    def create_case(self, case_data):
        """Create a new case"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO cases (
                case_number, phone_number, imei, victim_name, victim_contact,
                victim_address, incident_date, incident_location, description,
                assigned_officer_id, country, carrier, phone_type, timezone
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            case_data['case_number'], case_data['phone_number'], case_data.get('imei'),
            case_data['victim_name'], case_data.get('victim_contact'),
            case_data.get('victim_address'), case_data.get('incident_date'),
            case_data.get('incident_location'), case_data.get('description'),
            case_data['officer_id'], case_data.get('country'),
            case_data.get('carrier'), case_data.get('phone_type'),
            case_data.get('timezone')
        ))
        case_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return case_id
    
    def get_all_cases(self, officer_id=None):
        """Get all cases or cases for specific officer"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if officer_id:
            cursor.execute('''
                SELECT c.*, o.name as officer_name FROM cases c
                LEFT JOIN officers o ON c.assigned_officer_id = o.id
                WHERE c.assigned_officer_id = ?
                ORDER BY c.created_at DESC
            ''', (officer_id,))
        else:
            cursor.execute('''
                SELECT c.*, o.name as officer_name FROM cases c
                LEFT JOIN officers o ON c.assigned_officer_id = o.id
                ORDER BY c.created_at DESC
            ''')
        cases = cursor.fetchall()
        conn.close()
        return cases
    
    def get_case(self, case_id):
        """Get specific case details"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.*, o.name as officer_name FROM cases c
            LEFT JOIN officers o ON c.assigned_officer_id = o.id
            WHERE c.id = ?
        ''', (case_id,))
        case = cursor.fetchone()
        conn.close()
        return case
    
    def update_case_status(self, case_id, status):
        """Update case status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE cases SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, case_id))
        conn.commit()
        conn.close()
    
    def add_case_note(self, case_id, officer_id, note):
        """Add note to case"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO case_notes (case_id, officer_id, note)
            VALUES (?, ?, ?)
        ''', (case_id, officer_id, note))
        conn.commit()
        conn.close()
    
    def get_case_notes(self, case_id):
        """Get all notes for a case"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT cn.*, o.name as officer_name FROM case_notes cn
            LEFT JOIN officers o ON cn.officer_id = o.id
            WHERE cn.case_id = ?
            ORDER BY cn.created_at DESC
        ''', (case_id,))
        notes = cursor.fetchall()
        conn.close()
        return notes
    
    def add_officer(self, badge_number, name, rank, department, password):
        """Add new officer"""
        conn = self.get_connection()
        cursor = conn.cursor()
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        try:
            cursor.execute('''
                INSERT INTO officers (badge_number, name, rank, department, password_hash)
                VALUES (?, ?, ?, ?, ?)
            ''', (badge_number, name, rank, department, password_hash))
            conn.commit()
            officer_id = cursor.lastrowid
            conn.close()
            return officer_id
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    def get_audit_log(self, limit=100):
        """Get audit log entries"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT al.*, o.name as officer_name, o.badge_number 
            FROM audit_log al
            LEFT JOIN officers o ON al.officer_id = o.id
            ORDER BY al.timestamp DESC
            LIMIT ?
        ''', (limit,))
        logs = cursor.fetchall()
        conn.close()
        return logs
    
    def search_cases(self, query):
        """Search cases by phone number, IMEI, or victim name"""
        conn = self.get_connection()
        cursor = conn.cursor()
        search_term = f"%{query}%"
        cursor.execute('''
            SELECT c.*, o.name as officer_name FROM cases c
            LEFT JOIN officers o ON c.assigned_officer_id = o.id
            WHERE c.phone_number LIKE ? OR c.imei LIKE ? 
            OR c.victim_name LIKE ? OR c.case_number LIKE ?
            ORDER BY c.created_at DESC
        ''', (search_term, search_term, search_term, search_term))
        cases = cursor.fetchall()
        conn.close()
        return cases
    
    def delete_case(self, case_id):
        """Delete a case and its related notes"""
        conn = self.get_connection()
        cursor = conn.cursor()
        # Delete case notes first
        cursor.execute('DELETE FROM case_notes WHERE case_id = ?', (case_id,))
        # Delete the case
        cursor.execute('DELETE FROM cases WHERE id = ?', (case_id,))
        conn.commit()
        conn.close()


class LoginWindow:
    """Officer Login Window"""
    
    def __init__(self, db, on_success):
        self.db = db
        self.on_success = on_success
        
        self.window = Tk()
        self.window.title("Police Phone Tracker - Login")
        self.window.geometry("450x450")
        self.window.configure(bg="#1a1a2e")
        self.window.resizable(True, True)
        self.window.minsize(400, 400)
        
        # Center window
        self.window.eval('tk::PlaceWindow . center')
        
        self.build_ui()
    
    def build_ui(self):
        # Logo/Title
        Label(
            self.window,
            text="POLICE PHONE TRACKER",
            fg="#00d4ff",
            font=("Consolas", 18, "bold"),
            bg="#1a1a2e",
        ).pack(pady=30)
        
        Label(
            self.window,
            text="Authorized Personnel Only",
            fg="#ff4444",
            font=("Consolas", 10),
            bg="#1a1a2e",
        ).pack()
        
        # Login form
        form_frame = Frame(self.window, bg="#1a1a2e")
        form_frame.pack(pady=20)
        
        Label(
            form_frame,
            text="Badge Number:",
            fg="#a8d8ea",
            font=("Consolas", 11),
            bg="#1a1a2e",
        ).pack(anchor="w")
        
        self.badge_entry = Entry(
            form_frame,
            width=25,
            font=("Consolas", 12),
            bg="#2d2d5a",
            fg="white",
            insertbackground="white",
            relief="flat",
        )
        self.badge_entry.pack(pady=5, ipady=5)
        
        Label(
            form_frame,
            text="Password:",
            fg="#a8d8ea",
            font=("Consolas", 11),
            bg="#1a1a2e",
        ).pack(anchor="w", pady=(10, 0))
        
        self.password_entry = Entry(
            form_frame,
            width=25,
            font=("Consolas", 12),
            bg="#2d2d5a",
            fg="white",
            insertbackground="white",
            relief="flat",
            show="*",
        )
        self.password_entry.pack(pady=5, ipady=5)
        self.password_entry.bind("<Return>", lambda e: self.login())
        
        Button(
            self.window,
            text="LOGIN",
            bg="#00d4ff",
            fg="black",
            font=("Consolas", 12, "bold"),
            relief="flat",
            padx=40,
            pady=8,
            cursor="hand2",
            command=self.login,
        ).pack(pady=20)
        
        Label(
            self.window,
            text="Default: ADMIN001 / admin123",
            fg="#666",
            font=("Consolas", 8),
            bg="#1a1a2e",
        ).pack()
    
    def login(self):
        badge = self.badge_entry.get().strip()
        password = self.password_entry.get()
        
        if not badge or not password:
            messagebox.showwarning("Warning", "Please enter badge number and password!")
            return
        
        officer = self.db.verify_officer(badge, password)
        if officer:
            self.db.log_action(officer[0], "LOGIN", f"Officer logged in: {officer[1]}")
            self.window.destroy()
            self.on_success(officer)
        else:
            messagebox.showerror("Error", "Invalid credentials!")
            self.db.log_action(None, "FAILED_LOGIN", f"Failed login attempt: {badge}")
    
    def run(self):
        self.window.mainloop()


class PoliceTrackerApp:
    """Main Police Tracker Application"""
    
    COUNTRY_COORDS = {
        "Tanzania": (-6.369028, 34.888822),
        "Kenya": (-1.286389, 36.817223),
        "Uganda": (0.347596, 32.582520),
        "Nigeria": (9.081999, 8.675277),
        "South Africa": (-30.559482, 22.937506),
        "United States": (37.090240, -95.712891),
        "United Kingdom": (55.378051, -3.435973),
        "India": (20.593684, 78.962880),
        "Germany": (51.165691, 10.451526),
        "France": (46.227638, 2.213749),
        "Canada": (56.130366, -106.346771),
        "Australia": (-25.274398, 133.775136),
        "Brazil": (-14.235004, -51.925280),
        "Japan": (36.204824, 138.252924),
    }
    
    def __init__(self, officer_data, db):
        self.officer_id = officer_data[0]
        self.officer_name = officer_data[1]
        self.officer_rank = officer_data[2]
        self.officer_dept = officer_data[3]
        self.db = db
        
        self.window = Tk()
        self.window.title(f"Police Phone Tracker - {self.officer_name}")
        self.window.geometry("1000x700")
        self.window.configure(bg="#0f0f23")
        self.window.resizable(True, True)
        
        self.current_phone_data = {}
        
        self.build_ui()
        self.db.log_action(self.officer_id, "APP_OPENED", "Main application opened")
    
    def build_ui(self):
        # Header
        header = Frame(self.window, bg="#1a1a3e", pady=10)
        header.pack(fill="x")
        
        Label(
            header,
            text="POLICE PHONE TRACKER SYSTEM",
            fg="#00d4ff",
            font=("Consolas", 20, "bold"),
            bg="#1a1a3e",
        ).pack(side="left", padx=20)
        
        officer_info = Frame(header, bg="#1a1a3e")
        officer_info.pack(side="right", padx=20)
        
        Label(
            officer_info,
            text=f"Officer: {self.officer_name}",
            fg="#00ff88",
            font=("Consolas", 10),
            bg="#1a1a3e",
        ).pack(anchor="e")
        
        Label(
            officer_info,
            text=f"{self.officer_rank} - {self.officer_dept}",
            fg="#888",
            font=("Consolas", 9),
            bg="#1a1a3e",
        ).pack(anchor="e")
        
        # Navigation buttons
        nav_frame = Frame(self.window, bg="#0f0f23")
        nav_frame.pack(fill="x", pady=10, padx=20)
        
        nav_buttons = [
            ("New Case", "#4ecca3", self.show_new_case),
            ("View Cases", "#00d4ff", self.show_cases),
            ("Search", "#f39c12", self.show_search),
            ("Audit Log", "#9b59b6", self.show_audit_log),
            ("Add Officer", "#3498db", self.show_add_officer),
            ("Logout", "#e74c3c", self.logout),
        ]
        
        for text, color, cmd in nav_buttons:
            Button(
                nav_frame,
                text=text,
                bg=color,
                fg="white" if color not in ["#f39c12"] else "black",
                font=("Consolas", 10, "bold"),
                relief="flat",
                padx=15,
                pady=5,
                cursor="hand2",
                command=cmd,
            ).pack(side="left", padx=5)
        
        # Main content area
        self.content_frame = Frame(self.window, bg="#0f0f23")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Show dashboard by default
        self.show_dashboard()
    
    def clear_content(self):
        """Clear content frame"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_dashboard(self):
        """Show dashboard with stats"""
        self.clear_content()
        
        Label(
            self.content_frame,
            text="DASHBOARD",
            fg="#00d4ff",
            font=("Consolas", 16, "bold"),
            bg="#0f0f23",
        ).pack(anchor="w", pady=10)
        
        # Stats
        cases = self.db.get_all_cases()
        open_cases = len([c for c in cases if c[10] == "Open"])
        closed_cases = len([c for c in cases if c[10] == "Closed"])
        
        stats_frame = Frame(self.content_frame, bg="#0f0f23")
        stats_frame.pack(fill="x", pady=20)
        
        stats = [
            ("Total Cases", len(cases), "#00d4ff"),
            ("Open Cases", open_cases, "#f39c12"),
            ("Closed Cases", closed_cases, "#4ecca3"),
        ]
        
        for label, value, color in stats:
            stat_box = Frame(stats_frame, bg="#1a1a3e", padx=30, pady=20)
            stat_box.pack(side="left", padx=10)
            
            Label(
                stat_box,
                text=str(value),
                fg=color,
                font=("Consolas", 36, "bold"),
                bg="#1a1a3e",
            ).pack()
            
            Label(
                stat_box,
                text=label,
                fg="#888",
                font=("Consolas", 11),
                bg="#1a1a3e",
            ).pack()
    
    def show_new_case(self):
        """Show new case form"""
        self.clear_content()
        
        Label(
            self.content_frame,
            text="CREATE NEW CASE",
            fg="#00d4ff",
            font=("Consolas", 16, "bold"),
            bg="#0f0f23",
        ).pack(anchor="w", pady=10)
        
        # Form container
        form_container = Frame(self.content_frame, bg="#1a1a3e", padx=30, pady=20)
        form_container.pack(fill="both", expand=True)
        
        # Left column - Phone tracking
        left_col = Frame(form_container, bg="#1a1a3e")
        left_col.pack(side="left", fill="both", expand=True, padx=10)
        
        Label(
            left_col,
            text="Phone Number Analysis",
            fg="#00d4ff",
            font=("Consolas", 12, "bold"),
            bg="#1a1a3e",
        ).pack(anchor="w")
        
        # Phone entry
        phone_frame = Frame(left_col, bg="#1a1a3e")
        phone_frame.pack(fill="x", pady=10)
        
        Label(phone_frame, text="Phone Number*:", fg="#a8d8ea", bg="#1a1a3e", font=("Consolas", 10)).pack(anchor="w")
        self.phone_entry = Entry(phone_frame, width=30, font=("Consolas", 12), bg="#2d2d5a", fg="white", insertbackground="white", relief="flat")
        self.phone_entry.pack(fill="x", pady=2, ipady=5)
        
        Button(
            left_col,
            text="Analyze Number",
            bg="#00d4ff",
            fg="black",
            font=("Consolas", 10, "bold"),
            relief="flat",
            command=self.analyze_phone,
        ).pack(anchor="w", pady=10)
        
        # Analysis results
        self.analysis_frame = Frame(left_col, bg="#1a1a3e")
        self.analysis_frame.pack(fill="x", pady=10)
        
        self.analysis_vars = {
            "country": StringVar(value="-"),
            "carrier": StringVar(value="-"),
            "type": StringVar(value="-"),
            "timezone": StringVar(value="-"),
            "valid": StringVar(value="-"),
        }
        
        for label, var in [("Country:", "country"), ("Carrier:", "carrier"), 
                           ("Type:", "type"), ("Timezone:", "timezone"), ("Valid:", "valid")]:
            row = Frame(self.analysis_frame, bg="#1a1a3e")
            row.pack(fill="x")
            Label(row, text=label, fg="#888", bg="#1a1a3e", font=("Consolas", 9), width=12, anchor="w").pack(side="left")
            Label(row, textvariable=self.analysis_vars[var], fg="#00ff88", bg="#1a1a3e", font=("Consolas", 9, "bold")).pack(side="left")
        
        # IMEI entry
        Label(left_col, text="IMEI (if available):", fg="#a8d8ea", bg="#1a1a3e", font=("Consolas", 10)).pack(anchor="w", pady=(10, 0))
        self.imei_entry = Entry(left_col, width=30, font=("Consolas", 12), bg="#2d2d5a", fg="white", insertbackground="white", relief="flat")
        self.imei_entry.pack(fill="x", pady=2, ipady=5)
        
        # Right column - Victim info
        right_col = Frame(form_container, bg="#1a1a3e")
        right_col.pack(side="right", fill="both", expand=True, padx=10)
        
        Label(
            right_col,
            text="Victim Information",
            fg="#00d4ff",
            font=("Consolas", 12, "bold"),
            bg="#1a1a3e",
        ).pack(anchor="w")
        
        fields = [
            ("Victim Name*:", "victim_name"),
            ("Contact Number:", "victim_contact"),
            ("Address:", "victim_address"),
            ("Incident Date:", "incident_date"),
            ("Incident Location:", "incident_location"),
        ]
        
        self.case_entries = {}
        for label, key in fields:
            Label(right_col, text=label, fg="#a8d8ea", bg="#1a1a3e", font=("Consolas", 10)).pack(anchor="w", pady=(5, 0))
            entry = Entry(right_col, width=30, font=("Consolas", 11), bg="#2d2d5a", fg="white", insertbackground="white", relief="flat")
            entry.pack(fill="x", pady=2, ipady=3)
            self.case_entries[key] = entry
        
        Label(right_col, text="Description:", fg="#a8d8ea", bg="#1a1a3e", font=("Consolas", 10)).pack(anchor="w", pady=(5, 0))
        self.description_text = Text(right_col, height=4, font=("Consolas", 10), bg="#2d2d5a", fg="white", insertbackground="white", relief="flat")
        self.description_text.pack(fill="x", pady=2)
        
        # Buttons
        btn_frame = Frame(form_container, bg="#1a1a3e")
        btn_frame.pack(side="bottom", fill="x", pady=20)
        
        Button(
            btn_frame,
            text="Create Case",
            bg="#4ecca3",
            fg="white",
            font=("Consolas", 12, "bold"),
            relief="flat",
            padx=30,
            command=self.create_case,
        ).pack(side="left", padx=5)
        
        Button(
            btn_frame,
            text="Show on Map",
            bg="#fc5185",
            fg="white",
            font=("Consolas", 12, "bold"),
            relief="flat",
            padx=30,
            command=self.show_map,
        ).pack(side="left", padx=5)
    
    def analyze_phone(self):
        """Analyze phone number"""
        phone_input = self.phone_entry.get().strip()
        
        if not phone_input:
            messagebox.showwarning("Warning", "Enter a phone number!")
            return
        
        if not phone_input.startswith("+"):
            phone_input = "+" + phone_input
        
        try:
            parsed = phonenumbers.parse(phone_input)
            is_valid = phonenumbers.is_valid_number(parsed)
            
            country = geocoder.description_for_number(parsed, "en")
            carrier_name = carrier.name_for_number(parsed, "en")
            tz = timezone.time_zones_for_number(parsed)
            
            # Get number type
            num_type = phonenumbers.number_type(parsed)
            types = {
                phonenumbers.PhoneNumberType.MOBILE: "Mobile",
                phonenumbers.PhoneNumberType.FIXED_LINE: "Fixed Line",
                phonenumbers.PhoneNumberType.VOIP: "VoIP",
            }
            type_str = types.get(num_type, "Unknown")
            
            self.analysis_vars["country"].set(country or "Unknown")
            self.analysis_vars["carrier"].set(carrier_name or "Unknown")
            self.analysis_vars["type"].set(type_str)
            self.analysis_vars["timezone"].set(", ".join(tz) if tz else "Unknown")
            self.analysis_vars["valid"].set("Yes" if is_valid else "No")
            
            self.current_phone_data = {
                "country": country,
                "carrier": carrier_name,
                "type": type_str,
                "timezone": ", ".join(tz) if tz else "",
                "valid": is_valid,
                "international": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
            }
            
            self.db.log_action(self.officer_id, "PHONE_ANALYZED", f"Analyzed: {phone_input}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Invalid phone number!\n{str(e)}")
    
    def create_case(self):
        """Create new case"""
        phone = self.phone_entry.get().strip()
        victim_name = self.case_entries["victim_name"].get().strip()
        
        if not phone or not victim_name:
            messagebox.showwarning("Warning", "Phone number and victim name are required!")
            return
        
        # Generate case number
        case_number = f"CASE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        case_data = {
            "case_number": case_number,
            "phone_number": phone,
            "imei": self.imei_entry.get().strip(),
            "victim_name": victim_name,
            "victim_contact": self.case_entries["victim_contact"].get().strip(),
            "victim_address": self.case_entries["victim_address"].get().strip(),
            "incident_date": self.case_entries["incident_date"].get().strip(),
            "incident_location": self.case_entries["incident_location"].get().strip(),
            "description": self.description_text.get("1.0", END).strip(),
            "officer_id": self.officer_id,
            "country": self.current_phone_data.get("country"),
            "carrier": self.current_phone_data.get("carrier"),
            "phone_type": self.current_phone_data.get("type"),
            "timezone": self.current_phone_data.get("timezone"),
        }
        
        case_id = self.db.create_case(case_data)
        self.db.log_action(self.officer_id, "CASE_CREATED", f"Created case: {case_number}")
        
        messagebox.showinfo("Success", f"Case created successfully!\nCase Number: {case_number}")
        self.show_cases()
    
    def show_cases(self):
        """Show all cases"""
        self.clear_content()
        
        Label(
            self.content_frame,
            text="ALL CASES",
            fg="#00d4ff",
            font=("Consolas", 16, "bold"),
            bg="#0f0f23",
        ).pack(anchor="w", pady=10)
        
        # Create treeview
        columns = ("Case #", "Phone", "Victim", "Status", "Country", "Carrier", "Date")
        tree_frame = Frame(self.content_frame, bg="#0f0f23")
        tree_frame.pack(fill="both", expand=True)
        
        scrollbar = Scrollbar(tree_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.case_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.case_tree.yview)
        
        for col in columns:
            self.case_tree.heading(col, text=col)
            self.case_tree.column(col, width=100)
        
        self.case_tree.pack(fill="both", expand=True)
        
        # Load cases
        cases = self.db.get_all_cases()
        for case in cases:
            self.case_tree.insert("", END, values=(
                case[1],  # case_number
                case[2],  # phone_number
                case[4],  # victim_name
                case[10], # status
                case[12], # country
                case[13], # carrier
                case[19], # created_at
            ), tags=(str(case[0]),))
        
        # Buttons
        btn_frame = Frame(self.content_frame, bg="#0f0f23")
        btn_frame.pack(fill="x", pady=10)
        
        Button(btn_frame, text="View Details", bg="#00d4ff", fg="black", font=("Consolas", 10, "bold"),
               relief="flat", command=self.view_case_details).pack(side="left", padx=5)
        Button(btn_frame, text="Update Status", bg="#f39c12", fg="black", font=("Consolas", 10, "bold"),
               relief="flat", command=self.update_case_status).pack(side="left", padx=5)
        Button(btn_frame, text="Generate Report", bg="#4ecca3", fg="white", font=("Consolas", 10, "bold"),
               relief="flat", command=self.generate_report).pack(side="left", padx=5)
        Button(btn_frame, text="Carrier Request", bg="#9b59b6", fg="white", font=("Consolas", 10, "bold"),
               relief="flat", command=self.generate_carrier_request).pack(side="left", padx=5)
        Button(btn_frame, text="Delete Case", bg="#e74c3c", fg="white", font=("Consolas", 10, "bold"),
               relief="flat", command=self.delete_case).pack(side="left", padx=5)
    
    def view_case_details(self):
        """View selected case details"""
        selected = self.case_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a case first!")
            return
        
        case_id = int(self.case_tree.item(selected[0])["tags"][0])
        case = self.db.get_case(case_id)
        
        # Create details window
        details_win = Toplevel(self.window)
        details_win.title(f"Case Details - {case[1]}")
        details_win.geometry("600x500")
        details_win.configure(bg="#1a1a3e")
        
        text = Text(details_win, bg="#0f0f23", fg="#00ff88", font=("Consolas", 10), wrap="word")
        text.pack(fill="both", expand=True, padx=20, pady=20)
        
        details = f"""
CASE DETAILS
{'='*50}

Case Number:      {case[1]}
Status:           {case[10]}
Created:          {case[19]}

PHONE INFORMATION
{'-'*50}
Phone Number:     {case[2]}
IMEI:             {case[3] or 'N/A'}
Country:          {case[12] or 'N/A'}
Carrier:          {case[13] or 'N/A'}
Phone Type:       {case[14] or 'N/A'}
Timezone:         {case[15] or 'N/A'}

VICTIM INFORMATION
{'-'*50}
Name:             {case[4]}
Contact:          {case[5] or 'N/A'}
Address:          {case[6] or 'N/A'}

INCIDENT DETAILS
{'-'*50}
Date:             {case[7] or 'N/A'}
Location:         {case[8] or 'N/A'}
Description:      {case[9] or 'N/A'}

ASSIGNED OFFICER
{'-'*50}
Officer:          {case[21] if len(case) > 21 else 'N/A'}
"""
        text.insert(END, details)
        text.config(state="disabled")
        
        self.db.log_action(self.officer_id, "CASE_VIEWED", f"Viewed case: {case[1]}")
    
    def update_case_status(self):
        """Update case status"""
        selected = self.case_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a case first!")
            return
        
        case_id = int(self.case_tree.item(selected[0])["tags"][0])
        
        status_win = Toplevel(self.window)
        status_win.title("Update Status")
        status_win.geometry("300x150")
        status_win.configure(bg="#1a1a3e")
        
        Label(status_win, text="Select New Status:", fg="#a8d8ea", bg="#1a1a3e", font=("Consolas", 11)).pack(pady=10)
        
        status_var = StringVar(value="Open")
        statuses = ["Open", "In Progress", "Pending Carrier Response", "Closed", "Resolved"]
        
        for status in statuses:
            ttk.Radiobutton(status_win, text=status, variable=status_var, value=status).pack(anchor="w", padx=50)
        
        def update():
            self.db.update_case_status(case_id, status_var.get())
            self.db.log_action(self.officer_id, "STATUS_UPDATED", f"Case {case_id} -> {status_var.get()}")
            messagebox.showinfo("Success", "Status updated!")
            status_win.destroy()
            self.show_cases()
        
        Button(status_win, text="Update", bg="#4ecca3", fg="white", command=update).pack(pady=10)
    
    def generate_report(self):
        """Generate case report"""
        selected = self.case_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a case first!")
            return
        
        case_id = int(self.case_tree.item(selected[0])["tags"][0])
        case = self.db.get_case(case_id)
        
        report = f"""
================================================================================
                    OFFICIAL POLICE CASE REPORT
                    LOST/STOLEN PHONE INVESTIGATION
================================================================================

REPORT GENERATED: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
GENERATED BY: {self.officer_name} ({self.officer_rank})
DEPARTMENT: {self.officer_dept}

================================================================================
                         CASE INFORMATION
================================================================================

Case Number:          {case[1]}
Status:               {case[10]}
Date Created:         {case[19]}
Last Updated:         {case[20]}

================================================================================
                       PHONE DETAILS
================================================================================

Phone Number:         {case[2]}
IMEI Number:          {case[3] or 'Not Provided'}
Country/Region:       {case[12] or 'Unknown'}
Service Provider:     {case[13] or 'Unknown'}
Phone Type:           {case[14] or 'Unknown'}
Timezone:             {case[15] or 'Unknown'}
Last Known Location:  {case[16] or 'Not Available'}

================================================================================
                     VICTIM INFORMATION
================================================================================

Full Name:            {case[4]}
Contact Number:       {case[5] or 'Not Provided'}
Address:              {case[6] or 'Not Provided'}

================================================================================
                     INCIDENT DETAILS
================================================================================

Incident Date:        {case[7] or 'Not Specified'}
Incident Location:    {case[8] or 'Not Specified'}

Description:
{case[9] or 'No description provided.'}

================================================================================
                     INVESTIGATION NOTES
================================================================================

Carrier Response:     {case[17] or 'Awaiting response'}

================================================================================
                        DISCLAIMER
================================================================================

This report is for official law enforcement use only. The information
contained herein is based on publicly available data and victim statements.
Real-time location tracking requires proper legal authorization and
cooperation from service providers.

================================================================================
                     OFFICER SIGNATURE
================================================================================

Officer Name: _________________________

Badge Number: _________________________

Date: _________________________

Signature: _________________________

================================================================================
                       END OF REPORT
================================================================================
"""
        
        file_path = asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile=f"Report_{case[1]}.txt"
        )
        
        if file_path:
            with open(file_path, "w") as f:
                f.write(report)
            messagebox.showinfo("Success", f"Report saved to:\n{file_path}")
            self.db.log_action(self.officer_id, "REPORT_GENERATED", f"Generated report for case: {case[1]}")
    
    def generate_carrier_request(self):
        """Generate carrier request letter"""
        selected = self.case_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a case first!")
            return
        
        case_id = int(self.case_tree.item(selected[0])["tags"][0])
        case = self.db.get_case(case_id)
        
        letter = f"""
================================================================================
              OFFICIAL REQUEST FOR SUBSCRIBER INFORMATION
                    LAW ENFORCEMENT AGENCY
================================================================================

Date: {datetime.now().strftime("%Y-%m-%d")}

To: Legal/Law Enforcement Compliance Department
    {case[13] or '[CARRIER NAME]'}

RE: Request for Subscriber Information and Location Data
    Case Reference: {case[1]}

--------------------------------------------------------------------------------

Dear Sir/Madam,

This letter serves as an official request for subscriber information and
location data in connection with an ongoing criminal investigation.

INVESTIGATION DETAILS:
----------------------
Case Number:        {case[1]}
Investigating Dept: {self.officer_dept}
Lead Officer:       {self.officer_name}
Badge Number:       [BADGE NUMBER]

PHONE INFORMATION:
------------------
Phone Number:       {case[2]}
IMEI Number:        {case[3] or 'Unknown - Please provide if available'}

INFORMATION REQUESTED:
----------------------
1. Subscriber name and address registered to this number
2. Account activation date
3. Call Detail Records (CDR) for the past 30 days
4. SMS records for the past 30 days
5. Cell tower location data for the past 7 days
6. Last known location/cell tower connection
7. Current account status (active/inactive)
8. IMEI change history

LEGAL BASIS:
------------
This request is made pursuant to [APPLICABLE LAW/COURT ORDER NUMBER].
[Attach court order/warrant if required]

INCIDENT SUMMARY:
-----------------
{case[9] or 'A phone registered to the above number was reported lost/stolen.'}

Incident Date: {case[7] or 'See attached complaint'}
Incident Location: {case[8] or 'See attached complaint'}

URGENCY:
--------
This matter is considered [HIGH/MEDIUM] priority due to the nature of
the investigation. Your prompt attention is appreciated.

Please direct all responses to:

Officer: {self.officer_name}
Department: {self.officer_dept}
Phone: [DEPARTMENT PHONE]
Email: [OFFICIAL EMAIL]

Thank you for your cooperation in this matter.

Respectfully,


_______________________________
{self.officer_name}
{self.officer_rank}
{self.officer_dept}

================================================================================
                    END OF REQUEST
================================================================================
"""
        
        file_path = asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile=f"Carrier_Request_{case[1]}.txt"
        )
        
        if file_path:
            with open(file_path, "w") as f:
                f.write(letter)
            messagebox.showinfo("Success", f"Carrier request saved to:\n{file_path}")
            self.db.log_action(self.officer_id, "CARRIER_REQUEST", f"Generated carrier request for case: {case[1]}")
    
    def show_search(self):
        """Show search interface"""
        self.clear_content()
        
        Label(
            self.content_frame,
            text="SEARCH CASES",
            fg="#00d4ff",
            font=("Consolas", 16, "bold"),
            bg="#0f0f23",
        ).pack(anchor="w", pady=10)
        
        search_frame = Frame(self.content_frame, bg="#0f0f23")
        search_frame.pack(fill="x", pady=10)
        
        self.search_entry = Entry(search_frame, width=40, font=("Consolas", 12), bg="#2d2d5a", fg="white", insertbackground="white", relief="flat")
        self.search_entry.pack(side="left", ipady=5, padx=(0, 10))
        self.search_entry.bind("<Return>", lambda e: self.perform_search())
        
        Button(search_frame, text="Search", bg="#f39c12", fg="black", font=("Consolas", 10, "bold"),
               relief="flat", command=self.perform_search).pack(side="left")
        
        Label(self.content_frame, text="Search by phone number, IMEI, victim name, or case number",
              fg="#666", bg="#0f0f23", font=("Consolas", 9)).pack(anchor="w")
        
        self.search_results = Frame(self.content_frame, bg="#0f0f23")
        self.search_results.pack(fill="both", expand=True, pady=20)
    
    def perform_search(self):
        """Perform case search"""
        query = self.search_entry.get().strip()
        if not query:
            return
        
        for widget in self.search_results.winfo_children():
            widget.destroy()
        
        cases = self.db.search_cases(query)
        self.db.log_action(self.officer_id, "SEARCH", f"Searched for: {query}")
        
        if not cases:
            Label(self.search_results, text="No results found.", fg="#ff4444", bg="#0f0f23", font=("Consolas", 12)).pack()
            return
        
        Label(self.search_results, text=f"Found {len(cases)} result(s):", fg="#00ff88", bg="#0f0f23", font=("Consolas", 11)).pack(anchor="w")
        
        for case in cases:
            case_frame = Frame(self.search_results, bg="#1a1a3e", padx=15, pady=10)
            case_frame.pack(fill="x", pady=5)
            
            Label(case_frame, text=f"Case: {case[1]} | Phone: {case[2]} | Victim: {case[4]} | Status: {case[10]}",
                  fg="#00d4ff", bg="#1a1a3e", font=("Consolas", 10)).pack(anchor="w")
    
    def show_audit_log(self):
        """Show audit log"""
        self.clear_content()
        
        Label(
            self.content_frame,
            text="AUDIT LOG",
            fg="#00d4ff",
            font=("Consolas", 16, "bold"),
            bg="#0f0f23",
        ).pack(anchor="w", pady=10)
        
        text_frame = Frame(self.content_frame, bg="#0f0f23")
        text_frame.pack(fill="both", expand=True)
        
        scrollbar = Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        
        text = Text(text_frame, bg="#0f0f23", fg="#00ff88", font=("Consolas", 9), yscrollcommand=scrollbar.set)
        text.pack(fill="both", expand=True)
        scrollbar.config(command=text.yview)
        
        logs = self.db.get_audit_log()
        for log in logs:
            officer_info = f"{log[6]} ({log[7]})" if log[6] else "System"
            text.insert(END, f"[{log[5]}] {officer_info}: {log[2]} - {log[3]}\n")
        
        text.config(state="disabled")
    
    def show_add_officer(self):
        """Show add officer form"""
        self.clear_content()
        
        Label(
            self.content_frame,
            text="ADD NEW OFFICER",
            fg="#00d4ff",
            font=("Consolas", 16, "bold"),
            bg="#0f0f23",
        ).pack(anchor="w", pady=10)
        
        form_frame = Frame(self.content_frame, bg="#1a1a3e", padx=30, pady=20)
        form_frame.pack(fill="x")
        
        fields = [
            ("Badge Number:", "badge"),
            ("Full Name:", "name"),
            ("Rank:", "rank"),
            ("Department:", "dept"),
            ("Password:", "password"),
        ]
        
        self.officer_entries = {}
        for label, key in fields:
            Label(form_frame, text=label, fg="#a8d8ea", bg="#1a1a3e", font=("Consolas", 10)).pack(anchor="w", pady=(5, 0))
            entry = Entry(form_frame, width=30, font=("Consolas", 11), bg="#2d2d5a", fg="white", insertbackground="white", relief="flat")
            if key == "password":
                entry.config(show="*")
            entry.pack(fill="x", pady=2, ipady=3)
            self.officer_entries[key] = entry
        
        Button(form_frame, text="Add Officer", bg="#4ecca3", fg="white", font=("Consolas", 11, "bold"),
               relief="flat", command=self.add_officer).pack(pady=20)
    
    def add_officer(self):
        """Add new officer"""
        badge = self.officer_entries["badge"].get().strip()
        name = self.officer_entries["name"].get().strip()
        rank = self.officer_entries["rank"].get().strip()
        dept = self.officer_entries["dept"].get().strip()
        password = self.officer_entries["password"].get()
        
        if not all([badge, name, password]):
            messagebox.showwarning("Warning", "Badge number, name, and password are required!")
            return
        
        result = self.db.add_officer(badge, name, rank, dept, password)
        if result:
            self.db.log_action(self.officer_id, "OFFICER_ADDED", f"Added officer: {badge}")
            messagebox.showinfo("Success", f"Officer {name} added successfully!")
            self.show_dashboard()
        else:
            messagebox.showerror("Error", "Badge number already exists!")
    
    def delete_case(self):
        """Delete selected case"""
        selected = self.case_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a case first!")
            return
        
        case_id = int(self.case_tree.item(selected[0])["tags"][0])
        case_number = self.case_tree.item(selected[0])["values"][0]
        
        # Confirm deletion
        confirm = messagebox.askyesno(
            "Confirm Delete", 
            f"Are you sure you want to delete case {case_number}?\n\nThis action cannot be undone!"
        )
        
        if confirm:
            self.db.delete_case(case_id)
            self.db.log_action(self.officer_id, "CASE_DELETED", f"Deleted case: {case_number}")
            messagebox.showinfo("Success", f"Case {case_number} deleted successfully!")
            self.show_cases()
    
    def show_map(self):
        """Show location on map"""
        if not self.current_phone_data.get("country"):
            messagebox.showwarning("Warning", "Analyze a phone number first!")
            return
        
        country = self.current_phone_data["country"]
        coords = self.COUNTRY_COORDS.get(country, (20, 0))
        zoom = 5 if country in self.COUNTRY_COORDS else 2
        
        map_obj = folium.Map(location=coords, zoom_start=zoom, tiles="CartoDB dark_matter")
        
        folium.Marker(
            location=coords,
            popup=f"{country}<br>Carrier: {self.current_phone_data.get('carrier', 'Unknown')}",
            icon=folium.Icon(color="red", icon="phone", prefix="fa"),
        ).add_to(map_obj)
        
        folium.Circle(location=coords, radius=150000, color="#00d4ff", fill=True, fill_opacity=0.15).add_to(map_obj)
        
        map_path = os.path.join(os.path.dirname(__file__), "case_location_map.html")
        map_obj.save(map_path)
        webbrowser.open("file://" + os.path.abspath(map_path))
    
    def logout(self):
        """Logout and return to login"""
        self.db.log_action(self.officer_id, "LOGOUT", "Officer logged out")
        self.window.destroy()
        start_app()
    
    def run(self):
        self.window.mainloop()


def start_app():
    """Start the application"""
    db = Database()
    
    def on_login_success(officer_data):
        app = PoliceTrackerApp(officer_data, db)
        app.run()
    
    login = LoginWindow(db, on_login_success)
    login.run()


if __name__ == "__main__":
    start_app()
