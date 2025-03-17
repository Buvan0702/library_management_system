import tkinter as tk
from tkinter import ttk

# Initialize main window
root = tk.Tk()
root.title("Library User - Dashboard")
root.geometry("1000x600")
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

# ---------------- Dashboard Title ---------------- #
title_label = tk.Label(root, text="Welcome to Your Library Dashboard", font=("Arial", 14, "bold"), bg="#E6F4E6")
title_label.place(x=300, y=20)

# ---------------- Dashboard Summary ---------------- #
summary_data = [
    ("Books Borrowed", "3"),
    ("Due Books", "1"),
    ("Pending Fines", "$5.00")
]

x_pos = 300
for title, value in summary_data:
    frame = tk.Frame(root, bg="white", width=180, height=80, highlightbackground="gray", highlightthickness=1)
    frame.place(x=x_pos, y=60)
    tk.Label(frame, text=title, font=("Arial", 10, "bold"), bg="white").place(x=10, y=10)
    tk.Label(frame, text=value, font=("Arial", 12), fg="black", bg="white").place(x=10, y=40)
    x_pos += 200

# ---------------- Search for Books ---------------- #
search_label = tk.Label(root, text="🔍 Search for Books", font=("Arial", 12, "bold"), bg="#E6F4E6")
search_label.place(x=300, y=160)

search_entry = tk.Entry(root, font=("Arial", 10), width=50)
search_entry.place(x=300, y=190)

search_button = tk.Button(root, text="🔍 Search", font=("Arial", 10), fg="white", bg="blue")
search_button.place(x=650, y=188)

# ---------------- My Borrowed Books ---------------- #
borrowed_books_label = tk.Label(root, text="📖 My Borrowed Books", font=("Arial", 12, "bold"), bg="#E6F4E6")
borrowed_books_label.place(x=300, y=230)

borrowed_books_tree = ttk.Treeview(root, columns=("Title", "Author", "Due Date", "Fine", "Action"), show="headings")
borrowed_books_tree.place(x=300, y=260, width=680, height=80)

# Define column headings
borrowed_books_tree.heading("Title", text="Title")
borrowed_books_tree.heading("Author", text="Author")
borrowed_books_tree.heading("Due Date", text="Due Date")
borrowed_books_tree.heading("Fine", text="Fine")
borrowed_books_tree.heading("Action", text="Action")

# Add Data
borrowed_books_tree.insert("", "end", values=("The Great Gatsby", "F. Scott Fitzgerald", "2025-06-15", "$0.00", "✅ Return"))
borrowed_books_tree.insert("", "end", values=("1984", "George Orwell", "2025-06-10", "$5.00", "❌ Pay Fine"))

# Run Tkinter main loop
root.mainloop()
