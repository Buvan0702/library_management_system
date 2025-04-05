import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
import mysql.connector
import os
import sys
import subprocess
from PIL import Image, ImageTk

# ------------------- Constants -------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "new_password"  # Replace with your MySQL password
}

DB_NAME = "library_system"

# ------------------- Database Setup Functions -------------------
def check_database_exists():
    """Check if the library_system database exists"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Check if database exists
        cursor.execute("SHOW DATABASES LIKE %s", (DB_NAME,))
        result = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return result is not None
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Failed to connect to MySQL: {err}")
        return False

def create_database():
    """Create the library_system database and tables"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Create database
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        cursor.execute(f"USE {DB_NAME}")
        
        # Create Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                role ENUM('member', 'admin') DEFAULT 'member',
                registration_date DATE DEFAULT (CURRENT_DATE),
                CONSTRAINT email_unique UNIQUE (email)
            )
        """)
        
        # Create Books table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Books (
                book_id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                author VARCHAR(100) NOT NULL,
                isbn VARCHAR(20) UNIQUE,
                publication_year INT,
                genre VARCHAR(50),
                description TEXT,
                total_copies INT DEFAULT 1,
                available_copies INT DEFAULT 1
            )
        """)
        
        # Create Loans table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Loans (
                loan_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                book_id INT,
                loan_date DATE DEFAULT (CURRENT_DATE),
                due_date DATE,
                return_date DATE NULL,
                FOREIGN KEY (user_id) REFERENCES Users(user_id),
                FOREIGN KEY (book_id) REFERENCES Books(book_id)
            )
        """)
        
        # Create Fines table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Fines (
                fine_id INT AUTO_INCREMENT PRIMARY KEY,
                loan_id INT,
                amount DECIMAL(10, 2) NOT NULL,
                description VARCHAR(255),
                paid BOOLEAN DEFAULT FALSE,
                payment_date DATE NULL,
                FOREIGN KEY (loan_id) REFERENCES Loans(loan_id)
            )
        """)
        
        # Check if there's at least one admin user
        cursor.execute("SELECT COUNT(*) FROM Users WHERE role = 'admin'")
        admin_count = cursor.fetchone()[0]
        
        # Create default admin if none exists
        if admin_count == 0:
            import hashlib
            default_password = hashlib.sha256("admin123".encode()).hexdigest()
            
            cursor.execute("""
                INSERT INTO Users (first_name, last_name, email, password, role)
                VALUES ('Admin', 'User', 'admin@library.com', %s, 'admin')
            """, (default_password,))
        
        # Insert sample book data if the Books table is empty
        cursor.execute("SELECT COUNT(*) FROM Books")
        book_count = cursor.fetchone()[0]
        
        if book_count == 0:
            sample_books = [
                ("The Great Gatsby", "F. Scott Fitzgerald", "9780743273565", 1925, "Fiction", "A novel about the American Dream", 5, 5),
                ("To Kill a Mockingbird", "Harper Lee", "9780061120084", 1960, "Fiction", "Classic novel of racial injustice", 3, 3),
                ("1984", "George Orwell", "9780451524935", 1949, "Dystopian", "Dystopian social science fiction", 4, 4),
                ("Pride and Prejudice", "Jane Austen", "9780141439518", 1813, "Romance", "A romantic novel of manners", 2, 2),
                ("The Hobbit", "J.R.R. Tolkien", "9780547928227", 1937, "Fantasy", "Fantasy novel and prelude to Lord of the Rings", 3, 3),
                ("The Catcher in the Rye", "J.D. Salinger", "9780316769488", 1951, "Fiction", "Story of teenage angst and alienation", 2, 2),
                ("The Lord of the Rings", "J.R.R. Tolkien", "9780618640157", 1954, "Fantasy", "Epic high-fantasy novel", 3, 3),
                ("Animal Farm", "George Orwell", "9780451526342", 1945, "Satire", "Allegorical novella", 4, 4),
                ("The Da Vinci Code", "Dan Brown", "9780307474278", 2003, "Mystery", "Mystery thriller novel", 5, 5),
                ("Harry Potter and the Sorcerer's Stone", "J.K. Rowling", "9780590353427", 1997, "Fantasy", "Fantasy novel", 6, 6)
            ]
            
            cursor.executemany("""
                INSERT INTO Books (title, author, isbn, publication_year, genre, description, total_copies, available_copies)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, sample_books)
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("Database and tables created successfully!")
        return True
    except mysql.connector.Error as err:
        messagebox.showerror("Database Setup Error", f"Failed to set up database: {err}")
        return False

# ------------------- Main Application Class -------------------
class LibraryManagementSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Library Management System")
        self.root.geometry("800x600")
        
        # Set appearance mode and default color theme
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")
        
        # Create the main frame
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True)
        
        # Title and welcome message
        title_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(50, 20))
        
        # Title
        title_label = ctk.CTkLabel(
            title_frame,
            text="Library Management System",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#116636"
        )
        title_label.pack()
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="Your Gateway to Knowledge and Discovery",
            font=ctk.CTkFont(size=14),
            text_color="#555555"
        )
        subtitle_label.pack(pady=(5, 0))
        
        # Try to load and display a library image
        try:
            self.setup_image()
        except Exception as e:
            print(f"Could not load image: {e}")
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        buttons_frame.pack(pady=40)
        
        # Login button
        login_button = ctk.CTkButton(
            buttons_frame,
            text="User Login",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#116636",
            hover_color="#0d4f29",
            width=200,
            height=50,
            corner_radius=8,
            command=self.open_login
        )
        login_button.pack(pady=10)
        
        # Signup button
        signup_button = ctk.CTkButton(
            buttons_frame,
            text="New User? Sign Up",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2196f3",
            hover_color="#1976d2",
            width=200,
            height=50,
            corner_radius=8,
            command=self.open_signup
        )
        signup_button.pack(pady=10)
        
        # Admin button
        admin_button = ctk.CTkButton(
            buttons_frame,
            text="Admin Login",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#757575",
            hover_color="#616161",
            width=200,
            height=50,
            corner_radius=8,
            command=self.open_admin
        )
        admin_button.pack(pady=10)
        
        # Footer with information
        footer_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        footer_frame.pack(side="bottom", fill="x", padx=20, pady=20)
        
        # Add default admin credentials if we just created the database
        if not check_database_exists():
            create_database()
            admin_info = ctk.CTkLabel(
                footer_frame,
                text="Default Admin Login: admin@library.com / Password: admin123",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#116636"
            )
            admin_info.pack()
    
    def setup_image(self):
        """Try to load and display a library image"""
        # Check for predefined image first
        image_path = "library.png"
        
        if not os.path.exists(image_path):
            # No image found - create a placeholder
            image_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            image_frame.pack(pady=20)
            
            placeholder = ctk.CTkLabel(
                image_frame,
                text="📚",
                font=ctk.CTkFont(size=120),
                text_color="#116636"
            )
            placeholder.pack()
        else:
            # Image found - display it
            image_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            image_frame.pack(pady=20)
            
            # Load and resize the image
            pil_image = Image.open(image_path)
            pil_image = pil_image.resize((300, 200))
            img = ImageTk.PhotoImage(pil_image)
            
            # Create image label
            image_label = tk.Label(image_frame, image=img, bg="#F0F0F0")
            image_label.image = img  # Keep a reference to avoid garbage collection
            image_label.pack()
    
    def open_login(self):
        """Open the login page"""
        self.root.destroy()
        os.system("python login.py")
    
    def open_signup(self):
        """Open the signup page"""
        self.root.destroy()
        os.system("python signup.py")
    
    def open_admin(self):
        """Open the admin page"""
        self.root.destroy()
        os.system("python admin.py")

# ------------------- Main Execution -------------------
if __name__ == "__main__":
    # Check and create database if needed
    if not check_database_exists():
        print("Setting up database...")
        if not create_database():
            sys.exit(1)
    
    # Check if required files exist
    required_files = ["login.py", "signup.py", "admin.py", "home.py", "browse.py", "borrow.py"]
    missing_files = [file for file in required_files if not os.path.exists(file)]
    
    if missing_files:
        messagebox.showwarning(
            "Missing Files", 
            f"The following required files are missing:\n{', '.join(missing_files)}\n\n"
            "Some features may not work correctly."
        )
    
    # Start the application
    root = ctk.CTk()
    app = LibraryManagementSystem(root)
    root.mainloop()