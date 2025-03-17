import tkinter as tk
from tkinter import ttk

# Initialize main window
root = tk.Tk()
root.title("Library User - Fines & Payment")
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

# ---------------- Fines & Payment Title ---------------- #
title_label = tk.Label(root, text="Fines & Payment", font=("Arial", 14, "bold"), bg="#E6F4E6")
title_label.place(x=300, y=20)

# ---------------- Pending Fines Section ---------------- #
pending_fines_label = tk.Label(root, text="⚠ Pending Fines", font=("Arial", 12, "bold"), bg="#E6F4E6")
pending_fines_label.place(x=300, y=60)

pending_fines_tree = ttk.Treeview(root, columns=("Title", "Due Date", "Fine Amount", "Action"), show="headings")
pending_fines_tree.place(x=300, y=90, width=680, height=50)

# Define column headings
pending_fines_tree.heading("Title", text="Title")
pending_fines_tree.heading("Due Date", text="Due Date")
pending_fines_tree.heading("Fine Amount", text="Fine Amount")
pending_fines_tree.heading("Action", text="Action")

# Add Data
pending_fines_tree.insert("", "end", values=("1984", "2025-06-10", "$5.00", "❌ Pay Now"))

# ---------------- Payment History Section ---------------- #
payment_history_label = tk.Label(root, text="🔄 Payment History", font=("Arial", 12, "bold"), bg="#E6F4E6")
payment_history_label.place(x=300, y=160)

payment_history_tree = ttk.Treeview(root, columns=("Title", "Paid Amount", "Payment Date", "Status"), show="headings")
payment_history_tree.place(x=300, y=190, width=680, height=80)

# Define column headings
payment_history_tree.heading("Title", text="Title")
payment_history_tree.heading("Paid Amount", text="Paid Amount")
payment_history_tree.heading("Payment Date", text="Payment Date")
payment_history_tree.heading("Status", text="Status")

# Add Data
payment_history_tree.insert("", "end", values=("The Catcher in the Rye", "$2.00", "2025-05-05", "✅ Paid"))
payment_history_tree.insert("", "end", values=("To Kill a Mockingbird", "$0.00", "2025-05-20", "✔ No Fine"))

# Run Tkinter main loop
root.mainloop()
