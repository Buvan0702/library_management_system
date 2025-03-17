import tkinter as tk
from tkinter import ttk

# Initialize main window
root = tk.Tk()
root.title("Library Admin Dashboard")
root.geometry("1000x600")
root.configure(bg="#E6F4E6")  # Light green background

# ---------------- Sidebar (Left Panel) ---------------- #
sidebar = tk.Frame(root, bg="#116611", width=200, height=600)
sidebar.place(x=0, y=0)

# Sidebar Title
title_label = tk.Label(sidebar, text="📖 Library Admin", font=("Arial", 14, "bold"), fg="white", bg="#116611", anchor="w")
title_label.place(x=20, y=20)

# Sidebar Buttons
menu_items = ["📊 Dashboard", "👥 Manage Users", "⚙️ Settings", "🚪 Logout"]
y_pos = 60
for item in menu_items:
    button = tk.Button(sidebar, text=item, font=("Arial", 10), fg="white", bg="#116611", bd=0, anchor="w")
    button.place(x=20, y=y_pos, width=160)
    y_pos += 40

# ---------------- Dashboard Title ---------------- #
title_label = tk.Label(root, text="Library Admin Dashboard", font=("Arial", 14, "bold"), bg="#E6F4E6")
title_label.place(x=350, y=20)

# ---------------- Summary Cards ---------------- #
card_frame = tk.Frame(root, bg="#E6F4E6")
card_frame.place(x=220, y=60)

cards = [
    ("Total Books", "12,500"),
    ("Borrowed Books", "3,250"),
    ("Registered Users", "4,800"),
    ("Pending Fines", "$1,200")
]

x_offset = 0
for title, value in cards:
    card = tk.Frame(card_frame, bg="white", width=180, height=80, bd=1, relief="solid")
    card.place(x=x_offset, y=0)
    
    title_label = tk.Label(card, text=title, font=("Arial", 10, "bold"), bg="white")
    title_label.place(x=10, y=10)
    
    value_label = tk.Label(card, text=value, font=("Arial", 14), fg="black", bg="white")
    value_label.place(x=10, y=40)
    
    x_offset += 190

# ---------------- Book Management Table ---------------- #
table_frame = tk.Frame(root, bg="#E6F4E6")
table_frame.place(x=220, y=160)

table_title = tk.Label(table_frame, text="📚 Manage Books", font=("Arial", 12, "bold"), bg="#E6F4E6")
table_title.pack()

columns = ("Title", "Author", "Genre", "Status", "Actions")
tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=5)
tree.pack()

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=140)

# Sample Data
books = [
    ("The Great Gatsby", "F. Scott Fitzgerald", "Fiction", "Available"),
    ("1984", "George Orwell", "Dystopian", "Issued")
]

for book in books:
    tree.insert("", "end", values=book)

# ---------------- Add New Book Button ---------------- #
add_button = tk.Button(root, text="+ Add New Book", font=("Arial", 10, "bold"), bg="blue", fg="white", padx=10, pady=5)
add_button.place(x=220, y=400)

# Run Tkinter main loop
root.mainloop()
