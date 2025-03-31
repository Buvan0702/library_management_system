import tkinter as tk
from tkinter import Entry, Label, Button
from tkinter import messagebox
import mysql.connector
import hashlib
import subprocess  # To open login.py

# ------------------- Database Connection -------------------
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",  # Replace with your MySQL username
        password="your_password",  # Replace with your MySQL password
        database="library_system"  # Replace with your database name
    )

# ------------------- Password Hashing -------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ------------------- Sign Up Function -------------------
def signup_user():
    full_name = full_name_entry.get()
    email = email_entry.get()
    password = password_entry.get()
    confirm_password = confirm_password_entry.get()

    # Check if any fields are empty
    if not full_name or not email or not password or not confirm_password:
        messagebox.showwarning("Input Error", "All fields are required.")
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

        # Insert the user data into the database
        cursor.execute(
            "INSERT INTO Users (full_name, email, password) VALUES (%s, %s, %s)",
            (full_name, email, hashed_password)
        )

        connection.commit()
        messagebox.showinfo("Success", "User registered successfully!")
        
        # After successful registration, redirect to login page
        open_login_page()

    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- Open Login Page -------------------
def open_login_page():
    try:
        subprocess.Popen(["python", "login.py"])  # Open login.py when Sign Up is clicked
        root.quit()  # Close the signup window
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open login page: {e}")

# ----------------- Setup -----------------
root = tk.Tk()
root.title("Library Sign-Up")
root.geometry("850x500")  
root.configure(bg="#0D3B17")  # Dark green background

# ---------------- Background Frame ---------------- #
background_frame = tk.Frame(root, bg="#1B8D3D", width=830, height=480, bd=2, relief="flat")
background_frame.place(relx=0.5, rely=0.5, anchor="center")

# ---------------- Sign-Up Card ---------------- #
signup_frame = tk.Frame(background_frame, bg="white", width=780, height=380, bd=2, relief="flat")
signup_frame.place(relx=0.5, rely=0.5, anchor="center")

# ---------------- Sign-Up Title ---------------- #
title_label = Label(signup_frame, text="Create an Account", font=("Arial", 14, "bold"), bg="white", fg="green")
title_label.place(x=450, y=30)

subtitle_label = Label(signup_frame, text="Sign up to explore books, borrow items, and manage your library\naccount.",
                        font=("Arial", 9), bg="white", fg="gray", justify="left")
subtitle_label.place(x=450, y=55)

# ---------------- Full Name Entry ---------------- #
full_name_label = Label(signup_frame, text="Full Name", font=("Arial", 10, "bold"), bg="white")
full_name_label.place(x=450, y=100)

full_name_entry = Entry(signup_frame, font=("Arial", 10), bd=1, relief="solid", width=35)
full_name_entry.place(x=450, y=120)

# ---------------- Email Entry ---------------- #
email_label = Label(signup_frame, text="Email Address", font=("Arial", 10, "bold"), bg="white")
email_label.place(x=450, y=150)

email_entry = Entry(signup_frame, font=("Arial", 10), bd=1, relief="solid", width=35)
email_entry.place(x=450, y=170)

# ---------------- Password Entry ---------------- #
password_label = Label(signup_frame, text="Password", font=("Arial", 10, "bold"), bg="white")
password_label.place(x=450, y=200)

password_entry = Entry(signup_frame, font=("Arial", 10), bd=1, relief="solid", width=35, show="*")
password_entry.place(x=450, y=220)

# ---------------- Confirm Password Entry ---------------- #
confirm_password_label = Label(signup_frame, text="Confirm Password", font=("Arial", 10, "bold"), bg="white")
confirm_password_label.place(x=450, y=250)

confirm_password_entry = Entry(signup_frame, font=("Arial", 10), bd=1, relief="solid", width=35, show="*")
confirm_password_entry.place(x=450, y=270)

# ---------------- Sign-Up Button ---------------- #
signup_button = Button(signup_frame, text="  👤 Sign Up", font=("Arial", 10, "bold"), bg="green", fg="white",
                      bd=0, width=32, height=1, command=signup_user)
signup_button.place(x=450, y=300)

# ---------------- Already have an account? Login ---------------- #
login_label = Label(signup_frame, text="🔗 Already have an account? Login here", font=("Arial", 9, "bold"),
                     bg="white", fg="green", cursor="hand2")
login_label.place(x=450, y=340)

# ---------------- Illustration Image ---------------- #
try:
    image = Image.open("library_illustration.png")  # Load an image (Use an appropriate path)
    image = image.resize((250, 200))
    img = ImageTk.PhotoImage(image)
    img_label = Label(signup_frame, image=img, bg="white")
    img_label.place(x=40, y=120)
except:
    print("Image not found. Make sure 'library_illustration.png' is in the correct path.")

# Bind Login label to open login.py
login_label.bind("<Button-1>", lambda e: open_login_page())  # Open the login page when clicked

# Run Tkinter main loop
root.mainloop()
