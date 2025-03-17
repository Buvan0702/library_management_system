import tkinter as tk
from tkinter import ttk

# Initialize main window
root = tk.Tk()
root.title("Library User - Borrowed Books")
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

# ---------------- Borrowed Books Title ---------------- #
title_label = tk.Label(root, text="My Borrowed Books", font=("Arial", 14, "bold"), bg="#E6F4E6")
title_label.place(x=300, y=20)

# ---------------- Borrowed Books Table ---------------- #
borrowed_frame = tk.Frame(root, bg="#E6F4E6")
borrowed_frame.place(x=220, y=60)

borrowed_columns = ("Title", "Author", "Borrowed Date", "Due Date", "Fine", "Action")
borrowed_tree = ttk.Treeview(borrowed_frame, columns=borrowed_columns, show="headings", height=3)
borrowed_tree.pack()

for col in borrowed_columns:
    borrowed_tree.heading(col, text=col)
    borrowed_tree.column(col, width=130)

# Sample Data for Borrowed Books
borrowed_books = [
    ("The Great Gatsby", "F. Scott Fitzgerald", "2025-06-01", "2025-06-15", "$0.00", "Return"),
    ("1984", "George Orwell", "2025-05-25", "2025-06-10", "$5.00", "Pay Fine / Return")
]

for book in borrowed_books:
    borrowed_tree.insert("", "end", values=book)

# ---------------- Borrowing History Title ---------------- #
history_label = tk.Label(root, text="🔄 Borrowing History", font=("Arial", 12, "bold"), bg="#E6F4E6")
history_label.place(x=300, y=180)

# ---------------- Borrowing History Table ---------------- #
history_frame = tk.Frame(root, bg="#E6F4E6")
history_frame.place(x=220, y=210)

history_columns = ("Title", "Author", "Borrowed Date", "Returned Date", "Fine Paid")
history_tree = ttk.Treeview(history_frame, columns=history_columns, show="headings", height=3)
history_tree.pack()

for col in history_columns:
    history_tree.heading(col, text=col)
    history_tree.column(col, width=130)

# Sample Data for Borrowing History
history_data = [
    ("To Kill a Mockingbird", "Harper Lee", "2025-05-10", "2025-05-20", "$0.00"),
    ("The Catcher in the Rye", "J.D. Salinger", "2025-04-15", "2025-05-01", "$2.00")
]

for history in history_data:
    history_tree.insert("", "end", values=history)

# Run Tkinter main loop
root.mainloop()
