import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
import mysql.connector
import json
import os
from datetime import datetime
import hashlib

# ------------------- Constants -------------------
SESSION_FILE = 'user_session.json'
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "new_password",
    "database": "library_system"
}

# ------------------- Database Connection -------------------
def connect_db():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        print(f"Failed to connect to database: {err}")
        return None

# ------------------- Session Management -------------------
def load_session():
    """Load user data from session file"""
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, 'r') as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"Failed to load session: {e}")
        return None

def clear_session():
    """Delete the session file"""
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

# ------------------- Fine Functions -------------------
def get_pending_fines(user_id):
    """Get pending (unpaid) fines for a user"""
    connection = connect_db()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                f.fine_id,
                f.loan_id,
                f.amount,
                f.description,
                l.due_date,
                b.title,
                b.author,
                b.book_id
            FROM 
                Fines f
            JOIN 
                Loans l ON f.loan_id = l.loan_id
            JOIN 
                Books b ON l.book_id = b.book_id
            WHERE 
                l.user_id = %s AND
                f.paid = 0
            ORDER BY 
                f.fine_id DESC
        """, (user_id,))
        
        return cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_payment_history(user_id):
    """Get payment history for a user"""
    connection = connect_db()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                f.fine_id,
                f.loan_id,
                f.amount,
                f.description,
                f.payment_date,
                b.title,
                b.author
            FROM 
                Fines f
            JOIN 
                Loans l ON f.loan_id = l.loan_id
            JOIN 
                Books b ON l.book_id = b.book_id
            WHERE 
                l.user_id = %s AND
                f.paid = 1
            ORDER BY 
                f.payment_date DESC
        """, (user_id,))
        
        return cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_loans_with_no_fines(user_id):
    """Get loans that were returned without fines"""
    connection = connect_db()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                l.loan_id,
                l.return_date,
                b.title,
                b.author
            FROM 
                Loans l
            JOIN 
                Books b ON l.book_id = b.book_id
            LEFT JOIN 
                Fines f ON l.loan_id = f.loan_id
            WHERE 
                l.user_id = %s AND
                l.return_date IS NOT NULL AND
                f.fine_id IS NULL
            ORDER BY 
                l.return_date DESC
            LIMIT 10
        """, (user_id,))
        
        return cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def pay_fine(fine_id, user_id):
    """Pay a fine"""
    connection = connect_db()
    if not connection:
        return False, "Database connection failed"
    
    try:
        cursor = connection.cursor()
        
        # Verify that this fine belongs to the user
        cursor.execute("""
            SELECT f.fine_id 
            FROM Fines f
            JOIN Loans l ON f.loan_id = l.loan_id
            WHERE f.fine_id = %s AND l.user_id = %s AND f.paid = 0
        """, (fine_id, user_id))
        
        if not cursor.fetchone():
            return False, "Fine not found or already paid"
        
        # Update fine as paid
        cursor.execute(
            "UPDATE Fines SET paid = 1, payment_date = CURDATE() WHERE fine_id = %s", 
            (fine_id,)
        )
        
        connection.commit()
        return True, "Payment successful"
    except mysql.connector.Error as err:
        return False, f"Database Error: {err}"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- Utility Functions -------------------
def format_date(date_obj):
    """Format date object to string"""
    if isinstance(date_obj, datetime):
        date_obj = date_obj.date()
    try:
        return date_obj.strftime('%b %d, %Y')
    except:
        return str(date_obj)

def format_currency(amount):
    """Format amount as currency"""
    try:
        return f"${float(amount):.2f}"
    except:
        return f"${0:.2f}"

# ------------------- Main Application Class -------------------
class FinesPaymentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Library Management System - Fines & Payment")
        self.root.geometry("1100x700")
        
        # Set appearance mode and default color theme
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")
        
        # Load user session
        self.user = load_session()
        if not self.user:
            print("No active user session found.")
            self.logout()
            return
        
        # Initialize UI
        self.setup_ui()
        
        # Load fines and payment history
        self.load_data()
    
    def setup_ui(self):
        """Set up the user interface"""
        # Create main frame layout
        self.main_frame = ctk.CTkFrame(self.root, fg_color="#f0f4f0")
        self.main_frame.pack(fill="both", expand=True)
        
        # Create sidebar frame
        self.sidebar = ctk.CTkFrame(self.main_frame, width=210, fg_color="#116636")
        self.sidebar.pack(side="left", fill="y", padx=0, pady=0)
        
        # Content frame (right side)
        self.content = ctk.CTkFrame(self.main_frame, fg_color="#e6f4e6")
        self.content.pack(side="right", fill="both", expand=True, padx=0, pady=0)
        
        # Create sidebar content
        self.create_sidebar()
        
        # Create content area
        self.create_content_area()
    
    def create_sidebar(self):
        """Create the sidebar with navigation"""
        # Library System label
        library_label = ctk.CTkLabel(
            self.sidebar, 
            text="📚 Library System", 
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white"
        )
        library_label.pack(anchor="w", padx=20, pady=(20, 5))
        
        # User welcome
        user_welcome = ctk.CTkLabel(
            self.sidebar,
            text=f"Welcome,\n{self.user['first_name']} {self.user['last_name']}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="white"
        )
        user_welcome.pack(anchor="w", padx=20, pady=(0, 20))
        
        # Separator
        separator = ctk.CTkFrame(self.sidebar, height=1, fg_color="white")
        separator.pack(fill="x", padx=10, pady=10)
        
        # Menu buttons with icons
        menu_items = [
            ("🏠 Dashboard", self.open_dashboard),
            ("🔍 Search Books", self.open_search),
            ("📖 My Borrowed Books", self.open_borrowed),
            ("💰 Fines & Fees", None),  # Current page
            ("👤 My Profile", self.open_profile),
        ]
        
        # Add menu buttons
        for i, (text, command) in enumerate(menu_items):
            if command:  # Regular button
                btn = ctk.CTkButton(
                    self.sidebar,
                    text=text,
                    anchor="w",
                    font=ctk.CTkFont(size=14),
                    fg_color="transparent",
                    text_color="white",
                    hover_color="#0d4f29",
                    command=command
                )
            else:  # Current page (highlight)
                btn = ctk.CTkButton(
                    self.sidebar,
                    text=text,
                    anchor="w",
                    font=ctk.CTkFont(size=14),
                    fg_color="#0d4f29",
                    text_color="white",
                    hover_color="#0d4f29"
                )
            btn.pack(fill="x", pady=5, padx=10)
        
        # Add some space before logout
        spacer = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=200)
        spacer.pack(fill="x")
        
        # Logout button at bottom
        logout_btn = ctk.CTkButton(
            self.sidebar,
            text="🚪 Logout",
            anchor="w",
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            text_color="white",
            hover_color="#0d4f29",
            command=self.logout
        )
        logout_btn.pack(fill="x", pady=5, padx=10, side="bottom")
    
    def create_content_area(self):
        """Create the content area with fines and payment history"""
        # Title
        title = ctk.CTkLabel(
            self.content, 
            text="Fines & Payment",
            font=ctk.CTkFont(size=24, weight="bold"),
            anchor="w"
        )
        title.pack(anchor="w", padx=30, pady=(20, 20))
        
        # Summary box - total outstanding fines
        self.summary_frame = ctk.CTkFrame(self.content, fg_color="white", corner_radius=10)
        self.summary_frame.pack(fill="x", padx=30, pady=(0, 20))
        
        self.summary_label = ctk.CTkLabel(
            self.summary_frame,
            text="Outstanding Fines:",
            font=ctk.CTkFont(size=16),
            anchor="w"
        )
        self.summary_label.pack(side="left", padx=20, pady=15)
        
        self.amount_label = ctk.CTkLabel(
            self.summary_frame,
            text="$0.00",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#d32f2f",
            anchor="e"
        )
        self.amount_label.pack(side="right", padx=20, pady=15)
        
        # Pending Fines Section
        pending_label = ctk.CTkLabel(
            self.content,
            text="⚠️ Pending Fines",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        pending_label.pack(anchor="w", padx=30, pady=(10, 10))
        
        # Scrollable frame for pending fines
        self.pending_outer_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.pending_outer_frame.pack(fill="x", padx=30, pady=(0, 20))
        
        # Create canvas for scrolling
        self.pending_canvas = ctk.CTkCanvas(
            self.pending_outer_frame,
            bg="#e6f4e6",
            highlightthickness=0
        )
        self.pending_canvas.pack(side="left", fill="both", expand=True)
        
        # Add a scrollbar
        scrollbar = ctk.CTkScrollbar(
            self.pending_outer_frame,
            orientation="vertical",
            command=self.pending_canvas.yview
        )
        scrollbar.pack(side="right", fill="y")
        
        # Configure the canvas
        self.pending_canvas.configure(yscrollcommand=scrollbar.set)
        self.pending_canvas.bind('<Configure>', 
            lambda e: self.pending_canvas.configure(scrollregion=self.pending_canvas.bbox("all"))
        )
        
        # Create a frame inside the canvas
        self.pending_frame = ctk.CTkFrame(self.pending_canvas, fg_color="#f0f4f0")
        self.pending_canvas.create_window((0, 0), window=self.pending_frame, anchor="nw")
        
        # Table headers for pending fines
        self.pending_headers = ["Title", "Due Date", "Fine Amount", "Action"]
        self.pending_col_widths = [350, 150, 150, 150]
        
        for i, header in enumerate(self.pending_headers):
            header_label = ctk.CTkLabel(
                self.pending_frame,
                text=header,
                fg_color="#333333",
                corner_radius=0,
                text_color="white",
                font=ctk.CTkFont(weight="bold"),
                width=self.pending_col_widths[i],
                height=30
            )
            header_label.grid(row=0, column=i, sticky="ew")
        
        # Payment History Section
        history_label = ctk.CTkLabel(
            self.content,
            text="🔄 Payment History",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        history_label.pack(anchor="w", padx=30, pady=(20, 10))
        
        # Scrollable frame for payment history
        self.history_outer_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.history_outer_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        
        # Create canvas for scrolling
        self.history_canvas = ctk.CTkCanvas(
            self.history_outer_frame,
            bg="#e6f4e6",
            highlightthickness=0
        )
        self.history_canvas.pack(side="left", fill="both", expand=True)
        
        # Add a scrollbar
        history_scrollbar = ctk.CTkScrollbar(
            self.history_outer_frame,
            orientation="vertical",
            command=self.history_canvas.yview
        )
        history_scrollbar.pack(side="right", fill="y")
        
        # Configure the canvas
        self.history_canvas.configure(yscrollcommand=history_scrollbar.set)
        self.history_canvas.bind('<Configure>', 
            lambda e: self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all"))
        )
        
        # Create a frame inside the canvas
        self.history_frame = ctk.CTkFrame(self.history_canvas, fg_color="#f0f4f0")
        self.history_canvas.create_window((0, 0), window=self.history_frame, anchor="nw")
        
        # Table headers for payment history
        self.history_headers = ["Title", "Paid Amount", "Payment Date", "Status"]
        self.history_col_widths = [350, 150, 150, 150]
        
        for i, header in enumerate(self.history_headers):
            header_label = ctk.CTkLabel(
                self.history_frame,
                text=header,
                fg_color="#333333",
                corner_radius=0,
                text_color="white",
                font=ctk.CTkFont(weight="bold"),
                width=self.history_col_widths[i],
                height=30
            )
            header_label.grid(row=0, column=i, sticky="ew")
        
        # Configure grid columns to expand properly
        for frame in [self.pending_frame, self.history_frame]:
            for i in range(4):
                frame.grid_columnconfigure(i, weight=1)
    
    def load_data(self):
        """Load fines and payment history data"""
        # Get pending fines
        pending_fines = get_pending_fines(self.user['user_id'])
        
        # Get payment history
        payment_history = get_payment_history(self.user['user_id'])
        
        # Get loans with no fines
        no_fine_loans = get_loans_with_no_fines(self.user['user_id'])
        
        # Calculate total outstanding amount
        total_outstanding = sum(float(fine['amount']) for fine in pending_fines)
        self.amount_label.configure(text=format_currency(total_outstanding))
        
        # Display pending fines
        if pending_fines:
            for idx, fine in enumerate(pending_fines, 1):
                # Title
                title_label = ctk.CTkLabel(
                    self.pending_frame,
                    text=fine['title'],
                    anchor="w",
                    fg_color="#ffffff",
                    corner_radius=0,
                    height=30
                )
                title_label.grid(row=idx, column=0, sticky="ew", padx=1, pady=1)
                
                # Due Date
                due_date_label = ctk.CTkLabel(
                    self.pending_frame,
                    text=format_date(fine['due_date']),
                    anchor="w",
                    fg_color="#ffffff",
                    corner_radius=0,
                    height=30
                )
                due_date_label.grid(row=idx, column=1, sticky="ew", padx=1, pady=1)
                
                # Fine Amount
                amount_label = ctk.CTkLabel(
                    self.pending_frame,
                    text=format_currency(fine['amount']),
                    anchor="w",
                    fg_color="#ffffff",
                    corner_radius=0,
                    height=30
                )
                amount_label.grid(row=idx, column=2, sticky="ew", padx=1, pady=1)
                
                # Pay Button
                pay_button = ctk.CTkButton(
                    self.pending_frame,
                    text="$ Pay Now",
                    fg_color="#d32f2f",
                    text_color="white",
                    hover_color="#b71c1c",
                    width=80,
                    height=25,
                    font=ctk.CTkFont(size=12),
                    command=lambda f_id=fine['fine_id']: self.pay_fine(f_id)
                )
                pay_button.grid(row=idx, column=3, padx=5, pady=5)
        else:
            # No pending fines message
            no_fines_label = ctk.CTkLabel(
                self.pending_frame,
                text="No pending fines",
                anchor="w",
                fg_color="#ffffff",
                corner_radius=0,
                height=30
            )
            no_fines_label.grid(row=1, column=0, columnspan=4, sticky="ew", padx=1, pady=1)
        
        # Combine payment history with no-fine loans
        history_data = []
        
        # Add paid fines
        for fine in payment_history:
            history_data.append({
                'title': fine['title'],
                'amount': fine['amount'],
                'date': fine['payment_date'],
                'status': 'Paid'
            })
        
        # Add no-fine loans
        for loan in no_fine_loans:
            history_data.append({
                'title': loan['title'],
                'amount': 0.00,
                'date': loan['return_date'],
                'status': 'No Fine'
            })
        
        # Sort by date, most recent first
        history_data.sort(key=lambda x: x['date'] if x['date'] else datetime.min, reverse=True)
        
        # Display payment history
        if history_data:
            for idx, item in enumerate(history_data, 1):
                # Title
                title_label = ctk.CTkLabel(
                    self.history_frame,
                    text=item['title'],
                    anchor="w",
                    fg_color="#ffffff",
                    corner_radius=0,
                    height=30
                )
                title_label.grid(row=idx, column=0, sticky="ew", padx=1, pady=1)
                
                # Amount
                amount_label = ctk.CTkLabel(
                    self.history_frame,
                    text=format_currency(item['amount']),
                    anchor="w",
                    fg_color="#ffffff",
                    corner_radius=0,
                    height=30
                )
                amount_label.grid(row=idx, column=1, sticky="ew", padx=1, pady=1)
                
                # Date
                date_label = ctk.CTkLabel(
                    self.history_frame,
                    text=format_date(item['date']),
                    anchor="w",
                    fg_color="#ffffff",
                    corner_radius=0,
                    height=30
                )
                date_label.grid(row=idx, column=2, sticky="ew", padx=1, pady=1)
                
                # Status
                if item['status'] == 'Paid':
                    status_frame = ctk.CTkFrame(self.history_frame, fg_color="#4caf50", corner_radius=10, height=22)
                    status_label = ctk.CTkLabel(
                        status_frame, 
                        text=item['status'],
                        text_color="white",
                        font=ctk.CTkFont(size=12),
                        width=60
                    )
                    status_label.pack(padx=5, pady=2)
                    status_frame.grid(row=idx, column=3, padx=5, pady=5)
                else:
                    status_frame = ctk.CTkFrame(self.history_frame, fg_color="#2196f3", corner_radius=10, height=22)
                    status_label = ctk.CTkLabel(
                        status_frame, 
                        text=item['status'],
                        text_color="white",
                        font=ctk.CTkFont(size=12),
                        width=60
                    )
                    status_label.pack(padx=5, pady=2)
                    status_frame.grid(row=idx, column=3, padx=5, pady=5)
        else:
            # No history message
            no_history_label = ctk.CTkLabel(
                self.history_frame,
                text="No payment history",
                anchor="w",
                fg_color="#ffffff",
                corner_radius=0,
                height=30
            )
            no_history_label.grid(row=1, column=0, columnspan=4, sticky="ew", padx=1, pady=1)
        
        # Update canvas scrollregion
        self.pending_canvas.update_idletasks()
        self.pending_canvas.configure(scrollregion=self.pending_canvas.bbox("all"))
        
        self.history_canvas.update_idletasks()
        self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all"))
    
    def pay_fine(self, fine_id):
        """Handle pay fine action"""
        # Show payment confirmation dialog
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Payment Confirmation")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.grab_set()  # Make it modal
        
        # Center the dialog on screen
        dialog_x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 200
        dialog_y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 100
        dialog.geometry(f"+{dialog_x}+{dialog_y}")
        
        # Dialog content
        frame = ctk.CTkFrame(dialog)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = ctk.CTkLabel(
            frame,
            text="Confirm Payment",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 15))
        
        message_label = ctk.CTkLabel(
            frame,
            text="Are you sure you want to pay this fine?",
            font=ctk.CTkFont(size=14)
        )
        message_label.pack(pady=(0, 20))
        
        # Button frame
        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))
        
        # Cancel button
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            font=ctk.CTkFont(size=14),
            fg_color="#f0f0f0",
            text_color="#333333",
            hover_color="#e0e0e0",
            width=120,
            command=dialog.destroy
        )
        cancel_button.pack(side="left", padx=5)
        
        # Confirm button
        def confirm_payment():
            dialog.destroy()
            success, message = pay_fine(fine_id, self.user['user_id'])
            if success:
                self.show_success_message(message)
                self.load_data()  # Refresh data
            else:
                self.show_error_message(message)
        
        confirm_button = ctk.CTkButton(
            button_frame,
            text="Confirm Payment",
            font=ctk.CTkFont(size=14),
            fg_color="#d32f2f",
            hover_color="#b71c1c",
            width=120,
            command=confirm_payment
        )
        confirm_button.pack(side="right", padx=5)
    
    def show_success_message(self, message):
        """Show success message dialog"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Success")
        dialog.geometry("300x150")
        dialog.resizable(False, False)
        dialog.grab_set()  # Make it modal
        
        # Center the dialog on screen
        dialog_x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 150
        dialog_y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 75
        dialog.geometry(f"+{dialog_x}+{dialog_y}")
        
        frame = ctk.CTkFrame(dialog)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        message_label = ctk.CTkLabel(
            frame,
            text=message,
            font=ctk.CTkFont(size=14)
        )
        message_label.pack(pady=(10, 20))
        
        ok_button = ctk.CTkButton(
            frame,
            text="OK",
            font=ctk.CTkFont(size=14),
            fg_color="#116636",
            hover_color="#0d4f29",
            command=dialog.destroy
        )
        ok_button.pack()
    
    def show_error_message(self, message):
        """Show error message dialog"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Error")
        dialog.geometry("300x150")
        dialog.resizable(False, False)
        dialog.grab_set()  # Make it modal
        
        # Center the dialog on screen
        dialog_x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 150
        dialog_y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 75
        dialog.geometry(f"+{dialog_x}+{dialog_y}")
        
        frame = ctk.CTkFrame(dialog)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        message_label = ctk.CTkLabel(
            frame,
            text=message,
            font=ctk.CTkFont(size=14),
            text_color="#d32f2f"
        )
        message_label.pack(pady=(10, 20))
        
        ok_button = ctk.CTkButton(
            frame,
            text="OK",
            font=ctk.CTkFont(size=14),
            fg_color="#116636",
            hover_color="#0d4f29",
            command=dialog.destroy
        )
        ok_button.pack()
    
    def open_dashboard(self):
        """Open the dashboard page"""
        self.root.destroy()
        os.system("python home.py")
    
    def open_search(self):
        """Open the search books page"""
        self.root.destroy()
        os.system("python browse.py")
    
    def open_borrowed(self):
        """Open the borrowed books page"""
        self.root.destroy()
        os.system("python borrow.py")
    
    def open_profile(self):
        """Open the profile page"""
        self.root.destroy()
        os.system("python home.py profile")
    
    def logout(self):
        """Logout and return to login page"""
        try:
            # Clear the session
            clear_session()
            
            # Close current window
            self.root.destroy()
            
            # Open login page
            os.system("python login.py")
        except Exception as e:
            print(f"Logout Error: {e}")