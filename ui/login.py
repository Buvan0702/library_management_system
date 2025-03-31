import tkinter as tk
from tkinter import Entry, Label, Button
from tkinter import messagebox
from PIL import Image, ImageTk
import mysql.connector
import hashlib
import subprocess  # To open signup.py and home.py

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
        cursor = connection.cursor()
        cursor.execute(
            "SELECT first_name, last_name FROM Users WHERE email = %s AND password = %s",
            (email, hashed_password)
        )
        user = cursor.fetchone()

        if user:
            first_name, last_name = user
            messagebox.showinfo("Success", f"Welcome {first_name} {last_name}!")
            root.destroy()  # Close the login window upon successful login
            open_home_page()  # Open the home page after login
        else:
            messagebox.showerror("Login Failed", "Invalid Email or Password.")
    
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- Open Home Page -------------------
def open_home_page():
    try:
        subprocess.Popen(["python", "home.py"])  # Open home.py after successful login
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open home page: {e}")

# ------------------- Open Sign Up Page -------------------
def open_signup_page():
    try:
        subprocess.Popen(["python", "signup.py"])  # Open signup.py when Sign Up is clicked
        root.quit()  # Close the login window
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open signup page: {e}")

# ---------------- Initialize main window ----------------
root = tk.Tk()
root.title("Library Login")
root.geometry("850x400")
root.configure(bg="#0D3B17")  # Dark green background

# ---------------- Background Frame ---------------- #
background_frame = tk.Frame(root, bg="#1B8D3D", width=830, height=380, bd=2, relief="flat")
background_frame.place(relx=0.5, rely=0.5, anchor="center")

# ---------------- Login Card ---------------- #
login_frame = tk.Frame(background_frame, bg="white", width=780, height=300, bd=2, relief="flat")
login_frame.place(relx=0.5, rely=0.5, anchor="center")

# ---------------- Login Title ---------------- #
title_label = Label(login_frame, text="Library Login", font=("Arial", 14, "bold"), bg="white", fg="green")
title_label.place(x=450, y=30)

subtitle_label = Label(login_frame, text="Access thousands of books, track borrowed items, and manage\n"
                                         "your library account effortlessly.",
                        font=("Arial", 9), bg="white", fg="gray", justify="left")
subtitle_label.place(x=450, y=55)

# ---------------- Email Entry ---------------- #
email_label = Label(login_frame, text="Email Address", font=("Arial", 10, "bold"), bg="white")
email_label.place(x=450, y=100)
email_entry = Entry(login_frame, font=("Arial", 10), bd=1, relief="solid", width=35)
email_entry.place(x=450, y=120)

# ---------------- Password Entry ---------------- #
password_label = Label(login_frame, text="Password", font=("Arial", 10, "bold"), bg="white")
password_label.place(x=450, y=150)

password_entry = Entry(login_frame, font=("Arial", 10), bd=1, relief="solid", width=35, show="*")
password_entry.place(x=450, y=170)

# ---------------- Login Button ---------------- #
login_button = Button(login_frame, text="  ✅ Login", font=("Arial", 10, "bold"), bg="green", fg="white",
                      bd=0, width=32, height=1, command=login_user)
login_button.place(x=450, y=200)

# ---------------- Links (Forgot Password & Sign Up) ---------------- #
forgot_label = Label(login_frame, text="🔗 Forgot Password?", font=("Arial", 9, "bold"),
                     bg="white", fg="green", cursor="hand2")
forgot_label.place(x=450, y=240)

signup_label = Label(login_frame, text="👤 New User? Sign Up Here", font=("Arial", 9, "bold"),
                     bg="white", fg="green", cursor="hand2")
signup_label.place(x=570, y=240)

# Bind Sign Up link to open signup.py
signup_label.bind("<Button-1>", lambda e: open_signup_page())  # Open the sign-up page when clicked

# ---------------- Illustration Image ---------------- #
try:
    image = Image.open("library_illustration.png")  # Load an image (Use an appropriate path)
    image = image.resize((250, 200))
    img = ImageTk.PhotoImage(image)
    img_label = Label(login_frame, image=img, bg="white")
    img_label.place(x=40, y=70)
except:
    print("Image not found. Make sure 'library_illustration.png' is in the correct path.")

# Run Tkinter main loop
root.mainloop()
