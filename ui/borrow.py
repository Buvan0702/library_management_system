import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
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
        messagebox.showerror("Database Connection Error", f"Failed to connect to database: {err}")
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
        messagebox.showerror("Session Error", f"Failed to load session: {e}")
        return None

def clear_session():
    """Delete the session file"""
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

# ------------------- Loan Functions -------------------
def get_active_loans(user_id):
    """Get all active loans for a user"""
    connection = connect_db()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                l.loan_id,
                b.book_id, 
                b.title, 
                b.author, 
                l.loan_date, 
                l.due_date,
                CASE 
                    WHEN l.due_date < CURDATE() THEN 
                        DATEDIFF(CURDATE(), l.due_date) * 0.5
                    ELSE 0.00
                END AS fine_amount
            FROM 
                Books b
            JOIN 
                Loans l ON b.book_id = l.book_id
            WHERE 
                l.user_id = %s AND
                l.return_date IS NULL
            ORDER BY 
                l.due_date
        """, (user_id,))
        
        return cursor.fetchall()
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_loan_history(user_id):
    """Get loan history for a user"""
    connection = connect_db()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                l.loan_id,
                b.book_id, 
                b.title, 
                b.author, 
                l.loan_date, 
                l.return_date,
                COALESCE(SUM(f.amount), 0.00) AS fine_paid
            FROM 
                Books b
            JOIN 
                Loans l ON b.book_id = l.book_id
            LEFT JOIN 
                Fines f ON l.loan_id = f.loan_id AND f.paid = 1
            WHERE 
                l.user_id = %s AND
                l.return_date IS NOT NULL
            GROUP BY
                l.loan_id
            ORDER BY 
                l.return_date DESC
        """, (user_id,))
        
        return cursor.fetchall()
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def return_book(loan_id, user_id):
    """Return a borrowed book"""
    connection = connect_db()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # First get the book_id and due_date for this loan
        cursor.execute("SELECT book_id, due_date FROM Loans WHERE loan_id = %s", (loan_id,))
        loan_data = cursor.fetchone()
        
        if loan_data:
            book_id, due_date = loan_data
            
            # Update loan return date
            cursor.execute(
                "UPDATE Loans SET return_date = CURDATE() WHERE loan_id = %s AND user_id = %s", 
                (loan_id, user_id)
            )
            
            # Increment available copies
            cursor.execute(
                "UPDATE Books SET available_copies = available_copies + 1 WHERE book_id = %s", 
                (book_id,)
            )
            
            # Check if book is overdue and create fine if needed
            if due_date < datetime.now().date():
                days_overdue = (datetime.now().date() - due_date).days
                fine_amount = days_overdue * 0.50  # $0.50 per day
                
                # Create fine record
                cursor.execute(
                    "INSERT INTO Fines (loan_id, amount, description, paid) VALUES (%s, %s, %s, 0)",
                    (loan_id, fine_amount, f"Late return fine: {days_overdue} days")
                )
            
            connection.commit()
            return True
        return False
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def pay_fine(loan_id, user_id):
    """Pay fine for an overdue book"""
    connection = connect_db()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Check if there are unpaid fines for this loan
        cursor.execute(
            "SELECT fine_id FROM Fines WHERE loan_id = %s AND paid = 0", 
            (loan_id,)
        )
        
        fine_ids = [row[0] for row in cursor.fetchall()]
        
        if fine_ids:
            # Update all fines as paid
            for fine_id in fine_ids:
                cursor.execute(
                    "UPDATE Fines SET paid = 1, payment_date = CURDATE() WHERE fine_id = %s", 
                    (fine_id,)
                )
            
            connection.commit()
            return True
        return False
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
        return False
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
class BorrowedBooksApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Library Management System - Borrowed Books")
        self.root.geometry("1100x700")
        
        # Set appearance mode and default color theme
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")
        
        # Load user session
        self.user = load_session()
        if not self.user:
            messagebox.showerror("Session Error", "No active user session found.")
            self.logout()
            return
        
        # Initialize UI
        self.setup_ui()
        
        # Load borrowed books and history
        self.load_data()
    
    def setup_ui(self):
        """Set up the user interface"""
        # Create main grid layout
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Create sidebar
        self.create_sidebar()
        
        # Create main content area
        self.create_main_content()
    
    def create_sidebar(self):
        """Create the sidebar with navigation buttons"""
        sidebar = ctk.CTkFrame(self.root, width=210, fg_color="#116636", corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)  # Prevent the frame from shrinking

        # Sidebar Title
        title_label = ctk.CTkLabel(sidebar, text="📑 Library System", font=ctk.CTkFont(size=16, weight="bold"), 
                                  text_color="white", anchor="w", padx=10, pady=10)
        title_label.pack(fill="x", pady=(20, 10))
        
        # User welcome message
        user_welcome = ctk.CTkLabel(sidebar, 
                                 text=f"Welcome,\n{self.user['first_name']} {self.user['last_name']}", 
                                 font=ctk.CTkFont(size=12, weight="bold"), 
                                 text_color="white", anchor="w", padx=10, pady=10)
        user_welcome.pack(fill="x", pady=(0, 20))
        
        # Separator
        separator = ctk.CTkFrame(sidebar, height=1, fg_color="white")
        separator.pack(fill="x", padx=10, pady=10)

        # Sidebar Buttons with commands
        menu_items = [
            ("🏠 Dashboard", self.open_dashboard),
            ("🔍 Search Books", self.open_search),
            ("📖 My Borrowed Books", None),  # Current page
            ("💰 Fines & Fees", self.open_fines),
            ("👤 My Profile", self.open_profile),
            ("🚪 Logout", self.logout)
        ]

        for text, command in menu_items:
            if command:  # Regular button
                button = ctk.CTkButton(sidebar, text=text, font=ctk.CTkFont(size=12), 
                                     fg_color="transparent", text_color="white", anchor="w",
                                     hover_color="#0d4f29", corner_radius=0, height=40,
                                     command=command)
            else:  # Current page (highlight)
                button = ctk.CTkButton(sidebar, text=text, font=ctk.CTkFont(size=12), 
                                     fg_color="#0d4f29", text_color="white", anchor="w",
                                     hover_color="#0d4f29", corner_radius=0, height=40)
            button.pack(fill="x", pady=2)
    
    def create_main_content(self):
        """Create the main content area"""
        self.main_frame = ctk.CTkFrame(self.root, fg_color="#f0f5f0", corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Title Frame
        title_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        title = ctk.CTkLabel(title_frame, text="My Borrowed Books", 
                          font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=10)
        
        # Separator line
        separator = ctk.CTkFrame(self.main_frame, height=1, fg_color="#d1d1d1")
        separator.grid(row=1, column=0, sticky="ew", pady=5)
        
        # Current Loans Section
        self.current_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.current_frame.grid(row=2, column=0, sticky="ew", pady=15)
        
        # Current Loans Label
        current_label = ctk.CTkLabel(self.current_frame, text="📚 Current Loans", 
                                  font=ctk.CTkFont(size=16, weight="bold"), 
                                  anchor="w")
        current_label.pack(anchor="w", pady=(0, 10))
        
        # Create frame for treeview
        loans_tree_frame = ctk.CTkFrame(self.current_frame, fg_color="transparent")
        loans_tree_frame.pack(fill="x")
        
        # Set up treeview style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="white", fieldbackground="white", foreground="black")
        style.configure("Treeview.Heading", background="#f0f0f0", foreground="black", font=("Arial", 10, "bold"))
        style.map("Treeview", background=[("selected", "#116636")], foreground=[("selected", "white")])
        
        # Create treeview for current loans
        columns = ("Title", "Author", "Borrowed Date", "Due Date", "Fine", "Action")
        self.current_tree = ttk.Treeview(loans_tree_frame, columns=columns, show="headings", height=6)
        self.current_tree.pack(side="left", fill="x", expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(loans_tree_frame, orient="vertical", command=self.current_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.current_tree.configure(yscrollcommand=scrollbar.set)
        
        # Configure columns
        self.current_tree.column("Title", width=250, anchor="w")
        self.current_tree.column("Author", width=180, anchor="w")
        self.current_tree.column("Borrowed Date", width=120, anchor="center")
        self.current_tree.column("Due Date", width=120, anchor="center")
        self.current_tree.column("Fine", width=80, anchor="center")
        self.current_tree.column("Action", width=150, anchor="center")
        
        # Configure column headings
        for col in columns:
            self.current_tree.heading(col, text=col)
        
        # Add separator
        mid_separator = ctk.CTkFrame(self.main_frame, height=1, fg_color="#d1d1d1")
        mid_separator.grid(row=3, column=0, sticky="ew", pady=15)
        
        # Loan History Section
        self.history_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.history_frame.grid(row=4, column=0, sticky="nsew", pady=15)
        
        # Loan History Label
        history_label = ctk.CTkLabel(self.history_frame, text="🔄 Borrowing History", 
                                   font=ctk.CTkFont(size=16, weight="bold"), 
                                   anchor="w")
        history_label.pack(anchor="w", pady=(0, 10))
        
        # Create frame for history treeview
        history_tree_frame = ctk.CTkFrame(self.history_frame, fg_color="transparent")
        history_tree_frame.pack(fill="both", expand=True)
        
        # Create treeview for loan history
        history_columns = ("Title", "Author", "Borrowed Date", "Returned Date", "Fine Paid")
        self.history_tree = ttk.Treeview(history_tree_frame, columns=history_columns, show="headings", height=10)
        self.history_tree.pack(side="left", fill="both", expand=True)
        
        # Add scrollbar for history
        history_scrollbar = ttk.Scrollbar(history_tree_frame, orient="vertical", command=self.history_tree.yview)
        history_scrollbar.pack(side="right", fill="y")
        self.history_tree.configure(yscrollcommand=history_scrollbar.set)
        
        # Configure history columns
        self.history_tree.column("Title", width=250, anchor="w")
        self.history_tree.column("Author", width=180, anchor="w")
        self.history_tree.column("Borrowed Date", width=120, anchor="center")
        self.history_tree.column("Returned Date", width=120, anchor="center")
        self.history_tree.column("Fine Paid", width=100, anchor="center")
        
        # Configure history column headings
        for col in history_columns:
            self.history_tree.heading(col, text=col)
    
    def load_data(self):
        """Load borrowed books and history data"""
        # Clear existing data
        for item in self.current_tree.get_children():
            self.current_tree.delete(item)
        
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Load active loans
        loans = get_active_loans(self.user['user_id'])
        self.loan_ids = {}
        
        for loan in loans:
            loan_date = format_date(loan['loan_date'])
            due_date = format_date(loan['due_date'])
            fine = format_currency(loan['fine_amount'])
            
            item_id = self.current_tree.insert("", "end", values=(
                loan['title'],
                loan['author'],
                loan_date,
                due_date,
                fine,
                ""  # Action column will be filled with buttons
            ))
            
            # Store loan_id for button actions
            self.loan_ids[item_id] = loan['loan_id']
        
        # No active loans message
        if not loans:
            self.current_tree.insert("", "end", values=(
                "No active loans found",
                "",
                "",
                "",
                "",
                ""
            ))
        
        # Load loan history
        history = get_loan_history(self.user['user_id'])
        
        for record in history:
            loan_date = format_date(record['loan_date'])
            return_date = format_date(record['return_date'])
            fine_paid = format_currency(record['fine_paid'])
            
            self.history_tree.insert("", "end", values=(
                record['title'],
                record['author'],
                loan_date,
                return_date,
                fine_paid
            ))
        
        # No history message
        if not history:
            self.history_tree.insert("", "end", values=(
                "No borrowing history found",
                "",
                "",
                "",
                ""
            ))
        
        # Add buttons to active loans
        self.add_action_buttons()
    
    def add_action_buttons(self):
        """Add action buttons to the active loans table"""
        for item in self.current_tree.get_children():
            values = self.current_tree.item(item, 'values')
            if values[0] == "No active loans found":
                continue
                
            fine_amount = values[4]
            has_fine = False
            try:
                fine_value = float(fine_amount.replace('$', ''))
                has_fine = fine_value > 0
            except:
                pass
            
            bbox = self.current_tree.bbox(item, column="Action")
            if bbox:
                button_frame = ctk.CTkFrame(self.current_tree, fg_color="transparent", width=140, height=30)
                button_frame.place(x=bbox[0] + 5, y=bbox[1])
                
                if has_fine:
                    # Pay fine button
                    pay_button = ctk.CTkButton(
                        button_frame,
                        text="Pay Fine",
                        font=ctk.CTkFont(size=10),
                        fg_color="#d9534f",
                        hover_color="#c9302c",
                        width=70,
                        height=25,
                        corner_radius=3,
                        command=lambda i=item: self.pay_fine_action(i)
                    )
                    pay_button.pack(side="left", padx=(0, 5))
                
                # Return button
                return_button = ctk.CTkButton(
                    button_frame,
                    text="Return",
                    font=ctk.CTkFont(size=10),
                    fg_color="#116636",
                    hover_color="#0d4f29",
                    width=70,
                    height=25,
                    corner_radius=3,
                    command=lambda i=item: self.return_book_action(i)
                )
                return_button.pack(side="left")
    
    def return_book_action(self, tree_item):
        """Handle return book action"""
        loan_id = self.loan_ids.get(tree_item)
        if not loan_id:
            return
        
        result = messagebox.askyesno("Confirm Return", "Are you sure you want to return this book?")
        if result:
            success = return_book(loan_id, self.user['user_id'])
            if success:
                messagebox.showinfo("Success", "Book returned successfully!")
                self.load_data()  # Refresh data
            else:
                messagebox.showerror("Error", "Failed to return book.")
    
    def pay_fine_action(self, tree_item):
        """Handle pay fine action"""
        loan_id = self.loan_ids.get(tree_item)
        if not loan_id:
            return
        
        values = self.current_tree.item(tree_item, 'values')
        fine_amount = values[4]
        
        result = messagebox.askyesno("Confirm Payment", f"Pay fine of {fine_amount}?")
        if result:
            success = pay_fine(loan_id, self.user['user_id'])
            if success:
                messagebox.showinfo("Success", "Fine paid successfully!")
                self.load_data()  # Refresh data
            else:
                messagebox.showerror("Error", "Failed to process payment.")
    
    def open_dashboard(self):
        """Open the dashboard page"""
        self.root.destroy()
        os.system("python home.py")
    
    def open_search(self):
        """Open the search books page"""
        self.root.destroy()
        os.system("python browse.py")
    
    def open_fines(self):
        """Open the fines page"""
        self.root.destroy()
        os.system("python home.py fines")
    
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
            messagebox.showerror("Error", f"Failed to logout: {e}")
            self.root.destroy()

# ------------------- Main Application -------------------
if __name__ == "__main__":
    try:
        root = ctk.CTk()
        app = BorrowedBooksApp(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Application Error", f"An error occurred: {e}")