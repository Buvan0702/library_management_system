import tkinter as tk
from tkinter import Entry, Label, Button
from PIL import Image, ImageTk

# Initialize main window
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
                      bd=0, width=32, height=1)
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

# Run Tkinter main loop
root.mainloop()
