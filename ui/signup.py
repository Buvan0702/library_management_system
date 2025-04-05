import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image, ImageTk
import mysql.connector
import hashlib
import os
import re

# Set appearance mode and default color theme for CustomTkinter
ctk.set_appearance_mode("light")  # Modes: "System", "Dark", "Light"
ctk.set_default_color_theme("green")  # Themes: "blue", "green", "dark-blue"

# ------------------- Database Connection -------------------
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",  # Replace with your MySQL username
        password="new_password",  # Replace with your MySQL password
        database="library_system"  # Replace with your database name
    )

# ------------------- Password Hashing -------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ------------------- Email Validation -------------------
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

# ------------------- Sign Up Function -------------------
def signup_user():
    full_name = full_name_entry.get().strip()
    email = email_entry.get().strip()
    password = password_entry.get()
    confirm_password = confirm_password_entry.get()

    # Check if any fields are empty
    if not full_name or not email or not password or not confirm_password:
        messagebox.showwarning("Input Error", "All fields are required.")
        return

    # Validate email format
    if not is_valid_email(email):
        messagebox.showwarning("Email Error", "Please enter a valid email address.")
        return

    # Check if passwords match
    if password != confirm_password:
        messagebox.showwarning("Password Error", "Passwords do not match.")
        return

    # Hash the password
    hashed_password = hash_password(password)

    try:
        connection = connect_db()
        cursor = connection.cursor()

        # Check if email already exists
        cursor.execute("SELECT * FROM Users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            messagebox.showwarning("Email Error", "Email already exists. Please use a different email.")
            return

        # Split full name into first and last name (best effort)
        name_parts = full_name.split()
        first_name = name_parts[0] if name_parts else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        # Insert the user data into the database
        cursor.execute(
            "INSERT INTO Users (first_name, last_name, email, password, role) VALUES (%s, %s, %s, %s, %s)",
            (first_name, last_name, email, hashed_password, "member")
        )

        connection.commit()
        messagebox.showinfo("Success", "User registered successfully!")
        
        # After successful registration, redirect to login page
        open_login_page()

    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- Open Login Page -------------------
def open_login_page():
    try:
        root.destroy()
        os.system("python login.py")
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open login page: {e}")

# ----------------- Setup Main Window -----------------
root = ctk.CTk()
root.title("Library Management System - Sign Up")
root.geometry("1200x800")
root.resizable(False, False)

# Create main frame with rounded corners
main_frame = ctk.CTkFrame(root, fg_color="white", corner_radius=15, border_width=2, border_color="#15aa3e")
main_frame.pack(fill="both", expand=True, padx=20, pady=20)

# Create two columns (left for image, right for signup form)
left_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=0)
left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

right_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=0)
right_frame.pack(side="right", fill="both", expand=True, padx=40, pady=40)

# Add signup heading to the right frame
heading_label = ctk.CTkLabel(
    right_frame, 
    text="Create an Account", 
    font=ctk.CTkFont(family="Arial", size=30, weight="bold"),
    text_color="#15aa3e"
)
heading_label.pack(pady=(20, 10))

# Add descriptive text
desc_text = "Sign up to explore books, borrow items, and manage your library account."
desc_label = ctk.CTkLabel(
    right_frame,
    text=desc_text,
    font=ctk.CTkFont(family="Arial", size=12),
    text_color="gray"
)
desc_label.pack(pady=(0, 30))

# Full Name Entry
full_name_label = ctk.CTkLabel(
    right_frame,
    text="Full Name",
    font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
    text_color="#333333",
    anchor="w"
)
full_name_label.pack(anchor="w", pady=(0, 5))

full_name_entry = ctk.CTkEntry(
    right_frame,
    width=350,
    height=40,
    font=ctk.CTkFont(family="Arial", size=13),
    border_width=1,
    corner_radius=5,
    placeholder_text=" "
)
full_name_entry.pack(pady=(0, 15))

# Email Entry
email_label = ctk.CTkLabel(
    right_frame,
    text="Email Address",
    font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
    text_color="#333333",
    anchor="w"
)
email_label.pack(anchor="w", pady=(0, 5))

email_entry = ctk.CTkEntry(
    right_frame,
    width=350,
    height=40,
    font=ctk.CTkFont(family="Arial", size=13),
    border_width=1,
    corner_radius=5,
    placeholder_text=" "
)
email_entry.pack(pady=(0, 15))

# Password Entry
password_label = ctk.CTkLabel(
    right_frame,
    text="Password",
    font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
    text_color="#333333",
    anchor="w"
)
password_label.pack(anchor="w", pady=(0, 5))

password_entry = ctk.CTkEntry(
    right_frame,
    width=350,
    height=40,
    font=ctk.CTkFont(family="Arial", size=13),
    border_width=1,
    corner_radius=5,
    placeholder_text=" ",
    show="•"
)
password_entry.pack(pady=(0, 15))

# Confirm Password Entry
confirm_password_label = ctk.CTkLabel(
    right_frame,
    text="Confirm Password",
    font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
    text_color="#333333",
    anchor="w"
)
confirm_password_label.pack(anchor="w", pady=(0, 5))

confirm_password_entry = ctk.CTkEntry(
    right_frame,
    width=350,
    height=40,
    font=ctk.CTkFont(family="Arial", size=13),
    border_width=1,
    corner_radius=5,
    placeholder_text=" ",
    show="•"
)
confirm_password_entry.pack(pady=(0, 25))

# Sign Up Button
signup_button = ctk.CTkButton(
    right_frame,
    text="Sign Up",
    font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
    corner_radius=5,
    height=45,
    width=350,
    fg_color="#15aa3e",
    hover_color="#0d7f2f",
    text_color="white",
    command=signup_user
)
signup_button.pack(pady=(5, 15))

# Already have an account link
login_link = ctk.CTkButton(
    right_frame,
    text="Already have an account? Login here",
    font=ctk.CTkFont(family="Arial", size=12),
    fg_color="transparent",
    hover_color="#f0f0f0",
    text_color="#15aa3e",
    width=30,
    command=open_login_page
)
login_link.pack(pady=(5, 0))

# Try to load the illustration image for the left side
try:
    # Load and resize the image
    image_path = "library.png"  # Replace with your image path
    pil_image = Image.open(image_path)
    pil_image = pil_image.resize((600, 600))
    img = ImageTk.PhotoImage(pil_image)
    
    # Create image label
    image_label = tk.Label(left_frame, image=img, bg="white")
    image_label.image = img  # Keep a reference to avoid garbage collection
    image_label.pack(pady=50)
except Exception as e:
    # If image loading fails, display a placeholder text
    print(f"Error loading image: {e}")
    placeholder = ctk.CTkLabel(
        left_frame,
        text="Library\nManagement\nSystem",
        font=ctk.CTkFont(family="Arial", size=32, weight="bold"),
        text_color="#15aa3e"
    )
    placeholder.pack(expand=True)

# Start the application
root.mainloop()