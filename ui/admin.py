import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk
import mysql.connector
import json
import os
from datetime import datetime, timedelta
import hashlib
import re

# ------------------- Constants -------------------
SESSION_FILE = 'admin_session.json'
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
    """Load admin session data"""
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, 'r') as f:
                return json.load(f)
        return None
    except Exception as e:
        messagebox.showerror("Session Error", f"Failed to load session: {e}")
        return None

def save_session(admin_data):
    """Save admin session data"""
    with open(SESSION_FILE, 'w') as f:
        json.dump(admin_data, f)

def clear_session():
    """Delete the session file"""
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

# ------------------- Admin Auth Functions -------------------
def admin_login(email, password):
    """Authenticate admin credentials"""
    connection = connect_db()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute(
            "SELECT user_id, first_name, last_name, email, role FROM Users WHERE email = %s AND password = %s AND role = 'admin'",
            (email, hashed_password)
        )
        
        admin = cursor.fetchone()
        return admin
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- Book Management Functions -------------------
def get_books(search_term=""):
    """Get all books with optional search"""
    connection = connect_db()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        if search_term:
            query = """
                SELECT 
                    book_id, title, author, genre, isbn, publication_year, 
                    available_copies, total_copies, 
                    (total_copies - available_copies) AS borrowed_copies
                FROM 
                    Books
                WHERE 
                    title LIKE %s OR author LIKE %s OR genre LIKE %s OR isbn LIKE %s
                ORDER BY 
                    title
            """
            search_param = f"%{search_term}%"
            cursor.execute(query, (search_param, search_param, search_param, search_param))
        else:
            query = """
                SELECT 
                    book_id, title, author, genre, isbn, publication_year, 
                    available_copies, total_copies, 
                    (total_copies - available_copies) AS borrowed_copies
                FROM 
                    Books
                ORDER BY 
                    title
            """
            cursor.execute(query)
        
        return cursor.fetchall()
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def add_book(title, author, genre, isbn, publication_year, total_copies, description=""):
    """Add a new book"""
    connection = connect_db()
    if not connection:
        return False, "Database connection failed"
    
    try:
        cursor = connection.cursor()
        
        # Check if book with same ISBN already exists
        cursor.execute("SELECT book_id FROM Books WHERE isbn = %s", (isbn,))
        if cursor.fetchone():
            return False, "A book with this ISBN already exists"
        
        # Insert the new book
        cursor.execute(
            """
            INSERT INTO Books (
                title, author, genre, isbn, publication_year, 
                total_copies, available_copies, description
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (title, author, genre, isbn, publication_year, total_copies, total_copies, description)
        )
        
        connection.commit()
        return True, "Book added successfully"
    except mysql.connector.Error as err:
        return False, f"Database Error: {err}"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def update_book(book_id, title, author, genre, isbn, publication_year, total_copies, description=""):
    """Update an existing book"""
    connection = connect_db()
    if not connection:
        return False, "Database connection failed"
    
    try:
        cursor = connection.cursor()
        
        # Check if book exists
        cursor.execute("SELECT available_copies FROM Books WHERE book_id = %s", (book_id,))
        result = cursor.fetchone()
        if not result:
            return False, "Book not found"
        
        available_copies = result[0]
        
        # Calculate new available copies
        borrowed_copies = total_copies - available_copies
        new_available = max(0, total_copies - borrowed_copies)
        
        # Update the book
        cursor.execute(
            """
            UPDATE Books SET 
                title = %s, author = %s, genre = %s, isbn = %s, 
                publication_year = %s, total_copies = %s, 
                available_copies = %s, description = %s
            WHERE book_id = %s
            """,
            (title, author, genre, isbn, publication_year, 
             total_copies, new_available, description, book_id)
        )
        
        connection.commit()
        return True, "Book updated successfully"
    except mysql.connector.Error as err:
        return False, f"Database Error: {err}"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def delete_book(book_id):
    """Delete a book"""
    connection = connect_db()
    if not connection:
        return False, "Database connection failed"
    
    try:
        cursor = connection.cursor()
        
        # Check if book is currently borrowed
        cursor.execute(
            "SELECT COUNT(*) FROM Loans WHERE book_id = %s AND return_date IS NULL", 
            (book_id,)
        )
        
        if cursor.fetchone()[0] > 0:
            return False, "Cannot delete book: it is currently borrowed by users"
        
        # Delete the book
        cursor.execute("DELETE FROM Books WHERE book_id = %s", (book_id,))
        
        connection.commit()
        return True, "Book deleted successfully"
    except mysql.connector.Error as err:
        return False, f"Database Error: {err}"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- User Management Functions -------------------
def get_users(search_term=""):
    """Get all users with optional search"""
    connection = connect_db()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        if search_term:
            query = """
                SELECT 
                    user_id, first_name, last_name, email, role, 
                    registration_date
                FROM 
                    Users
                WHERE 
                    first_name LIKE %s OR last_name LIKE %s OR email LIKE %s
                ORDER BY 
                    registration_date DESC
            """
            search_param = f"%{search_term}%"
            cursor.execute(query, (search_param, search_param, search_param))
        else:
            query = """
                SELECT 
                    user_id, first_name, last_name, email, role, 
                    registration_date
                FROM 
                    Users
                ORDER BY 
                    registration_date DESC
            """
            cursor.execute(query)
        
        return cursor.fetchall()
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def create_user(first_name, last_name, email, password, role="member"):
    """Create a new user"""
    connection = connect_db()
    if not connection:
        return False, "Database connection failed"
    
    try:
        cursor = connection.cursor()
        
        # Check if email already exists
        cursor.execute("SELECT user_id FROM Users WHERE email = %s", (email,))
        if cursor.fetchone():
            return False, "A user with this email already exists"
        
        # Hash password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Insert the new user
        cursor.execute(
            """
            INSERT INTO Users (
                first_name, last_name, email, password, role, registration_date
            ) VALUES (%s, %s, %s, %s, %s, CURDATE())
            """,
            (first_name, last_name, email, hashed_password, role)
        )
        
        connection.commit()
        return True, "User created successfully"
    except mysql.connector.Error as err:
        return False, f"Database Error: {err}"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def update_user(user_id, first_name, last_name, email, role, new_password=None):
    """Update an existing user"""
    connection = connect_db()
    if not connection:
        return False, "Database connection failed"
    
    try:
        cursor = connection.cursor()
        
        # Check if user exists
        cursor.execute("SELECT user_id FROM Users WHERE user_id = %s", (user_id,))
        if not cursor.fetchone():
            return False, "User not found"
        
        # Update user with or without password change
        if new_password:
            hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
            cursor.execute(
                """
                UPDATE Users SET 
                    first_name = %s, last_name = %s, email = %s, role = %s, password = %s
                WHERE user_id = %s
                """,
                (first_name, last_name, email, role, hashed_password, user_id)
            )
        else:
            cursor.execute(
                """
                UPDATE Users SET 
                    first_name = %s, last_name = %s, email = %s, role = %s
                WHERE user_id = %s
                """,
                (first_name, last_name, email, role, user_id)
            )
        
        connection.commit()
        return True, "User updated successfully"
    except mysql.connector.Error as err:
        return False, f"Database Error: {err}"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def delete_user(user_id):
    """Delete a user"""
    connection = connect_db()
    if not connection:
        return False, "Database connection failed"
    
    try:
        cursor = connection.cursor()
        
        # Check if user has active loans
        cursor.execute(
            "SELECT COUNT(*) FROM Loans WHERE user_id = %s AND return_date IS NULL", 
            (user_id,)
        )
        
        if cursor.fetchone()[0] > 0:
            return False, "Cannot delete user: they have active loans"
        
        # Delete any fines
        cursor.execute(
            """
            DELETE FROM Fines
            WHERE loan_id IN (SELECT loan_id FROM Loans WHERE user_id = %s)
            """, 
            (user_id,)
        )
        
        # Delete loan history
        cursor.execute("DELETE FROM Loans WHERE user_id = %s", (user_id,))
        
        # Delete the user
        cursor.execute("DELETE FROM Users WHERE user_id = %s", (user_id,))
        
        connection.commit()
        return True, "User deleted successfully"
    except mysql.connector.Error as err:
        return False, f"Database Error: {err}"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- Dashboard Statistics -------------------
def get_dashboard_stats():
    """Get statistics for the dashboard"""
    connection = connect_db()
    if not connection:
        return {}
    
    try:
        cursor = connection.cursor()
        
        # Total Books Count
        cursor.execute("SELECT SUM(total_copies) FROM Books")
        total_books = cursor.fetchone()[0] or 0
        
        # Borrowed Books Count
        cursor.execute("SELECT COUNT(*) FROM Loans WHERE return_date IS NULL")
        borrowed_books = cursor.fetchone()[0] or 0
        
        # Total Users Count
        cursor.execute("SELECT COUNT(*) FROM Users")
        total_users = cursor.fetchone()[0] or 0
        
        # Pending Fines Amount
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM Fines WHERE paid = 0")
        pending_fines = cursor.fetchone()[0] or 0
        
        # Books by Genre
        cursor.execute("""
            SELECT genre, COUNT(*) as count 
            FROM Books 
            GROUP BY genre 
            ORDER BY count DESC 
            LIMIT 5
        """)
        genres = cursor.fetchall()
        
        # Recent Loans
        cursor.execute("""
            SELECT 
                b.title, u.first_name, u.last_name, l.loan_date, l.due_date
            FROM 
                Loans l
            JOIN 
                Books b ON l.book_id = b.book_id
            JOIN 
                Users u ON l.user_id = u.user_id
            WHERE 
                l.return_date IS NULL
            ORDER BY 
                l.loan_date DESC
            LIMIT 5
        """)
        recent_loans = cursor.fetchall()
        
        return {
            "total_books": total_books,
            "borrowed_books": borrowed_books,
            "total_users": total_users,
            "pending_fines": pending_fines,
            "genres": genres,
            "recent_loans": recent_loans
        }
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
        return {}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- Main Application Class -------------------
class LibraryAdminApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Library Management System - Admin Dashboard")
        self.root.geometry("1200x700")
        
        # Set appearance mode and default color theme
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")
        
        # Check admin session
        self.admin = load_session()
        if not self.admin:
            self.show_login()
            return
        
        # Set up UI once admin is authenticated
        self.setup_ui()
        
        # Load dashboard by default
        self.show_dashboard()
        
    def setup_ui(self):
        """Set up the main UI once admin is authenticated"""
        # Create main frame layout
        self.main_frame = ctk.CTkFrame(self.root, fg_color="#f0f4f0")
        self.main_frame.pack(fill="both", expand=True)
        
        # Create sidebar
        self.sidebar = ctk.CTkFrame(self.main_frame, width=210, fg_color="#116636")
        self.sidebar.pack(side="left", fill="y", padx=0, pady=0)
        
        # Content frame (right side)
        self.content = ctk.CTkFrame(self.main_frame, fg_color="#e6f4e6")
        self.content.pack(side="right", fill="both", expand=True, padx=0, pady=0)
        
        # Set up sidebar
        self.setup_sidebar()
        
        # Initialize content frames dictionary
        self.content_frames = {}
    
    def setup_sidebar(self):
        """Set up the sidebar with navigation"""
        # Admin Dashboard Label
        library_label = ctk.CTkLabel(
            self.sidebar, 
            text="📚 Library Admin", 
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white"
        )
        library_label.pack(anchor="w", padx=20, pady=(20, 5))
        
        # Admin name
        admin_welcome = ctk.CTkLabel(
            self.sidebar,
            text=f"Welcome,\n{self.admin['first_name']} {self.admin['last_name']}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="white"
        )
        admin_welcome.pack(anchor="w", padx=20, pady=(0, 20))
        
        # Separator
        separator = ctk.CTkFrame(self.sidebar, height=1, fg_color="white")
        separator.pack(fill="x", padx=10, pady=10)
        
        # Menu buttons 
        menu_items = [
            ("📊 Dashboard", self.show_dashboard),
            ("📚 Manage Books", self.show_books),
            ("👥 Manage Users", self.show_users),
            ("💰 Manage Fines", self.show_fines),
        ]
        
        # Create buttons
        self.menu_buttons = {}
        for text, command in menu_items:
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
            btn.pack(fill="x", pady=5, padx=10)
            self.menu_buttons[text] = btn
        
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
    
    def highlight_active_menu(self, active_menu):
        """Highlight the active menu button"""
        for text, button in self.menu_buttons.items():
            if text == active_menu:
                button.configure(fg_color="#0d4f29")
            else:
                button.configure(fg_color="transparent")
    
    def show_login(self):
        """Show admin login screen"""
        # Clear the root window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Create login frame
        login_frame = ctk.CTkFrame(self.root)
        login_frame.pack(fill="both", expand=True)
        
        # Add title
        title_label = ctk.CTkLabel(
            login_frame,
            text="Library Admin Login",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(100, 30))
        
        # Create input fields frame
        input_frame = ctk.CTkFrame(login_frame, fg_color="transparent")
        input_frame.pack(pady=20)
        
        # Email field
        email_label = ctk.CTkLabel(
            input_frame,
            text="Email:",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=100,
            anchor="e"
        )
        email_label.grid(row=0, column=0, padx=(20, 10), pady=10)
        
        email_entry = ctk.CTkEntry(
            input_frame,
            width=300,
            height=40,
            placeholder_text="Enter admin email"
        )
        email_entry.grid(row=0, column=1, padx=(0, 20), pady=10)
        
        # Password field
        password_label = ctk.CTkLabel(
            input_frame,
            text="Password:",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=100,
            anchor="e"
        )
        password_label.grid(row=1, column=0, padx=(20, 10), pady=10)
        
        password_entry = ctk.CTkEntry(
            input_frame,
            width=300,
            height=40,
            placeholder_text="Enter password",
            show="•"
        )
        password_entry.grid(row=1, column=1, padx=(0, 20), pady=10)
        
        # Error message label
        error_label = ctk.CTkLabel(
            login_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#d32f2f"
        )
        error_label.pack()
        
        # Login button
        def handle_login():
            email = email_entry.get()
            password = password_entry.get()
            
            if not email or not password:
                error_label.configure(text="Please enter both email and password")
                return
            
            admin = admin_login(email, password)
            if admin:
                # Save admin session
                save_session(admin)
                
                # Reload the application
                self.admin = admin
                self.setup_ui()
                self.show_dashboard()
            else:
                error_label.configure(text="Invalid admin credentials or insufficient privileges")
        
        login_button = ctk.CTkButton(
            login_frame,
            text="Login",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#116636",
            hover_color="#0d4f29",
            width=200,
            height=40,
            command=handle_login
        )
        login_button.pack(pady=20)
        
        # Bind Enter key to login
        password_entry.bind("<Return>", lambda event: handle_login())
    
    def show_dashboard(self):
        """Show the dashboard page"""
        self.highlight_active_menu("📊 Dashboard")
        
        # Clear content area
        for widget in self.content.winfo_children():
            widget.destroy()
        
        # Create book management title
        title = ctk.CTkLabel(
            self.content, 
            text="Book Management",
            font=ctk.CTkFont(size=24, weight="bold"),
            anchor="w"
        )
        title.pack(anchor="w", padx=30, pady=(20, 10))
        
        # Search and Add Book Bar
        action_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        action_frame.pack(fill="x", padx=30, pady=(10, 20))
        
        # Search box
        search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(
            action_frame,
            width=400,
            height=40,
            placeholder_text="Search by title, author, genre or ISBN",
            textvariable=search_var
        )
        search_entry.pack(side="left")
        
        def perform_search():
            search_term = search_var.get()
            self.populate_books_table(search_term)
        
        search_button = ctk.CTkButton(
            action_frame,
            text="🔍 Search",
            width=120,
            height=40,
            fg_color="#116636",
            hover_color="#0d4f29",
            command=perform_search
        )
        search_button.pack(side="left", padx=(10, 0))
        
        # Add New Book Button
        add_button = ctk.CTkButton(
            action_frame,
            text="+ Add New Book",
            width=150,
            height=40,
            fg_color="#2196f3",
            hover_color="#1976d2",
            command=self.show_book_form
        )
        add_button.pack(side="right")
        
        # Bind Enter key to search
        search_entry.bind("<Return>", lambda event: perform_search())
        
        # Books Table
        table_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        
        # Create scrollable table
        # Style for treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="white", fieldbackground="white", foreground="black")
        style.configure("Treeview.Heading", background="#f0f0f0", foreground="black", font=("Arial", 10, "bold"))
        style.map("Treeview", background=[("selected", "#116636")], foreground=[("selected", "white")])
        
        # Table columns
        self.books_columns = ("ID", "Title", "Author", "Genre", "ISBN", "Year", "Available", "Total", "Actions")
        
        # Create treeview
        self.books_tree = ttk.Treeview(
            table_frame, 
            columns=self.books_columns, 
            show="headings", 
            height=20,
            selectmode="browse"
        )
        self.books_tree.pack(side="left", fill="both", expand=True)
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.books_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.books_tree.configure(yscrollcommand=scrollbar.set)
        
        # Configure column widths and headings
        column_widths = {
            "ID": 50,
            "Title": 250,
            "Author": 150,
            "Genre": 100,
            "ISBN": 100,
            "Year": 60,
            "Available": 70,
            "Total": 60,
            "Actions": 120
        }
        
        for col in self.books_columns:
            self.books_tree.heading(col, text=col)
            self.books_tree.column(col, width=column_widths.get(col, 100), anchor="w" if col != "Actions" else "center")
        
        # Initial load of books
        self.populate_books_table()
    
    def populate_books_table(self, search_term=""):
        """Populate the books table with data"""
        # Clear existing data
        for item in self.books_tree.get_children():
            self.books_tree.delete(item)
        
        # Get books data
        books = get_books(search_term)
        
        # Insert books into table
        for book in books:
            item_id = self.books_tree.insert("", "end", values=(
                book['book_id'],
                book['title'],
                book['author'],
                book['genre'],
                book['isbn'],
                book['publication_year'],
                book['available_copies'],
                book['total_copies'],
                ""  # Actions column will be filled with buttons
            ))
            
        # Add buttons to the Actions column
        self.add_book_action_buttons()
    
    def add_book_action_buttons(self):
        """Add edit and delete buttons to the books table"""
        for item in self.books_tree.get_children():
            # Get the book ID
            book_id = self.books_tree.item(item, 'values')[0]
            
            # Get bounding box for action column
            col_idx = self.books_columns.index("Actions")
            bbox = self.books_tree.bbox(item, column=col_idx)
            
            if bbox:  # If visible
                # Create a frame for the buttons
                button_frame = ctk.CTkFrame(self.books_tree, fg_color="transparent")
                button_frame.place(x=bbox[0], y=bbox[1], width=120, height=bbox[3])
                
                # Edit button
                edit_button = ctk.CTkButton(
                    button_frame, 
                    text="Edit",
                    width=50,
                    height=20,
                    fg_color="#FFA500",
                    hover_color="#FF8C00",
                    corner_radius=4,
                    font=ctk.CTkFont(size=10),
                    command=lambda b_id=book_id: self.show_book_form(b_id)
                )
                edit_button.pack(side="left", padx=(0, 5))
                
                # Delete button
                delete_button = ctk.CTkButton(
                    button_frame, 
                    text="Delete",
                    width=50,
                    height=20,
                    fg_color="#FF5252",
                    hover_color="#D32F2F",
                    corner_radius=4,
                    font=ctk.CTkFont(size=10),
                    command=lambda b_id=book_id: self.confirm_delete_book(b_id)
                )
                delete_button.pack(side="left")
    
    def show_book_form(self, book_id=None):
        """Show form to add or edit a book"""
        # Create a dialog window
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Add New Book" if book_id is None else "Edit Book")
        dialog.geometry("600x550")
        dialog.resizable(False, False)
        dialog.grab_set()  # Make it modal
        
        # Center the dialog on screen
        dialog_x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 300
        dialog_y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 275
        dialog.geometry(f"+{dialog_x}+{dialog_y}")
        
        # Book data (empty for new, populated for edit)
        book_data = {}
        if book_id:
            # Fetch book data for editing
            books = get_books()
            for book in books:
                if str(book['book_id']) == str(book_id):
                    book_data = book
                    break
        
        # Form frame
        form_frame = ctk.CTkFrame(dialog)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        form_title = ctk.CTkLabel(
            form_frame,
            text="Add New Book" if book_id is None else "Edit Book",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        form_title.pack(pady=(0, 20))
        
        # Input fields frame
        input_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        input_frame.pack(fill="x", pady=10)
        
        # Configure grid
        input_frame.grid_columnconfigure(1, weight=1)
        
        # Title field
        ctk.CTkLabel(input_frame, text="Title:", anchor="e", width=100).grid(row=0, column=0, padx=(20, 10), pady=10, sticky="e")
        title_entry = ctk.CTkEntry(input_frame, width=400, height=30)
        title_entry.grid(row=0, column=1, padx=(0, 20), pady=10, sticky="ew")
        if 'title' in book_data:
            title_entry.insert(0, book_data['title'])
        
        # Author field
        ctk.CTkLabel(input_frame, text="Author:", anchor="e", width=100).grid(row=1, column=0, padx=(20, 10), pady=10, sticky="e")
        author_entry = ctk.CTkEntry(input_frame, width=400, height=30)
        author_entry.grid(row=1, column=1, padx=(0, 20), pady=10, sticky="ew")
        if 'author' in book_data:
            author_entry.insert(0, book_data['author'])
        
        # Genre field
        ctk.CTkLabel(input_frame, text="Genre:", anchor="e", width=100).grid(row=2, column=0, padx=(20, 10), pady=10, sticky="e")
        genre_entry = ctk.CTkEntry(input_frame, width=400, height=30)
        genre_entry.grid(row=2, column=1, padx=(0, 20), pady=10, sticky="ew")
        if 'genre' in book_data:
            genre_entry.insert(0, book_data['genre'])
        
        # ISBN field
        ctk.CTkLabel(input_frame, text="ISBN:", anchor="e", width=100).grid(row=3, column=0, padx=(20, 10), pady=10, sticky="e")
        isbn_entry = ctk.CTkEntry(input_frame, width=400, height=30)
        isbn_entry.grid(row=3, column=1, padx=(0, 20), pady=10, sticky="ew")
        if 'isbn' in book_data:
            isbn_entry.insert(0, book_data['isbn'])
        
        # Publication Year field
        ctk.CTkLabel(input_frame, text="Year:", anchor="e", width=100).grid(row=4, column=0, padx=(20, 10), pady=10, sticky="e")
        year_entry = ctk.CTkEntry(input_frame, width=400, height=30)
        year_entry.grid(row=4, column=1, padx=(0, 20), pady=10, sticky="ew")
        if 'publication_year' in book_data:
            year_entry.insert(0, str(book_data['publication_year']))
        
        # Total Copies field
        ctk.CTkLabel(input_frame, text="Total Copies:", anchor="e", width=100).grid(row=5, column=0, padx=(20, 10), pady=10, sticky="e")
        copies_entry = ctk.CTkEntry(input_frame, width=400, height=30)
        copies_entry.grid(row=5, column=1, padx=(0, 20), pady=10, sticky="ew")
        if 'total_copies' in book_data:
            copies_entry.insert(0, str(book_data['total_copies']))
        
        # Description field
        ctk.CTkLabel(input_frame, text="Description:", anchor="e", width=100).grid(row=6, column=0, padx=(20, 10), pady=10, sticky="ne")
        description_text = ctk.CTkTextbox(input_frame, width=400, height=100)
        description_text.grid(row=6, column=1, padx=(0, 20), pady=10, sticky="ew")
        if 'description' in book_data:
            description_text.insert("1.0", book_data.get('description', ''))
        
        # Error message label
        error_label = ctk.CTkLabel(
            form_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#d32f2f"
        )
        error_label.pack(pady=(10, 0))
        
        # Button frame
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(20, 0))
        
        # Cancel button
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            font=ctk.CTkFont(size=14),
            fg_color="#f0f0f0",
            text_color="#333333",
            hover_color="#e0e0e0",
            width=100,
            height=35,
            command=dialog.destroy
        )
        cancel_button.pack(side="left", padx=5)
        
        # Save/Update button
        def save_book():
            # Validate input
            title = title_entry.get().strip()
            author = author_entry.get().strip()
            genre = genre_entry.get().strip()
            isbn = isbn_entry.get().strip()
            year_str = year_entry.get().strip()
            copies_str = copies_entry.get().strip()
            description = description_text.get("1.0", "end-1c").strip()
            
            # Basic validation
            if not title or not author or not genre or not isbn:
                error_label.configure(text="Title, author, genre and ISBN are required")
                return
            
            try:
                year = int(year_str)
                if year < 1000 or year > datetime.now().year:
                    error_label.configure(text=f"Invalid year. Must be between 1000 and {datetime.now().year}")
                    return
            except ValueError:
                error_label.configure(text="Year must be a valid number")
                return
            
            try:
                copies = int(copies_str)
                if copies < 1:
                    error_label.configure(text="Total copies must be at least 1")
                    return
            except ValueError:
                error_label.configure(text="Total copies must be a valid number")
                return
            
            # Save/update the book
            if book_id:  # Update existing book
                success, message = update_book(book_id, title, author, genre, isbn, year, copies, description)
            else:  # Add new book
                success, message = add_book(title, author, genre, isbn, year, copies, description)
            
            if success:
                dialog.destroy()
                self.populate_books_table()  # Refresh the table
                messagebox.showinfo("Success", message)
            else:
                error_label.configure(text=message)
        
        save_button = ctk.CTkButton(
            button_frame,
            text="Save" if book_id is None else "Update",
            font=ctk.CTkFont(size=14),
            fg_color="#116636",
            hover_color="#0d4f29",
            width=100,
            height=35,
            command=save_book
        )
        save_button.pack(side="right", padx=5)
    
    def confirm_delete_book(self, book_id):
        """Show confirmation dialog before deleting a book"""
        # Find book title
        book_title = ""
        for item in self.books_tree.get_children():
            values = self.books_tree.item(item, 'values')
            if str(values[0]) == str(book_id):
                book_title = values[1]
                break
        
        result = messagebox.askyesno(
            "Confirm Delete", 
            f"Are you sure you want to delete the book:\n\n{book_title}?\n\nThis action cannot be undone."
        )
        
        if result:
            success, message = delete_book(book_id)
            if success:
                messagebox.showinfo("Success", message)
                self.populate_books_table()  # Refresh the table
            else:
                messagebox.showerror("Error", message)
    
    def show_users(self):
        """Show the user management page"""
        self.highlight_active_menu("👥 Manage Users")
        
        # Clear content area
        for widget in self.content.winfo_children():
            widget.destroy()
        
        # Create user management title
        title = ctk.CTkLabel(
            self.content, 
            text="User Management",
            font=ctk.CTkFont(size=24, weight="bold"),
            anchor="w"
        )
        title.pack(anchor="w", padx=30, pady=(20, 10))
        
        # Search and Add User Bar
        action_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        action_frame.pack(fill="x", padx=30, pady=(10, 20))
        
        # Search box
        search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(
            action_frame,
            width=400,
            height=40,
            placeholder_text="Search by name or email",
            textvariable=search_var
        )
        search_entry.pack(side="left")
        
        def perform_search():
            search_term = search_var.get()
            self.populate_users_table(search_term)
        
        search_button = ctk.CTkButton(
            action_frame,
            text="🔍 Search",
            width=120,
            height=40,
            fg_color="#116636",
            hover_color="#0d4f29",
            command=perform_search
        )
        search_button.pack(side="left", padx=(10, 0))
        
        # Add New User Button
        add_button = ctk.CTkButton(
            action_frame,
            text="+ Add New User",
            width=150,
            height=40,
            fg_color="#2196f3",
            hover_color="#1976d2",
            command=self.show_user_form
        )
        add_button.pack(side="right")
        
        # Bind Enter key to search
        search_entry.bind("<Return>", lambda event: perform_search())
        
        # Users Table
        table_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        
        # Style for treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="white", fieldbackground="white", foreground="black")
        style.configure("Treeview.Heading", background="#f0f0f0", foreground="black", font=("Arial", 10, "bold"))
        style.map("Treeview", background=[("selected", "#116636")], foreground=[("selected", "white")])
        
        # Table columns
        self.users_columns = ("ID", "First Name", "Last Name", "Email", "Role", "Registration Date", "Actions")
        
        # Create treeview
        self.users_tree = ttk.Treeview(
            table_frame, 
            columns=self.users_columns, 
            show="headings", 
            height=20,
            selectmode="browse"
        )
        self.users_tree.pack(side="left", fill="both", expand=True)
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.users_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.users_tree.configure(yscrollcommand=scrollbar.set)
        
        # Configure column widths and headings
        column_widths = {
            "ID": 50,
            "First Name": 120,
            "Last Name": 120,
            "Email": 200,
            "Role": 100,
            "Registration Date": 120,
            "Actions": 120
        }
        
        for col in self.users_columns:
            self.users_tree.heading(col, text=col)
            self.users_tree.column(col, width=column_widths.get(col, 100), anchor="w" if col != "Actions" else "center")
        
        # Initial load of users
        self.populate_users_table()
    
    def populate_users_table(self, search_term=""):
        """Populate the users table with data"""
        # Clear existing data
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        
        # Get users data
        users = get_users(search_term)
        
        # Insert users into table
        for user in users:
            reg_date = user['registration_date']
            if isinstance(reg_date, datetime):
                reg_date = reg_date.strftime('%Y-%m-%d')
            
            item_id = self.users_tree.insert("", "end", values=(
                user['user_id'],
                user['first_name'],
                user['last_name'],
                user['email'],
                user['role'],
                reg_date,
                ""  # Actions column will be filled with buttons
            ))
            
        # Add buttons to the Actions column
        self.add_user_action_buttons()
    
    def add_user_action_buttons(self):
        """Add edit and delete buttons to the users table"""
        for item in self.users_tree.get_children():
            # Get the user ID
            user_id = self.users_tree.item(item, 'values')[0]
            
            # Get bounding box for action column
            col_idx = self.users_columns.index("Actions")
            bbox = self.users_tree.bbox(item, column=col_idx)
            
            if bbox:  # If visible
                # Create a frame for the buttons
                button_frame = ctk.CTkFrame(self.users_tree, fg_color="transparent")
                button_frame.place(x=bbox[0], y=bbox[1], width=120, height=bbox[3])
                
                # Edit button
                edit_button = ctk.CTkButton(
                    button_frame, 
                    text="Edit",
                    width=50,
                    height=20,
                    fg_color="#FFA500",
                    hover_color="#FF8C00",
                    corner_radius=4,
                    font=ctk.CTkFont(size=10),
                    command=lambda u_id=user_id: self.show_user_form(u_id)
                )
                edit_button.pack(side="left", padx=(0, 5))
                
                # Delete button
                delete_button = ctk.CTkButton(
                    button_frame, 
                    text="Delete",
                    width=50,
                    height=20,
                    fg_color="#FF5252",
                    hover_color="#D32F2F",
                    corner_radius=4,
                    font=ctk.CTkFont(size=10),
                    command=lambda u_id=user_id: self.confirm_delete_user(u_id)
                )
                delete_button.pack(side="left")
    
    def show_user_form(self, user_id=None):
        """Show form to add or edit a user"""
        # Create a dialog window
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Add New User" if user_id is None else "Edit User")
        dialog.geometry("500x470")
        dialog.resizable(False, False)
        dialog.grab_set()  # Make it modal
        
        # Center the dialog on screen
        dialog_x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 250
        dialog_y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 235
        dialog.geometry(f"+{dialog_x}+{dialog_y}")
        
        # User data (empty for new, populated for edit)
        user_data = {}
        if user_id:
            # Fetch user data for editing
            users = get_users()
            for user in users:
                if str(user['user_id']) == str(user_id):
                    user_data = user
                    break
        
        # Form frame
        form_frame = ctk.CTkFrame(dialog)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        form_title = ctk.CTkLabel(
            form_frame,
            text="Add New User" if user_id is None else "Edit User",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        form_title.pack(pady=(0, 20))
        
        # Input fields frame
        input_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        input_frame.pack(fill="x", pady=10)
        
        # Configure grid
        input_frame.grid_columnconfigure(1, weight=1)
        
        # First Name field
        ctk.CTkLabel(input_frame, text="First Name:", anchor="e", width=100).grid(row=0, column=0, padx=(20, 10), pady=10, sticky="e")
        first_name_entry = ctk.CTkEntry(input_frame, width=300, height=30)
        first_name_entry.grid(row=0, column=1, padx=(0, 20), pady=10, sticky="ew")
        if 'first_name' in user_data:
            first_name_entry.insert(0, user_data['first_name'])
        
        # Last Name field
        ctk.CTkLabel(input_frame, text="Last Name:", anchor="e", width=100).grid(row=1, column=0, padx=(20, 10), pady=10, sticky="e")
        last_name_entry = ctk.CTkEntry(input_frame, width=300, height=30)
        last_name_entry.grid(row=1, column=1, padx=(0, 20), pady=10, sticky="ew")
        if 'last_name' in user_data:
            last_name_entry.insert(0, user_data['last_name'])
        
        # Email field
        ctk.CTkLabel(input_frame, text="Email:", anchor="e", width=100).grid(row=2, column=0, padx=(20, 10), pady=10, sticky="e")
        email_entry = ctk.CTkEntry(input_frame, width=300, height=30)
        email_entry.grid(row=2, column=1, padx=(0, 20), pady=10, sticky="ew")
        if 'email' in user_data:
            email_entry.insert(0, user_data['email'])
        
        # Role field
        ctk.CTkLabel(input_frame, text="Role:", anchor="e", width=100).grid(row=3, column=0, padx=(20, 10), pady=10, sticky="e")
        
        role_var = tk.StringVar(value=user_data.get('role', 'member'))
        role_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        role_frame.grid(row=3, column=1, padx=(0, 20), pady=10, sticky="ew")
        
        member_radio = ctk.CTkRadioButton(
            role_frame, 
            text="Member", 
            variable=role_var, 
            value="member",
            fg_color="#116636"
        )
        member_radio.pack(side="left", padx=(0, 20))
        
        admin_radio = ctk.CTkRadioButton(
            role_frame, 
            text="Admin", 
            variable=role_var, 
            value="admin",
            fg_color="#116636"
        )
        admin_radio.pack(side="left")
        
        # Password field (required for new users)
        ctk.CTkLabel(input_frame, text="Password:", anchor="e", width=100).grid(row=4, column=0, padx=(20, 10), pady=10, sticky="e")
        password_entry = ctk.CTkEntry(input_frame, width=300, height=30, show="•")
        password_entry.grid(row=4, column=1, padx=(0, 20), pady=10, sticky="ew")
        
        # Password note
        pass_note = "Password required for new users" if user_id is None else "Leave blank to keep current password"
        pass_note_label = ctk.CTkLabel(
            input_frame, 
            text=pass_note, 
            font=ctk.CTkFont(size=10), 
            text_color="gray"
        )
        pass_note_label.grid(row=5, column=1, padx=(0, 20), pady=(0, 10), sticky="w")
        
        # Error message label
        error_label = ctk.CTkLabel(
            form_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#d32f2f"
        )
        error_label.pack(pady=(10, 0))
        
        # Button frame
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(20, 0))
        
        # Cancel button
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            font=ctk.CTkFont(size=14),
            fg_color="#f0f0f0",
            text_color="#333333",
            hover_color="#e0e0e0",
            width=100,
            height=35,
            command=dialog.destroy
        )
        cancel_button.pack(side="left", padx=5)
        
        # Save/Update button
        def save_user():
            # Validate input
            first_name = first_name_entry.get().strip()
            last_name = last_name_entry.get().strip()
            email = email_entry.get().strip()
            role = role_var.get()
            password = password_entry.get()
            
            # Basic validation
            if not first_name or not last_name or not email:
                error_label.configure(text="First name, last name and email are required")
                return
            
            
        # Create dashboard title
        title = ctk.CTkLabel(
            self.content, 
            text="Admin Dashboard",
            font=ctk.CTkFont(size=24, weight="bold"),
            anchor="w"
        )
        title.pack(anchor="w", padx=30, pady=(20, 20))
        
        # Get dashboard statistics
        stats = get_dashboard_stats()
        
        # Summary Cards
        cards_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        cards_frame.pack(fill="x", padx=30, pady=(0, 20))
        
        # Configure grid columns
        for i in range(4):
            cards_frame.grid_columnconfigure(i, weight=1)
        
        # Card data and icons
        card_data = [
            ("Total Books", f"{stats.get('total_books', 0):,}", "📚"),
            ("Books Borrowed", f"{stats.get('borrowed_books', 0):,}", "📖"),
            ("Registered Users", f"{stats.get('total_users', 0):,}", "👥"),
            ("Pending Fines", f"${stats.get('pending_fines', 0):,.2f}", "💰")
        ]
        
        # Create summary cards
        for i, (title, value, icon) in enumerate(card_data):
            card = ctk.CTkFrame(cards_frame, fg_color="white", corner_radius=10)
            card.grid(row=0, column=i, padx=10, pady=10, sticky="nsew", ipadx=15, ipady=15)
            
            # Icon and title in same frame
            header_frame = ctk.CTkFrame(card, fg_color="transparent")
            header_frame.pack(anchor="w", padx=15, pady=(15, 5))
            
            icon_label = ctk.CTkLabel(
                header_frame,
                text=icon,
                font=ctk.CTkFont(size=20),
                text_color="#116636"
            )
            icon_label.pack(side="left", padx=(0, 5))
            
            title_label = ctk.CTkLabel(
                header_frame,
                text=title,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#116636"
            )
            title_label.pack(side="left")
            
            # Value
            value_label = ctk.CTkLabel(
                card,
                text=value,
                font=ctk.CTkFont(size=24, weight="bold"),
                text_color="#333333"
            )
            value_label.pack(anchor="w", padx=15, pady=(5, 15))
        
        # Create two columns for bottom section
        bottom_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        bottom_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(1, weight=1)
        
        # Recent Loans Section
        recent_loans_frame = ctk.CTkFrame(bottom_frame, fg_color="white", corner_radius=10)
        recent_loans_frame.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="nsew")
        
        recent_title = ctk.CTkLabel(
            recent_loans_frame,
            text="Recent Loans",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        recent_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # Recent loans table
        loans_columns = ("Book", "User", "Loan Date", "Due Date")
        loans_frame = ctk.CTkFrame(recent_loans_frame, fg_color="transparent")
        loans_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Style for treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="white", fieldbackground="white", foreground="black")
        style.configure("Treeview.Heading", background="#f0f0f0", foreground="black", font=("Arial", 10, "bold"))
        style.map("Treeview", background=[("selected", "#116636")], foreground=[("selected", "white")])
        
        # Create treeview
        loans_tree = ttk.Treeview(loans_frame, columns=loans_columns, show="headings", height=8)
        loans_tree.pack(side="left", fill="both", expand=True)
        
        # Configure columns
        for col in loans_columns:
            loans_tree.heading(col, text=col)
            loans_tree.column(col, width=100)
        
        # Populate with recent loans
        for loan in stats.get('recent_loans', []):
            loans_tree.insert("", "end", values=(
                loan[0],  # Book title
                f"{loan[1]} {loan[2]}",  # User name
                loan[3].strftime('%b %d, %Y') if isinstance(loan[3], datetime) else loan[3],  # Loan date
                loan[4].strftime('%b %d, %Y') if isinstance(loan[4], datetime) else loan[4]   # Due date
            ))
        
        # Genres Section
        genres_frame = ctk.CTkFrame(bottom_frame, fg_color="white", corner_radius=10)
        genres_frame.grid(row=0, column=1, padx=(10, 0), pady=10, sticky="nsew")
        
        genres_title = ctk.CTkLabel(
            genres_frame,
            text="Books by Genre",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        genres_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # Create canvas for the bar chart
        chart_frame = ctk.CTkFrame(genres_frame, fg_color="transparent")
        chart_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Simple bar chart implementation
        bar_canvas = ctk.CTkCanvas(chart_frame, bg="white", highlightthickness=0)
        bar_canvas.pack(fill="both", expand=True)
        
        # Get genre data
        genres = stats.get('genres', [])
        if genres:
            # Find the maximum count for scaling
            max_count = max(g[1] for g in genres)
            bar_width = 80
            spacing = 40
            start_x = 50
            max_height = 200
            
            # Draw bars
            for i, (genre, count) in enumerate(genres):
                # Calculate positions
                x = start_x + i * (bar_width + spacing)
                y_bottom = 250
                bar_height = (count / max_count) * max_height
                y_top = y_bottom - bar_height
                
                # Draw bar
                bar_canvas.create_rectangle(
                    x, y_bottom, x + bar_width, y_top,
                    fill="#116636", outline=""
                )
                
                # Draw genre label
                bar_canvas.create_text(
                    x + bar_width/2, y_bottom + 20,
                    text=genre, font=("Arial", 9), fill="#333333"
                )
                
                # Draw count label
                bar_canvas.create_text(
                    x + bar_width/2, y_top - 15,
                    text=str(count), font=("Arial", 10, "bold"), fill="#333333"
                )
    
    def show_books(self):
        """Show the book management page"""
        self.highlight_active_menu("📚 Manage Books")
        
        # Clear content area
        for widget in self.content.winfo_children():
            widget.destroy()
        # Email validation
            if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
                error_label.configure(text="Please enter a valid email address")
                return
            
            # Password required for new users
            if not user_id and not password:
                error_label.configure(text="Password is required for new users")
                return
            
            # Save/update the user
            if user_id:  # Update existing user
                success, message = update_user(user_id, first_name, last_name, email, role, password if password else None)
            else:  # Add new user
                success, message = create_user(first_name, last_name, email, password, role)
            
            if success:
                dialog.destroy()
                self.populate_users_table()  # Refresh the table
                messagebox.showinfo("Success", message)
            else:
                error_label.configure(text=message)
        
        save_button = ctk.CTkButton(
            button_frame,
            text="Save" if user_id is None else "Update",
            font=ctk.CTkFont(size=14),
            fg_color="#116636",
            hover_color="#0d4f29",
            width=100,
            height=35,
            command=save_user
        )
        save_button.pack(side="right", padx=5)
    
    def confirm_delete_user(self, user_id):
        """Show confirmation dialog before deleting a user"""
        # Find user name
        user_name = ""
        for item in self.users_tree.get_children():
            values = self.users_tree.item(item, 'values')
            if str(values[0]) == str(user_id):
                user_name = f"{values[1]} {values[2]}"
                break
        
        result = messagebox.askyesno(
            "Confirm Delete", 
            f"Are you sure you want to delete the user:\n\n{user_name}?\n\nThis action cannot be undone."
        )
        
        if result:
            success, message = delete_user(user_id)
            if success:
                messagebox.showinfo("Success", message)
                self.populate_users_table()  # Refresh the table
            else:
                messagebox.showerror("Error", message)
    
    def show_fines(self):
        """Show the fines management page"""
        self.highlight_active_menu("💰 Manage Fines")
        
        # Clear content area
        for widget in self.content.winfo_children():
            widget.destroy()
        
        # Create fines management title
        title = ctk.CTkLabel(
            self.content, 
            text="Fines Management",
            font=ctk.CTkFont(size=24, weight="bold"),
            anchor="w"
        )
        title.pack(anchor="w", padx=30, pady=(20, 20))
        
        # Fines statistics frame
        stats_frame = ctk.CTkFrame(self.content, fg_color="white", corner_radius=10)
        stats_frame.pack(fill="x", padx=30, pady=(0, 20))
        
        # Get dashboard stats for fines info
        stats = get_dashboard_stats()
        
        # Pending fines amount
        pending_fines = stats.get('pending_fines', 0)
        
        # Create stats display
        stats_label = ctk.CTkLabel(
            stats_frame,
            text="Outstanding Fines:",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        stats_label.pack(side="left", padx=20, pady=20)
        
        amount_label = ctk.CTkLabel(
            stats_frame,
            text=f"${pending_fines:.2f}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#d32f2f",
            anchor="e"
        )
        amount_label.pack(side="right", padx=20, pady=20)
        
        # Functions to get fine data from database
        def get_all_fines():
            """Get all fines information"""
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
                        f.paid,
                        f.payment_date,
                        b.title,
                        u.first_name,
                        u.last_name,
                        u.email,
                        l.due_date,
                        l.return_date
                    FROM 
                        Fines f
                    JOIN 
                        Loans l ON f.loan_id = l.loan_id
                    JOIN 
                        Books b ON l.book_id = b.book_id
                    JOIN 
                        Users u ON l.user_id = u.user_id
                    ORDER BY 
                        f.paid, f.fine_id DESC
                """)
                
                return cursor.fetchall()
            except mysql.connector.Error as err:
                messagebox.showerror("Database Error", str(err))
                return []
            finally:
                if connection.is_connected():
                    cursor.close()
                    connection.close()
        
        # Create tabs for different views
        tabview = ctk.CTkTabview(self.content, height=500)
        tabview.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        
        # Add tabs
        all_tab = tabview.add("All Fines")
        pending_tab = tabview.add("Pending Fines")
        paid_tab = tabview.add("Paid Fines")
        
        # Configure tabs to expand
        for tab in [all_tab, pending_tab, paid_tab]:
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure(0, weight=1)
        
        # Style for treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="white", fieldbackground="white", foreground="black")
        style.configure("Treeview.Heading", background="#f0f0f0", foreground="black", font=("Arial", 10, "bold"))
        style.map("Treeview", background=[("selected", "#116636")], foreground=[("selected", "white")])
        
        # Table columns
        fines_columns = ("ID", "Book", "User", "Email", "Amount", "Description", "Status", "Date")
        column_widths = {
            "ID": 50,
            "Book": 200,
            "User": 150,
            "Email": 200,
            "Amount": 80,
            "Description": 200,
            "Status": 100,
            "Date": 120
        }
        
        # Create tables for each tab
        tables = {}
        
        for tab_name, tab in [("all", all_tab), ("pending", pending_tab), ("paid", paid_tab)]:
            # Create frame for table
            table_frame = ctk.CTkFrame(tab, fg_color="transparent")
            table_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
            
            # Create treeview
            tree = ttk.Treeview(
                table_frame, 
                columns=fines_columns, 
                show="headings", 
                height=20,
                selectmode="browse"
            )
            tree.pack(side="left", fill="both", expand=True)
            
            # Add a scrollbar
            scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
            scrollbar.pack(side="right", fill="y")
            tree.configure(yscrollcommand=scrollbar.set)
            
            # Configure column widths and headings
            for col in fines_columns:
                tree.heading(col, text=col)
                tree.column(col, width=column_widths.get(col, 100), anchor="w")
            
            # Store in dictionary
            tables[tab_name] = tree
        
        # Function to populate tables
        def populate_fines_tables():
            # Clear existing data
            for tree in tables.values():
                for item in tree.get_children():
                    tree.delete(item)
            
            # Get fines data
            fines = get_all_fines()
            
            # Process each fine
            for fine in fines:
                status = "Paid" if fine['paid'] else "Pending"
                date = fine['payment_date'] if fine['paid'] else fine['due_date']
                
                if isinstance(date, datetime):
                    date = date.strftime('%Y-%m-%d')
                
                # Create row data
                row_data = (
                    fine['fine_id'],
                    fine['title'],
                    f"{fine['first_name']} {fine['last_name']}",
                    fine['email'],
                    f"${fine['amount']:.2f}",
                    fine['description'],
                    status,
                    date
                )
                
                # Insert into all fines table
                tables["all"].insert("", "end", values=row_data, tags=(status.lower(),))
                
                # Insert into appropriate status table
                if fine['paid']:
                    tables["paid"].insert("", "end", values=row_data, tags=("paid",))
                else:
                    tables["pending"].insert("", "end", values=row_data, tags=("pending",))
            
            # Configure tag colors
            for tree in tables.values():
                tree.tag_configure("paid", background="#E8F5E9")
                tree.tag_configure("pending", background="#FFEBEE")
        
        # Initial population of tables
        populate_fines_tables()
        
        # Refresh button
        refresh_btn = ctk.CTkButton(
            self.content,
            text="Refresh Data",
            font=ctk.CTkFont(size=14),
            fg_color="#116636",
            hover_color="#0d4f29",
            width=120,
            height=35,
            command=populate_fines_tables
        )
        refresh_btn.place(relx=0.95, rely=0.07, anchor="e")
    
    def logout(self):
        """Logout and return to login screen"""
        # Clear the admin session
        clear_session()
        
        # Show login screen
        self.show_login()

# ------------------- Main Application -------------------
if __name__ == "__main__":
    try:
        root = ctk.CTk()
        app = LibraryAdminApp(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Application Error", f"An error occurred: {e}")

        # Create dashboard title
        title = ctk.CTkLabel(
            self.content, 
            text="Admin Dashboard",
            font=ctk.CTkFont(size=24, weight="bold"),
            anchor="w"
        )
        title.pack(anchor="w", padx=30, pady=(20, 20))
        
        # Get dashboard statistics
        stats = get_dashboard_stats()
        
        # Summary Cards
        cards_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        cards_frame.pack(fill="x", padx=30, pady=(0, 20))
        
        # Configure grid columns
        for i in range(4):
            cards_frame.grid_columnconfigure(i, weight=1)
        
        # Card data and icons
        card_data = [
            ("Total Books", f"{stats.get('total_books', 0):,}", "📚"),
            ("Books Borrowed", f"{stats.get('borrowed_books', 0):,}", "📖"),
            ("Registered Users", f"{stats.get('total_users', 0):,}", "👥"),
            ("Pending Fines", f"${stats.get('pending_fines', 0):,.2f}", "💰")
        ]
        
        # Create summary cards
        for i, (title, value, icon) in enumerate(card_data):
            card = ctk.CTkFrame(cards_frame, fg_color="white", corner_radius=10)
            card.grid(row=0, column=i, padx=10, pady=10, sticky="nsew", ipadx=15, ipady=15)
            
            # Icon and title in same frame
            header_frame = ctk.CTkFrame(card, fg_color="transparent")
            header_frame.pack(anchor="w", padx=15, pady=(15, 5))
            
            icon_label = ctk.CTkLabel(
                header_frame,
                text=icon,
                font=ctk.CTkFont(size=20),
                text_color="#116636"
            )
            icon_label.pack(side="left", padx=(0, 5))
            
            title_label = ctk.CTkLabel(
                header_frame,
                text=title,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#116636"
            )
            title_label.pack(side="left")
            
            # Value
            value_label = ctk.CTkLabel(
                card,
                text=value,
                font=ctk.CTkFont(size=24, weight="bold"),
                text_color="#333333"
            )
            value_label.pack(anchor="w", padx=15, pady=(5, 15))
        
        # Create two columns for bottom section
        bottom_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        bottom_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(1, weight=1)
        
        # Recent Loans Section
        recent_loans_frame = ctk.CTkFrame(bottom_frame, fg_color="white", corner_radius=10)
        recent_loans_frame.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="nsew")
        
        recent_title = ctk.CTkLabel(
            recent_loans_frame,
            text="Recent Loans",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        recent_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # Recent loans table
        loans_columns = ("Book", "User", "Loan Date", "Due Date")
        loans_frame = ctk.CTkFrame(recent_loans_frame, fg_color="transparent")
        loans_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Style for treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="white", fieldbackground="white", foreground="black")
        style.configure("Treeview.Heading", background="#f0f0f0", foreground="black", font=("Arial", 10, "bold"))
        style.map("Treeview", background=[("selected", "#116636")], foreground=[("selected", "white")])
        
        # Create treeview
        loans_tree = ttk.Treeview(loans_frame, columns=loans_columns, show="headings", height=8)
        loans_tree.pack(side="left", fill="both", expand=True)
        
        # Configure columns
        for col in loans_columns:
            loans_tree.heading(col, text=col)
            loans_tree.column(col, width=100)
        
        # Populate with recent loans
        for loan in stats.get('recent_loans', []):
            loans_tree.insert("", "end", values=(
                loan[0],  # Book title
                f"{loan[1]} {loan[2]}",  # User name
                loan[3].strftime('%b %d, %Y') if isinstance(loan[3], datetime) else loan[3],  # Loan date
                loan[4].strftime('%b %d, %Y') if isinstance(loan[4], datetime) else loan[4]   # Due date
            ))
        
        # Genres Section
        genres_frame = ctk.CTkFrame(bottom_frame, fg_color="white", corner_radius=10)
        genres_frame.grid(row=0, column=1, padx=(10, 0), pady=10, sticky="nsew")
        
        genres_title = ctk.CTkLabel(
            genres_frame,
            text="Books by Genre",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        genres_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # Create canvas for the bar chart
        chart_frame = ctk.CTkFrame(genres_frame, fg_color="transparent")
        chart_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Simple bar chart implementation
        bar_canvas = ctk.CTkCanvas(chart_frame, bg="white", highlightthickness=0)
        bar_canvas.pack(fill="both", expand=True)
        
        # Get genre data
        genres = stats.get('genres', [])
        if genres:
            # Find the maximum count for scaling
            max_count = max(g[1] for g in genres)
            bar_width = 80
            spacing = 40
            start_x = 50
            max_height = 200
            
            # Draw bars
            for i, (genre, count) in enumerate(genres):
                # Calculate positions
                x = start_x + i * (bar_width + spacing)
                y_bottom = 250
                bar_height = (count / max_count) * max_height
                y_top = y_bottom - bar_height
                
                # Draw bar
                bar_canvas.create_rectangle(
                    x, y_bottom, x + bar_width, y_top,
                    fill="#116636", outline=""
                )
                
                # Draw genre label
                bar_canvas.create_text(
                    x + bar_width/2, y_bottom + 20,
                    text=genre, font=("Arial", 9), fill="#333333"
                )
                
                # Draw count label
                bar_canvas.create_text(
                    x + bar_width/2, y_top - 15,
                    text=str(count), font=("Arial", 10, "bold"), fill="#333333"
                )
    
    def show_books(self):
        """Show the book management page"""
        self.highlight_active_menu("📚 Manage Books")
        
        # Clear content area
        for widget in self.content.winfo_children():
            widget.destroy()