import tkinter as tk
from tkinter import Entry, Label, Button
from PIL import Image, ImageTk

# Initialize main window
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
                      bd=0, width=32, height=1)
login_button.place(x=450, y=200)

# ---------------- Links (Forgot Password & Sign Up) ---------------- #
forgot_label = Label(login_frame, text="🔗 Forgot Password?", font=("Arial", 9, "bold"),
                     bg="white", fg="green", cursor="hand2")
forgot_label.place(x=450, y=240)

signup_label = Label(login_frame, text="👤 New User? Sign Up Here", font=("Arial", 9, "bold"),
                     bg="white", fg="green", cursor="hand2")
signup_label.place(x=570, y=240)

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
