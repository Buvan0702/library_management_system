
import customtkinter as ctk
from tkinter import ttk, messagebox
import tkinter as tk
import mysql.connector
import json
import os
from datetime import datetime, timedelta
from PIL import Image, ImageTk
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

# ------------------- Database Verification -------------------
def verify_database():
    """Verify that the database and tables exist"""
    try:
        connection = connect_db()
        if not connection:
            return False
        
        cursor = connection.cursor()
        
        # Check if tables exist
        tables = ["Books", "Users", "Loans", "Fines"]
        for table in tables:
            cursor.execute(f"SHOW TABLES LIKE '{table}'")
            if not cursor.fetchone():
                messagebox.showerror("Database Error", f"Table '{table}' not found. Please run main.py first.")
                return False
        
        return True
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Database verification failed: {err}")
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

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

def save_session(user_data):
    """Save user data to session file"""
    with open(SESSION_FILE, 'w') as f:
        json.dump(user_data, f)

def clear_session():
    """Delete the session file"""
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

# ------------------- Utility Functions -------------------
def format_date(date_str):
    """Format date string to more readable format"""
    try:
        if isinstance(date_str, datetime):
            return date_str.strftime('%b %d, %Y')
        
        date_obj = datetime.strptime(str(date_str), '%Y-%m-%d')
        return date_obj.strftime('%b %d, %Y')
    except:
        return str(date_str)

def calculate_fine(due_date_str):
    """Calculate fine if book is overdue"""
    try:
        if isinstance(due_date_str, datetime):
            due_date = due_date_str
        else:
            due_date = datetime.strptime(str(due_date_str), '%Y-%m-%d')
        
        today = datetime.now()
        
        if today > due_date:
            days_overdue = (today - due_date).days
            fine = days_overdue * 0.50  # $0.50 per day
            return f"${fine:.2f}"
        return "$0.00"
    except Exception as e:
        print(f"Error calculating fine: {e}")
        return "$0.00"

def is_overdue(due_date_str):
    """Check if a book is overdue"""
    try:
        if isinstance(due_date_str, datetime):
            due_date = due_date_str
        else:
            due_date = datetime.strptime(str(due_date_str), '%Y-%m-%d')
        
        return datetime.now() > due_date
    except Exception as e:
        print(f"Error checking overdue: {e}")
        return False

# ------------------- Book Functions -------------------
def search_books(query=""):
    """Search for books based on query, or get all books if query is empty"""
    connection = connect_db()
    if not connection:
        print("Database connection failed in search_books")
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        if query and len(query.strip()) > 0:
            # Search with filter
            search_query = f"%{query}%"
            
            cursor.execute("""
                SELECT 
                    b.book_id, 
                    b.title, 
                    b.author, 
                    b.isbn,
                    b.publication_year,
                    b.genre,
                    b.available_copies
                FROM 
                    Books b
                WHERE 
                    b.title LIKE %s OR 
                    b.author LIKE %s OR 
                    b.genre LIKE %s OR
                    b.isbn LIKE %s
                ORDER BY 
                    b.title
            """, (search_query, search_query, search_query, search_query))
        else:
            # Get all books
            cursor.execute("""
                SELECT 
                    b.book_id, 
                    b.title, 
                    b.author, 
                    b.isbn,
                    b.publication_year,
                    b.genre,
                    b.available_copies
                FROM 
                    Books b
                ORDER BY 
                    b.title
                LIMIT 20
            """)
        
        results = cursor.fetchall()
        print(f"Search results: {len(results)} books found")
        if len(results) > 0:
            print(f"Sample book: {results[0]}")
        return results
    except mysql.connector.Error as err:
        print(f"Database Error in search_books: {err}")
        messagebox.showerror("Database Error", str(err))
        return []
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def get_user_borrowed_books(user_id):
    """Get all books borrowed by a user"""
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
                l.return_date
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
        
        results = cursor.fetchall()
        print(f"Borrowed books: {len(results)} books found for user {user_id}")
        return results
    except mysql.connector.Error as err:
        print(f"Error getting borrowed books: {err}")
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
        
        # First get the book_id for this loan to update available copies
        cursor.execute("SELECT book_id, due_date FROM Loans WHERE loan_id = %s", (loan_id,))
        result = cursor.fetchone()
        
        if not result:
            print(f"No loan found with ID {loan_id}")
            return False
        
        book_id, due_date = result
        
        # Update loan return date
        cursor.execute(
            "UPDATE Loans SET return_date = CURDATE() WHERE loan_id = %s AND user_id = %s", 
            (loan_id, user_id)
        )
        
        # Check if any rows were affected
        if cursor.rowcount == 0:
            print(f"No rows updated for loan {loan_id}")
            return False
        
        # Increment available copies
        cursor.execute(
            "UPDATE Books SET available_copies = available_copies + 1 WHERE book_id = %s", 
            (book_id,)
        )
        
        # Check if the book is overdue and create fine if needed
        if is_overdue(due_date):
            days_overdue = (datetime.now() - due_date).days if isinstance(due_date, datetime) else \
                          (datetime.now() - datetime.strptime(str(due_date), '%Y-%m-%d')).days
                          
            fine_amount = days_overdue * 0.50  # $0.50 per day
            
            # Create fine record
            cursor.execute(
                "INSERT INTO Fines (loan_id, amount, description, paid) VALUES (%s, %s, %s, 0)",
                (loan_id, fine_amount, f"Late return fine: {days_overdue} days")
            )
        
        connection.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Error returning book: {err}")
        messagebox.showerror("Database Error", str(err))
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def borrow_book(book_id, user_id):
    """Borrow a book"""
    connection = connect_db()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Check if user already has this book
        cursor.execute(
            "SELECT COUNT(*) FROM Loans WHERE book_id = %s AND user_id = %s AND return_date IS NULL", 
            (book_id, user_id)
        )
        if cursor.fetchone()[0] > 0:
            messagebox.showinfo("Already Borrowed", "You already have this book borrowed.")
            return False
        
        # Check if book has available copies
        cursor.execute("SELECT available_copies FROM Books WHERE book_id = %s", (book_id,))
        result = cursor.fetchone()
        
        if not result:
            print(f"No book found with ID {book_id}")
            return False
        
        available_copies = result[0]
        
        if available_copies > 0:
            # Create loan record with due date 14 days from now
            due_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
            
            cursor.execute(
                "INSERT INTO Loans (user_id, book_id, loan_date, due_date) VALUES (%s, %s, CURDATE(), %s)", 
                (user_id, book_id, due_date)
            )
            
            # Decrement available copies
            cursor.execute(
                "UPDATE Books SET available_copies = available_copies - 1 WHERE book_id = %s", 
                (book_id,)
            )
            
            connection.commit()
            return True
        else:
            messagebox.showinfo("Not Available", "This book is currently not available for borrowing.")
            return False
    except mysql.connector.Error as err:
        print(f"Error borrowing book: {err}")
        messagebox.showerror("Database Error", str(err))
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_user_fines(user_id):
    """Get all fines for a user"""
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
                f.paid,
                f.payment_date,
                b.title
            FROM 
                Fines f
            JOIN 
                Loans l ON f.loan_id = l.loan_id
            JOIN 
                Books b ON l.book_id = b.book_id
            WHERE 
                l.user_id = %s
            ORDER BY 
                f.paid, f.fine_id DESC
        """, (user_id,))
        
        results = cursor.fetchall()
        print(f"Fines: {len(results)} fines found for user {user_id}")
        return results
    except mysql.connector.Error as err:
        print(f"Error getting fines: {err}")
        messagebox.showerror("Database Error", str(err))
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def pay_fine(fine_id, user_id):
    """Mark a fine as paid"""
    connection = connect_db()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Update fine as paid
        cursor.execute(
            """
            UPDATE Fines SET paid = 1, payment_date = CURDATE() 
            WHERE fine_id = %s AND fine_id IN (
                SELECT f.fine_id FROM Fines f 
                JOIN Loans l ON f.loan_id = l.loan_id 
                WHERE l.user_id = %s
            )
            """, 
            (fine_id, user_id)
        )
        
        connection.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as err:
        print(f"Error paying fine: {err}")
        messagebox.showerror("Database Error", str(err))
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_user_profile(user_id):
    """Get user profile information"""
    connection = connect_db()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                user_id, 
                first_name, 
                last_name, 
                email, 
                role,
                DATE_FORMAT(registration_date, '%Y-%m-%d') AS registration_date
            FROM 
                Users 
            WHERE 
                user_id = %s
        """, (user_id,))
        
        result = cursor.fetchone()
        print(f"User profile loaded for user {user_id}")
        return result
    except mysql.connector.Error as err:
        print(f"Error getting user profile: {err}")
        messagebox.showerror("Database Error", str(err))
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def update_user_profile(user_id, first_name, last_name, email, current_password=None, new_password=None):
    """Update user profile information"""
    connection = connect_db()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # If changing password, verify current password
        if current_password and new_password:
            # Hash the provided current password
            hashed_current = hashlib.sha256(current_password.encode()).hexdigest()
            
            # Check if the current password matches
            cursor.execute("SELECT password FROM Users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            
            if not result:
                print(f"No user found with ID {user_id}")
                return False
            
            stored_hash = result[0]
            
            if stored_hash != hashed_current:
                messagebox.showerror("Password Error", "Current password is incorrect.")
                return False
            
            # Hash the new password
            hashed_new = hashlib.sha256(new_password.encode()).hexdigest()
            
            # Update user with new password
            cursor.execute(
                "UPDATE Users SET first_name = %s, last_name = %s, email = %s, password = %s WHERE user_id = %s", 
                (first_name, last_name, email, hashed_new, user_id)
            )
        else:
            # Update user without changing password
            cursor.execute(
                "UPDATE Users SET first_name = %s, last_name = %s, email = %s WHERE user_id = %s", 
                (first_name, last_name, email, user_id)
            )
        
        connection.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Error updating profile: {err}")
        messagebox.showerror("Database Error", str(err))
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_user_summary(user_id):
    """Get summary data for dashboard"""
    connection = connect_db()
    if not connection:
        return {"books_borrowed": 0, "due_books": 0, "pending_fines": "$0.00"}
    
    try:
        cursor = connection.cursor()
        
        # Get count of borrowed books
        cursor.execute(
            "SELECT COUNT(*) FROM Loans WHERE user_id = %s AND return_date IS NULL", 
            (user_id,)
        )
        books_borrowed = cursor.fetchone()[0]
        
        # Get count of overdue books
        cursor.execute(
            "SELECT COUNT(*) FROM Loans WHERE user_id = %s AND return_date IS NULL AND due_date < CURDATE()", 
            (user_id,)
        )
        due_books = cursor.fetchone()[0]
        
        # Get sum of unpaid fines
        cursor.execute("""
            SELECT COALESCE(SUM(f.amount), 0) 
            FROM Fines f
            JOIN Loans l ON f.loan_id = l.loan_id
            WHERE l.user_id = %s AND f.paid = 0
        """, (user_id,))
        pending_fines = cursor.fetchone()[0]
        
        print(f"User summary loaded: {books_borrowed} books, {due_books} overdue, ${pending_fines:.2f} in fines")
        
        return {
            "books_borrowed": books_borrowed,
            "due_books": due_books,
            "pending_fines": f"${pending_fines:.2f}"
        }
    except mysql.connector.Error as err:
        print(f"Error getting user summary: {err}")
        messagebox.showerror("Database Error", str(err))
        return {"books_borrowed": 0, "due_books": 0, "pending_fines": "$0.00"}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- Initialize Application -------------------
class LibraryApp:
    def __init__(self, root, start_page=None):
        self.root = root
        self.root.title("Library Management System - User Dashboard")
        self.root.geometry("1200x700")
        
        # Set appearance mode and default color theme
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")
        
        # Verify database first
        if not verify_database():
            messagebox.showerror("Database Error", "Database verification failed. Please run main.py first.")
            self.root.destroy()
            try:
                os.system("python main.py")
            except:
                pass
            return
        
        # Load user session
        self.user = load_session()
        if not self.user:
            messagebox.showerror("Session Error", "No active user session found.")
            self.logout()
            return
        
        print(f"User session loaded successfully: {self.user['first_name']} {self.user['last_name']}")
        
        # Initialize frames dictionary to keep track of different pages
        self.frames = {}
        
        # Create main grid layout
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Create sidebar
        self.create_sidebar()
        
        # Create main content area
        self.create_main_content()
        
        # Show appropriate start page
        if start_page == "borrowed":
            self.show_borrowed_books()
        elif start_page == "fines":
            self.show_fines()
        elif start_page == "profile":
            self.show_profile()
        else:
            # By default, show dashboard
            self.show_dashboard()
    
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
        self.menu_buttons = {}
        menu_items = [
            ("🏠 Dashboard", self.show_dashboard),
            ("🔍 Search Books", self.show_search_books),
            ("📖 My Borrowed Books", self.show_borrowed_books),
            ("💰 Fines & Fees", self.show_fines),
            ("👤 My Profile", self.show_profile),
            ("🚪 Logout", self.logout)
        ]

        for text, command in menu_items:
            button = ctk.CTkButton(sidebar, text=text, font=ctk.CTkFont(size=12), 
                                  fg_color="transparent", text_color="white", anchor="w",
                                  hover_color="#0d4f29", corner_radius=0, height=40,
                                  command=command)
            button.pack(fill="x", pady=2)
            self.menu_buttons[text] = button
    
    def highlight_active_menu(self, active_text):
        """Highlight the active menu button"""
        for text, button in self.menu_buttons.items():
            if text == active_text:
                button.configure(fg_color="#0d4f29")
            else:
                button.configure(fg_color="transparent")
    
    def create_main_content(self):
        """Create the main content area"""
        self.main_frame = ctk.CTkFrame(self.root, fg_color="#f0f5f0", corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
    
    def clear_main_frame(self):
        """Clear all widgets from the main frame"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
    
    # ------------------- Page Navigation -------------------
    def show_dashboard(self):
        """Show the dashboard page"""
        print("Loading dashboard...")
        self.clear_main_frame()
        self.highlight_active_menu("🏠 Dashboard")
        
        # Dashboard Title
        title_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        dash_title = ctk.CTkLabel(title_frame, text="Your Library Dashboard", 
                                 font=ctk.CTkFont(size=20, weight="bold"))
        dash_title.pack(pady=10)

        # Separator line
        separator_frame = ctk.CTkFrame(self.main_frame, height=1, fg_color="#d1d1d1")
        separator_frame.grid(row=1, column=0, sticky="ew", pady=5)
        
        # Get user summary data
        summary_data = get_user_summary(self.user['user_id'])
        
        # Dashboard Summary Boxes
        summary_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        summary_frame.grid(row=2, column=0, sticky="ew", pady=20)
        summary_frame.grid_columnconfigure(0, weight=1)
        summary_frame.grid_columnconfigure(1, weight=1)
        summary_frame.grid_columnconfigure(2, weight=1)

        summary_boxes = [
            ("Books Borrowed", str(summary_data["books_borrowed"])),
            ("Due Books", str(summary_data["due_books"])),
            ("Pending Fines", summary_data["pending_fines"])
        ]

        for i, (title, value) in enumerate(summary_boxes):
            box_frame = ctk.CTkFrame(summary_frame, fg_color="white", border_width=1, border_color="#d1d1d1", corner_radius=5)
            box_frame.grid(row=0, column=i, padx=10, sticky="nsew", ipadx=15, ipady=15)
            
            summary_title = ctk.CTkLabel(box_frame, text=title, font=ctk.CTkFont(size=12))
            summary_title.pack(anchor="center")
            
            # Make the value red if it's a positive number of due books or a non-zero fine
            text_color = "#d9534f" if ((title == "Due Books" and value != "0") or 
                                      (title == "Pending Fines" and value != "$0.00")) else "black"
            
            summary_value = ctk.CTkLabel(box_frame, text=value, 
                                        font=ctk.CTkFont(size=24, weight="bold"),
                                        text_color=text_color)
            summary_value.pack(anchor="center", pady=10)

        # Quick Search Box
        search_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        search_frame.grid(row=3, column=0, sticky="ew", pady=10)

        search_label = ctk.CTkLabel(search_frame, text="🔍 Quick Search", 
                                   font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
        search_label.pack(anchor="w", pady=(10, 5))

        search_entry_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
        search_entry_frame.pack(fill="x")

        search_entry = ctk.CTkEntry(search_entry_frame, placeholder_text="Enter book title, author, or genre", 
                                   font=ctk.CTkFont(size=12), height=35, border_width=1, border_color="#d1d1d1")
        search_entry.pack(side="left", fill="x", expand=True)

        search_button = ctk.CTkButton(search_entry_frame, text="🔍 Search", font=ctk.CTkFont(size=12), 
                                     fg_color="#116636", hover_color="#0d4f29", corner_radius=3, height=35,
                                     command=lambda: self.show_search_results(search_entry.get()))
        search_button.pack(side="left", padx=(10, 0))
        
        # Bind Enter key to search function
        search_entry.bind("<Return>", lambda event: self.show_search_results(search_entry.get()))
        
        # Get borrowed books for the preview section
        borrowed_books = get_user_borrowed_books(self.user['user_id'])
        
        # Recent Borrowed Books Section
        books_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        books_frame.grid(row=4, column=0, sticky="nsew", pady=10)
        books_frame.grid_rowconfigure(1, weight=1)
        books_frame.grid_columnconfigure(0, weight=1)

        books_label = ctk.CTkLabel(books_frame, text="📚 Recent Borrowed Books", 
                                  font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
        books_label.grid(row=0, column=0, sticky="w", pady=(20, 10))
        
        # Button to view all borrowed books
        view_all_button = ctk.CTkButton(books_frame, text="View All", font=ctk.CTkFont(size=12), 
                                      fg_color="#116636", hover_color="#0d4f29", corner_radius=3, height=30,
                                      command=self.show_borrowed_books)
        view_all_button.grid(row=0, column=1, sticky="e", pady=(20, 10))

        # Custom styling for ttk.Treeview
        style = ttk.Style()
        style.theme_use("clam")  # Use clam theme as base
        style.configure("Treeview", background="white", fieldbackground="white", foreground="black")
        style.configure("Treeview.Heading", background="#f0f0f0", foreground="black", font=("Arial", 10, "bold"))
        style.map("Treeview", background=[("selected", "#116636")], foreground=[("selected", "white")])

        # Create the treeview with columns
        columns = ("Title", "Author", "Due Date", "Status", "Action")
        borrowed_books_tree = ttk.Treeview(books_frame, columns=columns, show="headings", height=5)
        borrowed_books_tree.grid(row=1, column=0, columnspan=2, sticky="nsew")

        # Configure columns
        borrowed_books_tree.column("Title", width=250, anchor="w")
        borrowed_books_tree.column("Author", width=200, anchor="w")
        borrowed_books_tree.column("Due Date", width=100, anchor="center")
        borrowed_books_tree.column("Status", width=100, anchor="center")
        borrowed_books_tree.column("Action", width=150, anchor="center")

        # Configure column headings
        for col in columns:
            borrowed_books_tree.heading(col, text=col)

        # Add data and store loan_ids
        self.dashboard_loan_ids = {}
        
        if borrowed_books:
            for book in borrowed_books[:5]:  # Show max 5 books
                due_date = book['due_date'].strftime('%Y-%m-%d') if isinstance(book['due_date'], datetime) else str(book['due_date'])
                
                status = "Overdue" if is_overdue(due_date) else "On Time"
                status_text = status
                
                item_id = borrowed_books_tree.insert("", "end", values=(
                    book['title'], 
                    book['author'], 
                    format_date(due_date), 
                    status_text,
                    ""
                ))
                
                self.dashboard_loan_ids[item_id] = book['loan_id']
            
            
            def on_return_click(tree_item):
                loan_id = self.dashboard_loan_ids.get(tree_item)
                if loan_id:
                    if return_book(loan_id, self.user['user_id']):
                        messagebox.showinfo("Success", "Book returned successfully!")
                        self.show_dashboard()  # Refresh dashboard
                    else:
                        messagebox.showerror("Error", "Failed to return book.")
            
            def create_return_buttons():
                for item in borrowed_books_tree.get_children():
                    bbox = borrowed_books_tree.bbox(item, column="Action")
                    if bbox:
                        button_frame = ctk.CTkFrame(borrowed_books_tree, fg_color="transparent")
                        button_frame.place(x=bbox[0] + 30, y=bbox[1])
                        
                        return_button = ctk.CTkButton(
                            button_frame, 
                            text="↩ Return", 
                            fg_color="#116636", 
                            hover_color="#0d4f29",
                            corner_radius=3, 
                            width=80, 
                            height=25, 
                            font=ctk.CTkFont(size=10),
                            command=lambda i=item: on_return_click(i)
                        )
                        return_button.pack()
            
            # Schedule creation of buttons after treeview is ready
            self.root.after(100, create_return_buttons)
        else:
            # No borrowed books message
            no_books_message = borrowed_books_tree.insert("", "end", values=(
                "You haven't borrowed any books yet.", "", "", "", ""
            ))
    
    def show_search_results(self, query):
        """Switch to the search page and perform search"""
        self.show_search_books()
        if query and len(query.strip()) > 0:
            self.perform_search(query)
    
    def show_search_books(self):
        """Show the search books page"""
        print("Loading search books page...")
        self.clear_main_frame()
        self.highlight_active_menu("🔍 Search Books")
        
        # Search Books Title
        title_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        title = ctk.CTkLabel(title_frame, text="Search for Books", 
                           font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=10)

        # Separator line
        separator_frame = ctk.CTkFrame(self.main_frame, height=1, fg_color="#d1d1d1")
        separator_frame.grid(row=1, column=0, sticky="ew", pady=5)
        
        # Search Box
        search_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        search_frame.grid(row=2, column=0, sticky="ew", pady=15)

        search_label = ctk.CTkLabel(search_frame, text="🔍 Search by Title, Author, Genre, or ISBN", 
                                   font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
        search_label.pack(anchor="w", pady=(5, 10))

        search_entry_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
        search_entry_frame.pack(fill="x")

        self.search_entry = ctk.CTkEntry(search_entry_frame, placeholder_text="Enter search terms...", 
                                   font=ctk.CTkFont(size=12), height=40, border_width=1, border_color="#d1d1d1")
        self.search_entry.pack(side="left", fill="x", expand=True)

        search_button = ctk.CTkButton(search_entry_frame, text="🔍 Search", font=ctk.CTkFont(size=12), 
                                     fg_color="#116636", hover_color="#0d4f29", corner_radius=3, height=40,
                                     command=lambda: self.perform_search(self.search_entry.get()))
        search_button.pack(side="left", padx=(10, 0))
        
        # Bind Enter key to search function
        self.search_entry.bind("<Return>", lambda event: self.perform_search(self.search_entry.get()))
        
        # Results Frame
        results_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        results_frame.grid(row=3, column=0, sticky="nsew", pady=10)
        results_frame.grid_rowconfigure(1, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)

        self.results_label = ctk.CTkLabel(results_frame, text="Enter a search term above to find books", 
                                        font=ctk.CTkFont(size=12), anchor="w")
        self.results_label.grid(row=0, column=0, sticky="w", pady=(10, 5))

        # Custom styling for ttk.Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="white", fieldbackground="white", foreground="black")
        style.configure("Treeview.Heading", background="#f0f0f0", foreground="black", font=("Arial", 10, "bold"))
        style.map("Treeview", background=[("selected", "#116636")], foreground=[("selected", "white")])

        # Create the treeview with columns
        columns = ("Title", "Author", "Genre", "Year", "ISBN", "Available", "Action")
        self.books_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=10)
        self.books_tree.grid(row=1, column=0, sticky="nsew")

        # Add scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.books_tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.books_tree.configure(yscrollcommand=scrollbar.set)

        # Configure columns
        self.books_tree.column("Title", width=250, anchor="w")
        self.books_tree.column("Author", width=170, anchor="w")
        self.books_tree.column("Genre", width=120, anchor="w")
        self.books_tree.column("Year", width=70, anchor="center")
        self.books_tree.column("ISBN", width=120, anchor="center")
        self.books_tree.column("Available", width=70, anchor="center")
        self.books_tree.column("Action", width=100, anchor="center")

        # Configure column headings
        for col in columns:
            self.books_tree.heading(col, text=col)
        
        # Store book_ids for borrow actions
        self.search_book_ids = {}
    
    def perform_search(self, query):
        """Search for books and display results"""
        if not query or len(query.strip()) == 0:
            messagebox.showinfo("Search Error", "Please enter a search term.")
            return
        
        print(f"Performing search for '{query}'...")
        
        # Clear existing results
        for item in self.books_tree.get_children():
            self.books_tree.delete(item)
        
        # Perform search
        results = search_books(query)
        
        # Update results label
        self.results_label.configure(text=f"Found {len(results)} books matching '{query}'")
        
        # Add results to treeview and store book_ids
        self.search_book_ids = {}
        
        if results:
            for book in results:
                item_id = self.books_tree.insert("", "end", values=(
                    book['title'], 
                    book['author'], 
                    book.get('genre', 'Unknown'),
                    book.get('publication_year', ''),
                    book.get('isbn', ''),
                    book.get('available_copies', 0),
                    ""
                ))
                
                self.search_book_ids[item_id] = book['book_id']
            
            # Add Borrow buttons for books with available copies
            def on_borrow_click(tree_item):
                book_id = self.search_book_ids.get(tree_item)
                if book_id:
                    if borrow_book(book_id, self.user['user_id']):
                        messagebox.showinfo("Success", "Book borrowed successfully! You can view it in 'My Borrowed Books'.")
                        self.perform_search(query)  # Refresh results
                    else:
                        messagebox.showerror("Error", "Failed to borrow book.")
            
            def create_borrow_buttons():
                for item in self.books_tree.get_children():
                    values = self.books_tree.item(item, 'values')
                    try:
                        available = int(values[5])  # Available copies column
                    except:
                        available = 0
                    
                    bbox = self.books_tree.bbox(item, column="Action")
                    if bbox:
                        button_frame = ctk.CTkFrame(self.books_tree, fg_color="transparent")
                        button_frame.place(x=bbox[0] + 10, y=bbox[1])
                        
                        if available > 0:
                            borrow_button = ctk.CTkButton(
                                button_frame, 
                                text="Borrow", 
                                fg_color="#116636", 
                                hover_color="#0d4f29",
                                corner_radius=3, 
                                width=80, 
                                height=25, 
                                font=ctk.CTkFont(size=10),
                                command=lambda i=item: on_borrow_click(i)
                            )
                            borrow_button.pack()
                        else:
                            unavailable_label = ctk.CTkLabel(
                                button_frame,
                                text="Unavailable",
                                fg_color="#f0f0f0",
                                text_color="gray",
                                corner_radius=3,
                                width=80,
                                height=25,
                                font=ctk.CTkFont(size=10)
                            )
                            unavailable_label.pack()
            
            # Schedule creation of buttons after treeview is ready
            self.root.after(100, create_borrow_buttons)
        else:
            # No results found
            self.books_tree.insert("", "end", values=(
                "No books found matching your search.", "", "", "", "", "", ""
            ))
    
    def show_borrowed_books(self):
        """Show the user's borrowed books"""
        print("Loading borrowed books page...")
        self.clear_main_frame()
        self.highlight_active_menu("📖 My Borrowed Books")
        
        # Borrowed Books Title
        title_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        title = ctk.CTkLabel(title_frame, text="My Borrowed Books", 
                           font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=10)

        # Separator line
        separator_frame = ctk.CTkFrame(self.main_frame, height=1, fg_color="#d1d1d1")
        separator_frame.grid(row=1, column=0, sticky="ew", pady=5)
        
        # Borrowed Books Frame
        books_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        books_frame.grid(row=2, column=0, sticky="nsew", pady=15)
        books_frame.grid_rowconfigure(1, weight=1)
        books_frame.grid_columnconfigure(0, weight=1)

        # Get borrowed books data
        borrowed_books = get_user_borrowed_books(self.user['user_id'])
        
        books_label = ctk.CTkLabel(books_frame, 
                                 text=f"You currently have {len(borrowed_books)} borrowed books", 
                                 font=ctk.CTkFont(size=14), anchor="w")
        books_label.grid(row=0, column=0, sticky="w", pady=(10, 15))

        # Custom styling for ttk.Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="white", fieldbackground="white", foreground="black")
        style.configure("Treeview.Heading", background="#f0f0f0", foreground="black", font=("Arial", 10, "bold"))
        style.map("Treeview", background=[("selected", "#116636")], foreground=[("selected", "white")])

        # Create the treeview with columns
        columns = ("Title", "Author", "Borrowed Date", "Due Date", "Status", "Fine", "Action")
        borrowed_books_tree = ttk.Treeview(books_frame, columns=columns, show="headings", height=12)
        borrowed_books_tree.grid(row=1, column=0, sticky="nsew")

        # Add scrollbar
        scrollbar = ttk.Scrollbar(books_frame, orient="vertical", command=borrowed_books_tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        borrowed_books_tree.configure(yscrollcommand=scrollbar.set)

        # Configure columns
        borrowed_books_tree.column("Title", width=250, anchor="w")
        borrowed_books_tree.column("Author", width=170, anchor="w")
        borrowed_books_tree.column("Borrowed Date", width=120, anchor="center")
        borrowed_books_tree.column("Due Date", width=120, anchor="center")
        borrowed_books_tree.column("Status", width=100, anchor="center")
        borrowed_books_tree.column("Fine", width=70, anchor="center")
        borrowed_books_tree.column("Action", width=100, anchor="center")

        # Configure column headings
        for col in columns:
            borrowed_books_tree.heading(col, text=col)

        # Add data and store loan_ids
        self.borrowed_loan_ids = {}
        
        if borrowed_books:
            for book in borrowed_books:
                # Format dates
                loan_date = book['loan_date'].strftime('%Y-%m-%d') if isinstance(book['loan_date'], datetime) else str(book['loan_date'])
                due_date = book['due_date'].strftime('%Y-%m-%d') if isinstance(book['due_date'], datetime) else str(book['due_date'])
                
                # Calculate status and fine
                status = "Overdue" if is_overdue(due_date) else "On Time"
                fine = calculate_fine(due_date)
                
                # Add row to treeview
                item_id = borrowed_books_tree.insert("", "end", values=(
                    book['title'], 
                    book['author'], 
                    format_date(loan_date),
                    format_date(due_date), 
                    status,
                    fine,
                    ""
                ))
                
                self.borrowed_loan_ids[item_id] = book['loan_id']
            
            # Add Return buttons
            def on_return_click(tree_item):
                loan_id = self.borrowed_loan_ids.get(tree_item)
                if loan_id:
                    if return_book(loan_id, self.user['user_id']):
                        messagebox.showinfo("Success", "Book returned successfully!")
                        self.show_borrowed_books()  # Refresh page
                    else:
                        messagebox.showerror("Error", "Failed to return book.")
            
            def create_return_buttons():
                for item in borrowed_books_tree.get_children():
                    bbox = borrowed_books_tree.bbox(item, column="Action")
                    if bbox:
                        button_frame = ctk.CTkFrame(borrowed_books_tree, fg_color="transparent")
                        button_frame.place(x=bbox[0] + 10, y=bbox[1])
                        
                        return_button = ctk.CTkButton(
                            button_frame, 
                            text="Return", 
                            fg_color="#116636", 
                            hover_color="#0d4f29",
                            corner_radius=3, 
                            width=80, 
                            height=25, 
                            font=ctk.CTkFont(size=10),
                            command=lambda i=item: on_return_click(i)
                        )
                        return_button.pack()
            
            # Schedule creation of buttons after treeview is ready
            self.root.after(100, create_return_buttons)
        else:
            # No borrowed books, show message
            no_books_frame = ctk.CTkFrame(books_frame, fg_color="white", corner_radius=10)
            no_books_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
            
            no_books_label = ctk.CTkLabel(no_books_frame, 
                                       text="You haven't borrowed any books yet.\nVisit the Search Books page to borrow books!", 
                                       font=ctk.CTkFont(size=14))
            no_books_label.pack(pady=50)
            
            search_button = ctk.CTkButton(no_books_frame, text="Search Books", 
                                       fg_color="#116636", hover_color="#0d4f29",
                                       command=self.show_search_books)
            search_button.pack(pady=10)
    
    def show_fines(self):
        """Show the user's fines and fees"""
        print("Loading fines page...")
        self.clear_main_frame()
        self.highlight_active_menu("💰 Fines & Fees")
        
        # Fines Title
        title_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        title = ctk.CTkLabel(title_frame, text="Fines & Fees", 
                           font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=10)

        # Separator line
        separator_frame = ctk.CTkFrame(self.main_frame, height=1, fg_color="#d1d1d1")
        separator_frame.grid(row=1, column=0, sticky="ew", pady=5)
        
        # Fines Info
        info_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        info_frame.grid(row=2, column=0, sticky="ew", pady=15)
        
        info_text = "• Overdue fees are charged at $0.50 per day\n• Payments can be made online or at the library front desk"
        info_label = ctk.CTkLabel(info_frame, text=info_text, font=ctk.CTkFont(size=12), justify="left")
        info_label.pack(anchor="w")
        
        # Fines Frame
        fines_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        fines_frame.grid(row=3, column=0, sticky="nsew", pady=15)
        fines_frame.grid_rowconfigure(1, weight=1)
        fines_frame.grid_columnconfigure(0, weight=1)

        # Get fines data
        fines = get_user_fines(self.user['user_id'])
        
        # Current Outstanding Fines
        outstanding_fines = [f for f in fines if not f['paid']]
        paid_fines = [f for f in fines if f['paid']]
        
        total_outstanding = sum(float(f['amount']) for f in outstanding_fines)
        
        fines_label = ctk.CTkLabel(fines_frame, 
                                 text=f"Outstanding Fines: ${total_outstanding:.2f}", 
                                 font=ctk.CTkFont(size=14, weight="bold"), 
                                 text_color="#d9534f" if total_outstanding > 0 else "black",
                                 anchor="w")
        fines_label.grid(row=0, column=0, sticky="w", pady=(10, 15))

        # Custom styling for ttk.Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="white", fieldbackground="white", foreground="black")
        style.configure("Treeview.Heading", background="#f0f0f0", foreground="black", font=("Arial", 10, "bold"))
        style.map("Treeview", background=[("selected", "#116636")], foreground=[("selected", "white")])

        # Create the treeview with columns
        columns = ("Book", "Amount", "Status", "Action")
        fines_tree = ttk.Treeview(fines_frame, columns=columns, show="headings", height=8)
        fines_tree.grid(row=1, column=0, sticky="nsew")

        # Add scrollbar
        scrollbar = ttk.Scrollbar(fines_frame, orient="vertical", command=fines_tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        fines_tree.configure(yscrollcommand=scrollbar.set)

        # Configure columns
        fines_tree.column("Book", width=350, anchor="w")
        fines_tree.column("Amount", width=100, anchor="center")
        fines_tree.column("Status", width=100, anchor="center")
        fines_tree.column("Action", width=150, anchor="center")

        # Configure column headings
        for col in columns:
            fines_tree.heading(col, text=col)

        # Add data and store fine_ids
        self.fine_ids = {}
        
        if fines:
            # First add outstanding fines
            for fine in outstanding_fines:
                item_id = fines_tree.insert("", "end", values=(
                    fine['title'], 
                    f"${float(fine['amount']):.2f}",
                    "Unpaid",
                    ""
                ))
                
                self.fine_ids[item_id] = fine['fine_id']
            
            # Add paid fines with different formatting
            for fine in paid_fines:
                payment_date = fine['payment_date'].strftime('%Y-%m-%d') if isinstance(fine['payment_date'], datetime) else str(fine['payment_date'])
                status = f"Paid on {format_date(payment_date)}"
                
                item_id = fines_tree.insert("", "end", values=(
                    fine['title'], 
                    f"${float(fine['amount']):.2f}",
                    status,
                    ""
                ))
                
                self.fine_ids[item_id] = fine['fine_id']
            
            # Add Pay buttons for unpaid fines
            def on_pay_click(tree_item):
                fine_id = self.fine_ids.get(tree_item)
                if fine_id:
                    response = messagebox.askyesno("Confirm Payment", "Proceed to payment gateway?")
                    if response:
                        if pay_fine(fine_id, self.user['user_id']):
                            messagebox.showinfo("Success", "Fine paid successfully!")
                            self.show_fines()  # Refresh page
                        else:
                            messagebox.showerror("Error", "Failed to process payment.")
            
            def create_pay_buttons():
                for item in fines_tree.get_children():
                    values = fines_tree.item(item, 'values')
                    status = values[2]
                    
                    if status == "Unpaid":
                        bbox = fines_tree.bbox(item, column="Action")
                        if bbox:
                            button_frame = ctk.CTkFrame(fines_tree, fg_color="transparent")
                            button_frame.place(x=bbox[0] + 30, y=bbox[1])
                            
                            pay_button = ctk.CTkButton(
                                button_frame, 
                                text="Pay Now", 
                                fg_color="#d9534f", 
                                hover_color="#c9302c",
                                corner_radius=3, 
                                width=80, 
                                height=25, 
                                font=ctk.CTkFont(size=10),
                                command=lambda i=item: on_pay_click(i)
                            )
                            pay_button.pack()
            
            # Schedule creation of buttons after treeview is ready
            self.root.after(100, create_pay_buttons)
        else:
            # No fines, show message
            no_fines_frame = ctk.CTkFrame(fines_frame, fg_color="white", corner_radius=10)
            no_fines_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
            
            no_fines_label = ctk.CTkLabel(no_fines_frame, 
                                       text="You have no fines or fees.\nThank you for returning your books on time!", 
                                       font=ctk.CTkFont(size=14))
            no_fines_label.pack(pady=50)
    
    def show_profile(self):
        """Show the user's profile"""
        print("Loading profile page...")
        self.clear_main_frame()
        self.highlight_active_menu("👤 My Profile")
        
        # Get user profile data
        profile = get_user_profile(self.user['user_id'])
        if not profile:
            messagebox.showerror("Error", "Failed to load profile data.")
            return
        
        # Profile Title
        title_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        title = ctk.CTkLabel(title_frame, text="My Profile", 
                           font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=10)

        # Separator line
        separator_frame = ctk.CTkFrame(self.main_frame, height=1, fg_color="#d1d1d1")
        separator_frame.grid(row=1, column=0, sticky="ew", pady=5)
        
        # Profile Frame
        profile_frame = ctk.CTkFrame(self.main_frame, fg_color="white", corner_radius=10)
        profile_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=20)
        profile_frame.grid_columnconfigure(0, weight=1)
        
        # Header with user role and join date
        header_frame = ctk.CTkFrame(profile_frame, fg_color="#f0f5f0", corner_radius=0)
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 30), ipady=10)
        
        role_text = f"Account Type: {profile['role'].capitalize()}"
        role_label = ctk.CTkLabel(header_frame, text=role_text, font=ctk.CTkFont(size=14, weight="bold"))
        role_label.pack(side="left", padx=20)
        
        joined_text = f"Member Since: {format_date(profile['registration_date'])}"
        joined_label = ctk.CTkLabel(header_frame, text=joined_text, font=ctk.CTkFont(size=14))
        joined_label.pack(side="right", padx=20)
        
        # Profile form
        form_frame = ctk.CTkFrame(profile_frame, fg_color="transparent")
        form_frame.grid(row=1, column=0, sticky="nsew", padx=40, pady=10)
        form_frame.grid_columnconfigure(1, weight=1)
        
        # First Name
        ctk.CTkLabel(form_frame, text="First Name:", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, sticky="w", pady=(10, 5))
        first_name_entry = ctk.CTkEntry(form_frame, width=300, height=35, font=ctk.CTkFont(size=12))
        first_name_entry.grid(row=0, column=1, sticky="w", pady=(10, 5))
        first_name_entry.insert(0, profile['first_name'])
        
        # Last Name
        ctk.CTkLabel(form_frame, text="Last Name:", font=ctk.CTkFont(size=14, weight="bold")).grid(row=1, column=0, sticky="w", pady=5)
        last_name_entry = ctk.CTkEntry(form_frame, width=300, height=35, font=ctk.CTkFont(size=12))
        last_name_entry.grid(row=1, column=1, sticky="w", pady=5)
        last_name_entry.insert(0, profile['last_name'])
        
        # Email
        ctk.CTkLabel(form_frame, text="Email:", font=ctk.CTkFont(size=14, weight="bold")).grid(row=2, column=0, sticky="w", pady=5)
        email_entry = ctk.CTkEntry(form_frame, width=300, height=35, font=ctk.CTkFont(size=12))
        email_entry.grid(row=2, column=1, sticky="w", pady=5)
        email_entry.insert(0, profile['email'])
        
        # Separator
        separator = ctk.CTkFrame(profile_frame, height=1, fg_color="#d1d1d1")
        separator.grid(row=2, column=0, sticky="ew", padx=40, pady=20)
        
        # Password change section
        password_frame = ctk.CTkFrame(profile_frame, fg_color="transparent")
        password_frame.grid(row=3, column=0, sticky="nsew", padx=40, pady=10)
        password_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(password_frame, text="Change Password", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        # Current Password
        ctk.CTkLabel(password_frame, text="Current Password:", font=ctk.CTkFont(size=14)).grid(row=1, column=0, sticky="w", pady=5)
        current_password_entry = ctk.CTkEntry(password_frame, width=300, height=35, font=ctk.CTkFont(size=12), show="•")
        current_password_entry.grid(row=1, column=1, sticky="w", pady=5)
        
        # New Password
        ctk.CTkLabel(password_frame, text="New Password:", font=ctk.CTkFont(size=14)).grid(row=2, column=0, sticky="w", pady=5)
        new_password_entry = ctk.CTkEntry(password_frame, width=300, height=35, font=ctk.CTkFont(size=12), show="•")
        new_password_entry.grid(row=2, column=1, sticky="w", pady=5)
        
        # Confirm New Password
        ctk.CTkLabel(password_frame, text="Confirm New Password:", font=ctk.CTkFont(size=14)).grid(row=3, column=0, sticky="w", pady=5)
        confirm_password_entry = ctk.CTkEntry(password_frame, width=300, height=35, font=ctk.CTkFont(size=12), show="•")
        confirm_password_entry.grid(row=3, column=1, sticky="w", pady=5)
        
        # Action buttons
        button_frame = ctk.CTkFrame(profile_frame, fg_color="transparent")
        button_frame.grid(row=4, column=0, sticky="ew", padx=40, pady=(20, 30))
        
        def save_profile():
            # Validate inputs
            first_name = first_name_entry.get().strip()
            last_name = last_name_entry.get().strip()
            email = email_entry.get().strip()
            
            if not first_name or not last_name or not email:
                messagebox.showwarning("Input Error", "Name and email fields cannot be empty.")
                return
            
            # Check for password change
            current_password = current_password_entry.get()
            new_password = new_password_entry.get()
            confirm_password = confirm_password_entry.get()
            
            if new_password or confirm_password or current_password:
                # Password change requested
                if not current_password:
                    messagebox.showwarning("Password Error", "Please enter your current password.")
                    return
                
                if not new_password:
                    messagebox.showwarning("Password Error", "Please enter a new password.")
                    return
                
                if new_password != confirm_password:
                    messagebox.showwarning("Password Error", "New passwords do not match.")
                    return
                
                # Update profile with password change
                if update_user_profile(profile['user_id'], first_name, last_name, email, current_password, new_password):
                    messagebox.showinfo("Success", "Profile updated successfully with new password.")
                    # Update session info
                    self.user['first_name'] = first_name
                    self.user['last_name'] = last_name
                    self.user['email'] = email
                    save_session(self.user)
                    self.show_profile()  # Refresh page
            else:
                # Update profile without password change
                if update_user_profile(profile['user_id'], first_name, last_name, email):
                    messagebox.showinfo("Success", "Profile updated successfully.")
                    # Update session info
                    self.user['first_name'] = first_name
                    self.user['last_name'] = last_name
                    self.user['email'] = email
                    save_session(self.user)
                    self.show_profile()  # Refresh page
        
        # Save button
        save_button = ctk.CTkButton(button_frame, text="Save Changes", font=ctk.CTkFont(size=14), 
                                  fg_color="#116636", hover_color="#0d4f29", width=150, height=40,
                                  command=save_profile)
        save_button.pack(side="right")
    
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
            print(f"Error during logout: {e}")
            messagebox.showerror("Error", f"Failed to logout: {e}")
            self.root.destroy()

# ------------------- Main Application -------------------
if __name__ == "__main__":
    try:
        # Get command line arguments if any
        import sys
        start_page = sys.argv[1] if len(sys.argv) > 1 else None
        
        root = ctk.CTk()
        app = LibraryApp(root, start_page)
        root.mainloop()
    except Exception as e:
        print(f"Application Error: {e}")
        messagebox.showerror("Application Error", f"An error occurred: {e}")