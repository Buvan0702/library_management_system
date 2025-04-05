import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
import mysql.connector
import json
import os
from datetime import datetime
import math

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

# ------------------- Book Functions -------------------
def get_books(search_term="", category=""):
    """Get books from database with optional search and category filters"""
    connection = connect_db()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        query = """
            SELECT 
                b.book_id, 
                b.title, 
                b.author, 
                b.genre,
                b.publication_year,
                b.available_copies,
                b.total_copies,
                b.isbn,
                b.description
            FROM 
                Books b
            WHERE 1=1
        """
        
        params = []
        
        if search_term:
            query += """ AND (
                b.title LIKE %s OR 
                b.author LIKE %s OR 
                b.genre LIKE %s OR
                b.isbn LIKE %s
            )"""
            search_param = f"%{search_term}%"
            params.extend([search_param, search_param, search_param, search_param])
        
        if category:
            query += " AND b.genre = %s"
            params.append(category)
        
        query += " ORDER BY b.title"
        
        cursor.execute(query, params)
        return cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_book_categories():
    """Get all unique book categories/genres"""
    connection = connect_db()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("SELECT DISTINCT genre FROM Books ORDER BY genre")
        
        # Extract first element from each tuple in result
        return [category[0] for category in cursor.fetchall()]
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def borrow_book(book_id, user_id):
    """Borrow a book"""
    connection = connect_db()
    if not connection:
        return False, "Database connection failed"
    
    try:
        cursor = connection.cursor()
        
        # Check if user already has this book
        cursor.execute(
            "SELECT COUNT(*) FROM Loans WHERE book_id = %s AND user_id = %s AND return_date IS NULL", 
            (book_id, user_id)
        )
        if cursor.fetchone()[0] > 0:
            return False, "You already have this book borrowed"
        
        # Check if book has available copies
        cursor.execute("SELECT available_copies FROM Books WHERE book_id = %s", (book_id,))
        result = cursor.fetchone()
        
        if result and result[0] > 0:
            # Create loan record with due date 14 days from now
            cursor.execute(
                "INSERT INTO Loans (user_id, book_id, loan_date, due_date) VALUES (%s, %s, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY))", 
                (user_id, book_id)
            )
            
            # Decrement available copies
            cursor.execute(
                "UPDATE Books SET available_copies = available_copies - 1 WHERE book_id = %s", 
                (book_id,)
            )
            
            connection.commit()
            return True, "Book borrowed successfully"
        else:
            return False, "This book is currently unavailable"
    except mysql.connector.Error as err:
        return False, f"Database Error: {err}"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def is_book_borrowed_by_user(book_id, user_id):
    """Check if a user has already borrowed a specific book"""
    connection = connect_db()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        cursor.execute(
            "SELECT COUNT(*) FROM Loans WHERE book_id = %s AND user_id = %s AND return_date IS NULL", 
            (book_id, user_id)
        )
        
        return cursor.fetchone()[0] > 0
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- UI Functions -------------------
class LibraryBrowseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Library Management System - Browse Books")
        self.root.geometry("1300x700")
        
        # Set appearance mode and default color theme
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")
        
        # Load user session
        self.user = load_session()
        if not self.user:
            print("No active user session found.")
            self.logout()
            return
        
        # Initialize variables
        self.current_page = 0
        self.books_per_page = 6
        self.current_search = ""
        self.current_category = ""
        self.all_books = []
        
        # Create main frame layout
        self.create_layout()
        
        # Load initial books
        self.load_books()
    
    def create_layout(self):
        """Create the main UI layout"""
        # Create main frame
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
            ("🔍 Search Books", self.refresh_page),  # Current page
            ("📖 My Borrowed Books", self.open_borrowed),
            ("💰 Fines & Fees", self.open_fines),
            ("👤 My Profile", self.open_profile),
        ]
        
        # Highlight the current active menu (Search Books)
        for i, (text, command) in enumerate(menu_items):
            if i == 1:  # Search Books is active
                btn = ctk.CTkButton(
                    self.sidebar,
                    text=text,
                    anchor="w",
                    font=ctk.CTkFont(size=14),
                    fg_color="#0d4f29",  # Highlight color
                    text_color="white",
                    hover_color="#0d4f29",
                    command=command
                )
            else:
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
        """Create the content area with search and book display"""
        # Title
        self.title_label = ctk.CTkLabel(
            self.content, 
            text="Browse Books",
            font=ctk.CTkFont(size=24, weight="bold"),
            anchor="w"
        )
        self.title_label.pack(anchor="w", padx=30, pady=(20, 20))
        
        # Search bar frame
        search_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        search_frame.pack(fill="x", padx=30, pady=(0, 10))
        
        # Search Entry and Button
        self.search_entry = ctk.CTkEntry(
            search_frame,
            width=600,
            height=40,
            placeholder_text="Search by title, author, genre, or ISBN",
            font=ctk.CTkFont(size=14)
        )
        self.search_entry.pack(side="left")
        
        # Bind Enter key to search
        self.search_entry.bind("<Return>", lambda event: self.search_books())
        
        search_button = ctk.CTkButton(
            search_frame,
            text="🔍 Search",
            font=ctk.CTkFont(size=14),
            fg_color="#116636",
            hover_color="#0d4f29",
            width=120,
            height=40,
            command=self.search_books
        )
        search_button.pack(side="left", padx=(10, 0))
        
        # Categories Label
        categories_label = ctk.CTkLabel(
            self.content,
            text="Categories:",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        categories_label.pack(anchor="w", padx=30, pady=(10, 5))
        
        # Categories Buttons Frame
        self.categories_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.categories_frame.pack(fill="x", padx=30, pady=(0, 20))
        
        # Create category buttons
        self.create_category_buttons()
        
        # Frame for result info and pagination
        self.results_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.results_frame.pack(fill="x", padx=30, pady=(0, 10))
        
        # Results info label (left)
        self.results_info = ctk.CTkLabel(
            self.results_frame,
            text="Showing all books",
            font=ctk.CTkFont(size=14),
            anchor="w"
        )
        self.results_info.pack(side="left")
        
        # Create pagination frame (right)
        self.pagination_frame = ctk.CTkFrame(self.results_frame, fg_color="transparent")
        self.pagination_frame.pack(side="right")
        
        # Books Grid Frame - will contain book cards
        self.books_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.books_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
    
    def create_category_buttons(self):
        """Create category filter buttons"""
        # Clear existing buttons
        for widget in self.categories_frame.winfo_children():
            widget.destroy()
        
        # Add "All" category button
        all_btn = ctk.CTkButton(
            self.categories_frame,
            text="All",
            font=ctk.CTkFont(size=12),
            fg_color="#116636" if self.current_category == "" else "#C5E1A5",
            text_color="white" if self.current_category == "" else "#333333",
            hover_color="#0d4f29" if self.current_category == "" else "#A5D6A7",
            width=100,
            height=30,
            corner_radius=15,
            command=lambda: self.filter_by_category("")
        )
        all_btn.pack(side="left", padx=(0, 5))
        
        # Get categories from database
        categories = get_book_categories()
        
        for category in categories:
            cat_button = ctk.CTkButton(
                self.categories_frame,
                text=category,
                font=ctk.CTkFont(size=12),
                fg_color="#116636" if self.current_category == category else "#C5E1A5",
                text_color="white" if self.current_category == category else "#333333",
                hover_color="#0d4f29" if self.current_category == category else "#A5D6A7",
                width=100,
                height=30,
                corner_radius=15,
                command=lambda cat=category: self.filter_by_category(cat)
            )
            cat_button.pack(side="left", padx=(0, 5))
    
    def create_pagination(self):
        """Create pagination controls"""
        # Clear existing pagination controls
        for widget in self.pagination_frame.winfo_children():
            widget.destroy()
        
        # Calculate total pages
        total_books = len(self.all_books)
        total_pages = max(1, math.ceil(total_books / self.books_per_page))
        
        # Only show pagination if there's more than one page
        if total_pages > 1:
            # Previous button
            prev_btn = ctk.CTkButton(
                self.pagination_frame,
                text="< Prev",
                font=ctk.CTkFont(size=12),
                fg_color="#116636" if self.current_page > 0 else "#cccccc",
                text_color="white" if self.current_page > 0 else "#777777",
                hover_color="#0d4f29" if self.current_page > 0 else "#cccccc",
                width=80,
                height=30,
                corner_radius=15,
                state="normal" if self.current_page > 0 else "disabled",
                command=self.previous_page
            )
            prev_btn.pack(side="left", padx=(0, 5))
            
            # Page indicator
            page_label = ctk.CTkLabel(
                self.pagination_frame,
                text=f"Page {self.current_page + 1} of {total_pages}",
                font=ctk.CTkFont(size=12),
                width=120,
                anchor="center"
            )
            page_label.pack(side="left", padx=5)
            
            # Next button
            next_btn = ctk.CTkButton(
                self.pagination_frame,
                text="Next >",
                font=ctk.CTkFont(size=12),
                fg_color="#116636" if self.current_page < total_pages - 1 else "#cccccc",
                text_color="white" if self.current_page < total_pages - 1 else "#777777",
                hover_color="#0d4f29" if self.current_page < total_pages - 1 else "#cccccc",
                width=80,
                height=30,
                corner_radius=15,
                state="normal" if self.current_page < total_pages - 1 else "disabled",
                command=self.next_page
            )
            next_btn.pack(side="left", padx=(5, 0))
    
    def load_books(self):
        """Load books from database with current filters"""
        # Get books with current search and category
        self.all_books = get_books(self.current_search, self.current_category)
        
        # Update results info
        self.update_results_info()
        
        # Create pagination
        self.create_pagination()
        
        # Display current page of books
        self.display_books()
    
    def display_books(self):
        """Display the current page of books"""
        # Clear current book display
        for widget in self.books_frame.winfo_children():
            widget.destroy()
        
        # Calculate slice for current page
        start_idx = self.current_page * self.books_per_page
        end_idx = start_idx + self.books_per_page
        current_books = self.all_books[start_idx:end_idx]
        
        # Configure grid columns and rows
        cols = 3  # Number of books per row
        rows = math.ceil(len(current_books) / cols)
        
        for i in range(cols):
            self.books_frame.grid_columnconfigure(i, weight=1, uniform="column")
        
        for i in range(rows):
            self.books_frame.grid_rowconfigure(i, weight=1)
        
        # Create book cards
        for i, book in enumerate(current_books):
            row = i // cols
            col = i % cols
            
            # Create the book card
            self.create_book_card(book, row, col)
    
    def create_book_card(self, book, row, col):
        """Create a card for an individual book"""
        # Create a book card frame with white background and slight shadow
        book_card = ctk.CTkFrame(
            self.books_frame,
            width=350,
            height=200,
            fg_color="white",
            corner_radius=10,
            border_width=1,
            border_color="#cccccc"
        )
        book_card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        book_card.grid_propagate(False)  # Prevent frame from shrinking
        
        # Book title
        title_label = ctk.CTkLabel(
            book_card,
            text=book["title"],
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
            text_color="#000000"
        )
        title_label.place(x=15, y=15)
        
        # Author
        author_label = ctk.CTkLabel(
            book_card,
            text=f"Author: {book['author']}",
            font=ctk.CTkFont(size=14),
            anchor="w",
            text_color="#444444"
        )
        author_label.place(x=15, y=45)
        
        # Genre
        genre_label = ctk.CTkLabel(
            book_card,
            text=f"Genre: {book['genre']}",
            font=ctk.CTkFont(size=14),
            anchor="w",
            text_color="#444444"
        )
        genre_label.place(x=15, y=75)
        
        # Year
        year_label = ctk.CTkLabel(
            book_card,
            text=f"Year: {book['publication_year']}",
            font=ctk.CTkFont(size=14),
            anchor="w",
            text_color="#444444"
        )
        year_label.place(x=15, y=105)
        
        # Status with colored indicator
        status_text = "Status: "
        status_label = ctk.CTkLabel(
            book_card,
            text=status_text,
            font=ctk.CTkFont(size=14),
            anchor="w",
            text_color="#444444"
        )
        status_label.place(x=15, y=135)
        
        # Check if book is available
        is_available = book["available_copies"] > 0
        
        # Check if user already has this book borrowed
        already_borrowed = is_book_borrowed_by_user(book["book_id"], self.user["user_id"])
        
        # Status indicator
        if is_available:
            status = "Available"
            status_color = "#4CAF50"  # Green
        else:
            status = "Unavailable"
            status_color = "#F44336"  # Red
        
        status_indicator = ctk.CTkLabel(
            book_card,
            text=status,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=status_color
        )
        status_indicator.place(x=70, y=135)
        
        # Add copies indicator
        copies_text = f"Copies: {book['available_copies']}/{book['total_copies']}"
        copies_label = ctk.CTkLabel(
            book_card,
            text=copies_text,
            font=ctk.CTkFont(size=12),
            text_color="#777777"
        )
        copies_label.place(x=200, y=135)
        
        # Action button
        if already_borrowed:
            # Already borrowed - show indicator
            action_button = ctk.CTkButton(
                book_card,
                text="✓ Borrowed",
                font=ctk.CTkFont(size=14),
                fg_color="#8bc34a",  # Light green
                text_color="white",
                hover_color="#7cb342",
                width=120,
                height=30,
                corner_radius=15,
                state="disabled"
            )
        elif is_available:
            # Borrow button
            action_button = ctk.CTkButton(
                book_card,
                text="Borrow Book",
                font=ctk.CTkFont(size=14),
                fg_color="#116636",
                hover_color="#0d4f29",
                width=120,
                height=30,
                corner_radius=15,
                command=lambda b_id=book["book_id"]: self.borrow_book_action(b_id)
            )
        else:
            # Unavailable status
            action_button = ctk.CTkButton(
                book_card,
                text="Unavailable",
                font=ctk.CTkFont(size=14),
                fg_color="#cccccc",
                text_color="#777777",
                hover_color="#bbbbbb",
                width=120,
                height=30,
                corner_radius=15,
                state="disabled"
            )
        
        action_button.place(x=15, y=165)
        
        # Details button
        details_button = ctk.CTkButton(
            book_card,
            text="View Details",
            font=ctk.CTkFont(size=14),
            fg_color="#f0f0f0",
            text_color="#116636",
            hover_color="#e0e0e0",
            width=100,
            height=30,
            corner_radius=15,
            command=lambda b_id=book["book_id"]: self.show_book_details(book)
        )
        details_button.place(x=145, y=165)
    
    def update_results_info(self):
        """Update the results info text"""
        total_books = len(self.all_books)
        
        if self.current_search and self.current_category:
            self.results_info.configure(text=f"Found {total_books} books matching '{self.current_search}' in category '{self.current_category}'")
        elif self.current_search:
            self.results_info.configure(text=f"Found {total_books} books matching '{self.current_search}'")
        elif self.current_category:
            self.results_info.configure(text=f"Showing {total_books} books in category '{self.current_category}'")
        else:
            self.results_info.configure(text=f"Showing all {total_books} books")
    
    # ------------------- Action Functions -------------------
    def search_books(self):
        """Search for books with the current search term"""
        self.current_page = 0  # Reset to first page
        self.current_search = self.search_entry.get()
        self.load_books()
    
    def filter_by_category(self, category):
        """Filter books by category"""
        self.current_page = 0  # Reset to first page
        self.current_category = category
        self.load_books()
        
        # Refresh category buttons to show the active one
        self.create_category_buttons()
    
    def next_page(self):
        """Go to next page of books"""
        total_pages = math.ceil(len(self.all_books) / self.books_per_page)
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.create_pagination()
            self.display_books()
    
    def previous_page(self):
        """Go to previous page of books"""
        if self.current_page > 0:
            self.current_page -= 1
            self.create_pagination()
            self.display_books()
    
    def borrow_book_action(self, book_id):
        """Handle the borrow book action"""
        success, message = borrow_book(book_id, self.user["user_id"])
        
        if success:
            # Show success message
            messagebox = ctk.CTkToplevel(self.root)
            messagebox.title("Success")
            messagebox.geometry("300x150")
            messagebox.resizable(False, False)
            messagebox.grab_set()  # Make it modal
            
            # Center the messagebox on screen
            messageX = self.root.winfo_x() + (self.root.winfo_width() // 2) - 150
            messageY = self.root.winfo_y() + (self.root.winfo_height() // 2) - 75
            messagebox.geometry(f"+{messageX}+{messageY}")
            
            # Add message and button
            frame = ctk.CTkFrame(messagebox, fg_color="transparent")
            frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            label = ctk.CTkLabel(
                frame, 
                text=message,
                font=ctk.CTkFont(size=14)
            )
            label.pack(pady=(10, 20))
            
            ok_button = ctk.CTkButton(
                frame,
                text="OK",
                font=ctk.CTkFont(size=14),
                fg_color="#116636",
                hover_color="#0d4f29",
                command=lambda: [messagebox.destroy(), self.refresh_page()]
            )
            ok_button.pack()
            
            # Set focus and bind Return key
            ok_button.focus_set()
            messagebox.bind("<Return>", lambda event: [messagebox.destroy(), self.refresh_page()])
        else:
            # Show error message
            messagebox = ctk.CTkToplevel(self.root)
            messagebox.title("Error")
            messagebox.geometry("300x150")
            messagebox.resizable(False, False)
            messagebox.grab_set()  # Make it modal
            
            # Center the messagebox on screen
            messageX = self.root.winfo_x() + (self.root.winfo_width() // 2) - 150
            messageY = self.root.winfo_y() + (self.root.winfo_height() // 2) - 75
            messagebox.geometry(f"+{messageX}+{messageY}")
            
            # Add message and button
            frame = ctk.CTkFrame(messagebox, fg_color="transparent")
            frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            label = ctk.CTkLabel(
                frame, 
                text=message,
                font=ctk.CTkFont(size=14),
                text_color="#d9534f"
            )
            label.pack(pady=(10, 20))
            
            ok_button = ctk.CTkButton(
                frame,
                text="OK",
                font=ctk.CTkFont(size=14),
                fg_color="#116636",
                hover_color="#0d4f29",
                command=messagebox.destroy
            )
            ok_button.pack()
            
            # Set focus and bind Return key
            ok_button.focus_set()
            messagebox.bind("<Return>", lambda event: messagebox.destroy())
    
    def show_book_details(self, book):
        """Show detailed information about a book"""
        # Create a modal dialog for book details
        details_window = ctk.CTkToplevel(self.root)
        details_window.title(f"Book Details: {book['title']}")
        details_window.geometry("600x400")
        details_window.resizable(False, False)
        details_window.grab_set()  # Make it modal
        
        # Center the window on screen
        windowX = self.root.winfo_x() + (self.root.winfo_width() // 2) - 300
        windowY = self.root.winfo_y() + (self.root.winfo_height() // 2) - 200
        details_window.geometry(f"+{windowX}+{windowY}")
        
        # Create details frame
        details_frame = ctk.CTkFrame(details_window)
        details_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Book title
        title_label = ctk.CTkLabel(
            details_frame,
            text=book["title"],
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor="w"
        )
        title_label.pack(anchor="w", pady=(0, 10))
        
        # Details grid
        info_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
        info_frame.pack(fill="x", pady=(0, 10))
        
        info_grid = [
            ("Author:", book["author"]),
            ("Genre:", book["genre"]),
            ("Publication Year:", str(book["publication_year"])),
            ("ISBN:", book["isbn"]),
            ("Status:", f"Available ({book['available_copies']}/{book['total_copies']} copies)")
            if book["available_copies"] > 0 else f"Unavailable (0/{book['total_copies']} copies)"
        ]
        
        for i, (label_text, value) in enumerate(info_grid):
            label = ctk.CTkLabel(
                info_frame,
                text=label_text,
                font=ctk.CTkFont(size=14, weight="bold"),
                width=150,
                anchor="e"
            )
            label.grid(row=i, column=0, sticky="e", pady=5)
            
            value_label = ctk.CTkLabel(
                info_frame,
                text=value,
                font=ctk.CTkFont(size=14),
                anchor="w"
            )
            value_label.grid(row=i, column=1, sticky="w", padx=10, pady=5)
        
        # Description section
        desc_label = ctk.CTkLabel(
            details_frame,
            text="Description:",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        desc_label.pack(anchor="w", pady=(10, 5))
        
        description = book.get("description", "No description available.")
        if not description:
            description = "No description available."
        
        desc_text = ctk.CTkTextbox(
            details_frame,
            font=ctk.CTkFont(size=12),
            width=560,
            height=120,
            fg_color="#f5f5f5",
            border_width=1,
            border_color="#dddddd",
            activate_scrollbars=True
        )
        desc_text.pack(fill="x", pady=(0, 15))
        desc_text.insert("1.0", description)
        desc_text.configure(state="disabled")  # Make read-only
        
        # Action buttons
        button_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))
        
        # Check if user already has this book borrowed
        already_borrowed = is_book_borrowed_by_user(book["book_id"], self.user["user_id"])
        
        # Close button (always show)
        close_button = ctk.CTkButton(
            button_frame,
            text="Close",
            font=ctk.CTkFont(size=14),
            fg_color="#f0f0f0",
            text_color="#333333",
            hover_color="#e0e0e0",
            width=120,
            height=35,
            corner_radius=5,
            command=details_window.destroy
        )
        close_button.pack(side="right", padx=5)
        
        # Borrow/status button (conditional)
        if already_borrowed:
            status_button = ctk.CTkButton(
                button_frame,
                text="✓ Already Borrowed",
                font=ctk.CTkFont(size=14),
                fg_color="#8bc34a",
                text_color="white",
                hover_color="#8bc34a",
                width=150,
                height=35,
                corner_radius=5,
                state="disabled"
            )
        elif book["available_copies"] > 0:
            status_button = ctk.CTkButton(
                button_frame,
                text="Borrow This Book",
                font=ctk.CTkFont(size=14),
                fg_color="#116636",
                hover_color="#0d4f29",
                width=150,
                height=35,
                corner_radius=5,
                command=lambda: [details_window.destroy(), self.borrow_book_action(book["book_id"])]
            )
        else:
            status_button = ctk.CTkButton(
                button_frame,
                text="Unavailable",
                font=ctk.CTkFont(size=14),
                fg_color="#cccccc",
                text_color="#777777",
                hover_color="#cccccc",
                width=150,
                height=35,
                corner_radius=5,
                state="disabled"
            )
        
        status_button.pack(side="right", padx=5)
    
    def refresh_page(self):
        """Refresh the current page"""
        self.load_books()
    
    def open_dashboard(self):
        """Open the dashboard page"""
        self.root.destroy()
        os.system("python home.py")
    
    def open_borrowed(self):
        """Open the borrowed books page"""
        self.root.destroy()
        # We'll redirect to home.py and it will show the borrowed books tab
        os.system("python home.py borrowed")
    
    def open_fines(self):
        """Open the fines page"""
        self.root.destroy()
        # We'll redirect to home.py and it will show the fines tab
        os.system("python home.py fines")
    
    def open_profile(self):
        """Open the profile page"""
        self.root.destroy()
        # We'll redirect to home.py and it will show the profile tab
        os.system("python home.py profile")
    
    def logout(self):
        """Logout and return to login page"""
        try:
            # Clear the session if it exists
            if os.path.exists(SESSION_FILE):
                os.remove(SESSION_FILE)
            
            # Close current window
            self.root.destroy()
            
            # Open login page
            os.system("python login.py")
        except Exception as e:
            print(f"Logout Error: {e}")
            self.root.destroy()

# ------------------- Main Application -------------------
if __name__ == "__main__":
    try:
        root = ctk.CTk()
        app = LibraryBrowseApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Application Error: {e}")