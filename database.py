import sqlite3
import os
from datetime import datetime
import hashlib
from persiantools.jdatetime import JalaliDateTime

class Database:
    def __init__(self):
        self.db_path = "attendance.db"
        self.conn = None
        
    def connect(self):
        """Create database connection"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def init_db(self):
        """Initialize database tables"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Create workers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                personal_number TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create attendance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_id INTEGER NOT NULL,
                entry_time TIMESTAMP,
                exit_time TIMESTAMP,
                date TEXT NOT NULL,
                jalali_date TEXT NOT NULL,
                total_hours REAL DEFAULT 0,
                FOREIGN KEY (worker_id) REFERENCES workers (id)
            )
        ''')
        
        # Create admin table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        
        # Create default admin if not exists
        cursor.execute("SELECT COUNT(*) FROM admin")
        if cursor.fetchone()[0] == 0:
            self.create_admin("admin", "admin123")
        
        conn.commit()
        conn.close()
    
    def create_admin(self, username, password):
        """Create admin user"""
        conn = self.connect()
        cursor = conn.cursor()
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute("INSERT INTO admin (username, password_hash) VALUES (?, ?)",
                      (username, password_hash))
        conn.commit()
        conn.close()
    
    def verify_admin(self, username, password):
        """Verify admin credentials"""
        conn = self.connect()
        cursor = conn.cursor()
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute("SELECT * FROM admin WHERE username = ? AND password_hash = ?",
                      (username, password_hash))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def add_worker(self, personal_number, full_name, phone=""):
        """Add new worker"""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO workers (personal_number, full_name, phone) VALUES (?, ?, ?)",
                          (personal_number, full_name, phone))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def get_worker_by_personal_number(self, personal_number):
        """Get worker by personal number"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM workers WHERE personal_number = ?", (personal_number,))
        result = cursor.fetchone()
        conn.close()
        return result
    
    def get_all_workers(self):
        """Get all workers"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM workers ORDER BY full_name")
        results = cursor.fetchall()
        conn.close()
        return results
    
    def record_entry(self, worker_id):
        """Record worker entry time"""
        conn = self.connect()
        cursor = conn.cursor()
        now = datetime.now()
        jalali_now = JalaliDateTime.now()
        date_str = now.strftime('%Y-%m-%d')
        jalali_date_str = jalali_now.strftime('%Y/%m/%d')
        
        # Check if already has entry today
        cursor.execute("SELECT * FROM attendance WHERE worker_id = ? AND date = ? AND exit_time IS NULL",
                      (worker_id, date_str))
        if cursor.fetchone():
            conn.close()
            return False, "شما قبلاً ورود خود را ثبت کرده‌اید"
        
        cursor.execute("INSERT INTO attendance (worker_id, entry_time, date, jalali_date) VALUES (?, ?, ?, ?)",
                      (worker_id, now, date_str, jalali_date_str))
        conn.commit()
        conn.close()
        return True, "ورود با موفقیت ثبت شد"
    
    def record_exit(self, worker_id):
        """Record worker exit time"""
        conn = self.connect()
        cursor = conn.cursor()
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        
        # Find today's entry without exit
        cursor.execute("SELECT * FROM attendance WHERE worker_id = ? AND date = ? AND exit_time IS NULL",
                      (worker_id, date_str))
        record = cursor.fetchone()
        
        if not record:
            conn.close()
            return False, "ابتدا باید ورود خود را ثبت کنید"
        
        # Calculate total hours
        entry_time = datetime.fromisoformat(record['entry_time'])
        total_hours = (now - entry_time).total_seconds() / 3600
        
        cursor.execute("UPDATE attendance SET exit_time = ?, total_hours = ? WHERE id = ?",
                      (now, total_hours, record['id']))
        conn.commit()
        conn.close()
        return True, f"خروج با موفقیت ثبت شد. مدت حضور: {total_hours:.2f} ساعت"
    
    def get_worker_attendance(self, worker_id, start_date=None, end_date=None):
        """Get worker attendance records"""
        conn = self.connect()
        cursor = conn.cursor()
        
        if start_date and end_date:
            cursor.execute("""
                SELECT * FROM attendance 
                WHERE worker_id = ? AND date BETWEEN ? AND ?
                ORDER BY date DESC
            """, (worker_id, start_date, end_date))
        else:
            cursor.execute("""
                SELECT * FROM attendance 
                WHERE worker_id = ?
                ORDER BY date DESC
            """, (worker_id,))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_all_attendance(self, start_date=None, end_date=None):
        """Get all attendance records with worker info"""
        conn = self.connect()
        cursor = conn.cursor()
        
        query = """
            SELECT a.*, w.full_name, w.personal_number 
            FROM attendance a
            JOIN workers w ON a.worker_id = w.id
        """
        
        if start_date and end_date:
            query += " WHERE a.date BETWEEN ? AND ?"
            cursor.execute(query + " ORDER BY a.date DESC, w.full_name", (start_date, end_date))
        else:
            cursor.execute(query + " ORDER BY a.date DESC, w.full_name")
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def delete_worker(self, worker_id):
        """Delete worker and their attendance records"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM attendance WHERE worker_id = ?", (worker_id,))
        cursor.execute("DELETE FROM workers WHERE id = ?", (worker_id,))
        conn.commit()
        conn.close()
    
    def get_monthly_report(self, worker_id, year, month):
        """Get monthly report for a worker"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Create date range
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month + 1:02d}-01"
        
        cursor.execute("""
            SELECT COUNT(*) as days_worked, SUM(total_hours) as total_hours
            FROM attendance
            WHERE worker_id = ? AND date >= ? AND date < ?
        """, (worker_id, start_date, end_date))
        
        result = cursor.fetchone()
        conn.close()
        return result
    def update_attendance_time(self, attendance_id, column, new_time_str):
        """Update entry or exit time for an attendance record and recalculate total hours."""
        conn = self.connect()
        cursor = conn.cursor()

        try:
            cursor.execute(f"UPDATE attendance SET {column} = ? WHERE id = ?", (new_time_str, attendance_id))

            # After updating, fetch the record to recalculate total_hours
            cursor.execute("SELECT entry_time, exit_time FROM attendance WHERE id = ?", (attendance_id,))
            record = cursor.fetchone()

            if record and record['entry_time'] and record['exit_time']:
                entry_time = datetime.fromisoformat(record['entry_time'])
                exit_time = datetime.fromisoformat(record['exit_time'])
                if exit_time > entry_time:
                    total_hours = (exit_time - entry_time).total_seconds() / 3600
                else:
                    total_hours = 0  # Or handle as an error case
                cursor.execute("UPDATE attendance SET total_hours = ? WHERE id = ?", (total_hours, attendance_id))
            else:
                # If either entry or exit is NULL, total hours is 0
                cursor.execute("UPDATE attendance SET total_hours = 0 WHERE id = ?", (attendance_id,))

            conn.commit()
            return True, "زمان با موفقیت ویرایش شد."
        except Exception as e:
            conn.rollback()
            return False, f"خطا در ویرایش زمان: {e}"
        finally:
            conn.close()