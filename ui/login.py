import tkinter as tk
from tkinter import messagebox, Entry, StringVar
import customtkinter as ctk
from PIL import Image, ImageTk
import mysql.connector
import hashlib
import os
import json

# Set appearance mode and default color theme for CustomTkinter
ctk.set_appearance_mode("light")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("green")  # Themes: "blue" (standard), "green", "dark-blue"

# ------------------- Database Configuration -------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "new_password",
    "database": "library_system"
}

SESSION_FILE = 'user_session.json'

# ------------------- Database Connection -------------------
def connect_db():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        messagebox.showerror("Database Connection Error", f"Failed to connect to database: {err}")
        return None

# ------------------- Password Hashing -------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ------------------- Session Management -------------------
def save_session(user_data):
    """Save user data to session file"""
    with open(SESSION_FILE, 'w') as f:
        json.dump(user_data, f)

# ------------------- Login Function -------------------
def login_user():
    email = email_entry.get()
    password = password_entry.get()

    if not email or not password:
        messagebox.showwarning("Input Error", "Please enter both email and password.")
        return

    hashed_password = hash_password(password)

    try:
        connection = connect_db()
        if not connection:
            return
            
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT user_id, first_name, last_name, email, role FROM Users WHERE email = %s AND password = %s",
            (email, hashed_password)
        )
        user = cursor.fetchone()

        if user:
            # Save user session
            save_session(user)
            
            # Show success message
            messagebox.showinfo("Success", f"Welcome {user['first_name']} {user['last_name']}!")
            
            # Close the login window and open home page
            root.destroy()
            os.system("python home.py")
        else:
            messagebox.showerror("Login Failed", "Invalid Email or Password.")
    
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- Open Sign Up Page -------------------
def open_signup_page():
    root.destroy()
    os.system("python signup.py")

# ------------------- Forgot Password Function -------------------
def forgot_password():
    email = email_entry.get()
    if not email:
        messagebox.showwarning("Input Required", "Please enter your email address first.")
        return
        
    messagebox.showinfo("Password Reset", 
                       f"A password reset link would be sent to {email}.\n"
                       "This feature would be implemented in a real system.")

# ------------------- Create Main Window -------------------
root = ctk.CTk()
root.title("Library Management System")
root.geometry("1000x600")
root.resizable(False, False)

# Create main frame with rounded corners
main_frame = ctk.CTkFrame(root, fg_color="white", corner_radius=15)
main_frame.pack(fill="both", expand=True, padx=20, pady=20)

# Create two columns (left for image, right for login)
left_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=0)
left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

right_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=0)
right_frame.pack(side="right", fill="both", expand=True, padx=40, pady=40)

# Add login heading to the right frame
heading_label = ctk.CTkLabel(
    right_frame, 
    text="Library Login", 
    font=ctk.CTkFont(family="Arial", size=32, weight="bold"),
    text_color="#15883e"
)
heading_label.pack(pady=(20, 10))

# Add descriptive text
desc_text = "Access thousands of books, track borrowed items, and manage\nyour library account effortlessly."
desc_label = ctk.CTkLabel(
    right_frame,
    text=desc_text,
    font=ctk.CTkFont(family="Arial", size=12),
    text_color="gray"
)
desc_label.pack(pady=(0, 30))

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
    corner_radius=5
)
email_entry.pack(pady=(0, 20))

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
    show="•"
)
password_entry.pack(pady=(0, 30))

# Login Button
login_button = ctk.CTkButton(
    right_frame,
    text="Login",
    font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
    corner_radius=5,
    height=45,
    width=350,
    fg_color="#15883e",
    hover_color="#0d6f2f",
    text_color="white",
    command=login_user
)
login_button.pack(pady=(0, 20))

# Links Frame
links_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
links_frame.pack(fill="x", pady=(0, 20))

# Forgot Password Link
forgot_link = ctk.CTkButton(
    links_frame,
    text="🔑 Forgot Password?",
    font=ctk.CTkFont(family="Arial", size=12),
    fg_color="transparent",
    hover_color="#f0f0f0",
    text_color="#15883e",
    width=30,
    command=forgot_password
)
forgot_link.pack(side="left")

# Spacer
spacer_label = ctk.CTkLabel(links_frame, text="|", text_color="#15883e")
spacer_label.pack(side="left", padx=20)

# Sign Up Link
signup_link = ctk.CTkButton(
    links_frame,
    text="👤 New User? Sign Up Here",
    font=ctk.CTkFont(family="Arial", size=12),
    fg_color="transparent",
    hover_color="#f0f0f0",
    text_color="#15883e",
    width=30,
    command=open_signup_page
)
signup_link.pack(side="left")

# Try to load the illustration image for the left side
try:
    # Load and resize the image
    image_path = "library.png"  # Replace with your image path
    pil_image = Image.open(image_path)
    pil_image = pil_image.resize((400, 400))
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
        text_color="#15883e"
    )
    placeholder.pack(expand=True)

# Start the application
root.mainloop()