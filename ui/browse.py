import tkinter as tk
from tkinter import ttk

# Initialize main window
root = tk.Tk()
root.title("Library User - Browse Books")
root.geometry("1300x600")
root.configure(bg="#E6F4E6")  # Light green background

# ---------------- Sidebar (Left Panel) ---------------- #
sidebar = tk.Frame(root, bg="#116611", width=200, height=600)
sidebar.place(x=0, y=0)

# Sidebar Title
title_label = tk.Label(sidebar, text="📚 Library User", font=("Arial", 14, "bold"), fg="white", bg="#116611", anchor="w")
title_label.place(x=20, y=20)

# Sidebar Buttons
menu_items = ["🏠 Dashboard", "🔍 Search Books", "📖 My Borrowed Books", "💰 Fines & Fees", "👤 My Profile", "🚪 Logout"]
y_pos = 60
for item in menu_items:
    button = tk.Button(sidebar, text=item, font=("Arial", 10), fg="white", bg="#116611", bd=0, anchor="w")
    button.place(x=20, y=y_pos, width=160)
    y_pos += 40

# ---------------- Browse Books Title ---------------- #
title_label = tk.Label(root, text="Browse Books", font=("Arial", 14, "bold"), bg="#E6F4E6")
title_label.place(x=300, y=20)

# ---------------- Search Bar ---------------- #
search_bar = tk.Entry(root, font=("Arial", 12), width=50)
search_bar.place(x=300, y=60)

search_button = tk.Button(root, text="🔍 Search", font=("Arial", 10), bg="blue", fg="white")
search_button.place(x=720, y=60)

# ---------------- Category Buttons ---------------- #
categories = ["Fiction", "Non-Fiction", "Science", "Biography", "Mystery", "Fantasy"]
x_pos = 300
for category in categories:
    button = tk.Button(root, text=category, font=("Arial", 10), bg="#C5E1A5", relief="flat")
    button.place(x=x_pos, y=100)
    x_pos += 80

# ---------------- Book Cards ---------------- #
books = [
    {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "genre": "Fiction", "status": "Available"},
    {"title": "1984", "author": "George Orwell", "genre": "Dystopian", "status": "Issued"},
    {"title": "A Brief History of Time", "author": "Stephen Hawking", "genre": "Science", "status": "Available"}
]

x_pos = 300
for book in books:
    frame = tk.Frame(root, bg="white", width=250, height=120, highlightbackground="black", highlightthickness=1)
    frame.place(x=x_pos, y=140)

    title_label = tk.Label(frame, text=book["title"], font=("Arial", 12, "bold"), bg="white")
    title_label.place(x=10, y=10)

    author_label = tk.Label(frame, text=f"Author: {book['author']}", font=("Arial", 10), bg="white")
    author_label.place(x=10, y=35)

    genre_label = tk.Label(frame, text=f"Genre: {book['genre']}", font=("Arial", 10), bg="white")
    genre_label.place(x=10, y=55)

    status_label = tk.Label(frame, text=f"Status: {book['status']}", font=("Arial", 10),
                            fg="green" if book["status"] == "Available" else "red", bg="white")
    status_label.place(x=10, y=75)

    if book["status"] == "Available":
        borrow_button = tk.Button(frame, text="Borrow Book", font=("Arial", 10), bg="blue", fg="white")
        borrow_button.place(x=10, y=95)
    else:
        unavailable_label = tk.Label(frame, text="Unavailable", font=("Arial", 10, "bold"), fg="gray", bg="white")
        unavailable_label.place(x=10, y=95)

    x_pos += 270

# Run Tkinter main loop
root.mainloop()
