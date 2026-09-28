import tkinter as tk
from PIL import Image, ImageTk
from tkinter import ttk, messagebox
from datetime import datetime 
import os 
import shutil
from tkinter import filedialog
import mysql.connector       
    

#demo theme.
NAVY = "#102F5F"
BLUE = "#2563EB"
LIGHT_BLUE = "#EAF3FF"
BACKGROUND = "#F5F8FF"
WHITE = "#FFFFFF"
TEXT = "#172033"
GREEN = "#DCFCE7"
YELLOW = "#FEF3C7"
RED = "#FEE2E2"
IN_APP_MODE = True
active_dialog = None


def open_in_app_dialog(width, height):
    """Show a full in-app page while preserving the single native window."""
    global active_dialog
    if active_dialog is not None and active_dialog.winfo_exists():
        active_dialog.destroy()
    active_dialog = tk.Frame(window, bg=BACKGROUND)
    active_dialog.place(relx=0, rely=0, relwidth=1, relheight=1)
    active_dialog.lift()
    return active_dialog


def maximize_window(target):
    """Use the available desktop area while retaining the normal Windows title bar."""
    try:
        target.state("zoomed")
    except tk.TclError:
        pass


def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Rakesh@",
        database="it_support"
    )

def add_ticket_history(cursor, ticket_id, action, changed_by, old_status=None, new_status=None):
    cursor.execute(
        """INSERT INTO ticket_history
           (ticket_id, action, changed_by, old_status, new_status)
           VALUES (%s, %s, %s, %s, %s)""",
        (ticket_id, action, changed_by, old_status, new_status)
    )
def show_ticket_history(parent, ticket_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT ticket_history.action,
               COALESCE(users.username, 'Unknown'),
               ticket_history.old_status,
               ticket_history.new_status,
               ticket_history.changed_at
        FROM ticket_history
        LEFT JOIN users ON ticket_history.changed_by = users.id
        WHERE ticket_history.ticket_id = %s
        ORDER BY ticket_history.changed_at ASC, ticket_history.id ASC
    """, (ticket_id,))

    history = cursor.fetchall()
    cursor.close()
    connection.close()

    history_window = tk.Toplevel(parent)
    setup_window(history_window,"Ticket History","1200x700")
    maximize_window(history_window)

    add_header(
        history_window,
        f"Ticket {ticket_id} - History",
        "Complete activity timeline",
        closable=IN_APP_MODE
    )

    table_frame = tk.Frame(history_window, bg=BACKGROUND)
    table_frame.pack(fill="both", expand=True, padx=20, pady=15)

    columns = ("Date & Time", "Action", "Changed By", "Old Status", "New Status")

    history_tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings"
    )

    configure_tree(history_tree)

    widths = (170, 250, 150, 150, 150)

    for column, width in zip(columns, widths):
        history_tree.heading(column, text=column)
        history_tree.column(column, width=width, anchor="center")

    history_tree.pack(fill="both", expand=True)

    if not history:
        history_tree.insert(
            "",
            tk.END,
            values=("—", "No history available", "—", "—", "—")
        )
    else:
        for action, changed_by, old_status, new_status, changed_at in history:
            old_status = old_status or "—"
            new_status = new_status or "—"

            history_tree.insert(
                "",
                tk.END,
                values=(
                    changed_at,
                    action,
                    changed_by,
                    old_status,
                    new_status
                )
            )
    add_button(history_window, "Close", history_window.destroy, 14, True).pack(side="bottom", pady=12)
def add_notification(cursor, user_id, ticket_id, message):
    cursor.execute("""
        INSERT INTO notifications (user_id, ticket_id, message)
        VALUES (%s, %s, %s)
    """, (user_id, ticket_id, message))

def notify_sla_breach(ticket_id, assigned_to):

    connection = get_connection()
    cursor = connection.cursor()

    message = f"Ticket #{ticket_id} has breached SLA."

    try:

        # ---------------------------------------------
        # NOTIFY ADMINS
        # ---------------------------------------------

        cursor.execute("""
            SELECT id
            FROM users
            WHERE role = 'Admin'
        """)

        admins = cursor.fetchall()

        for (admin_id,) in admins:

            cursor.execute("""
                SELECT COUNT(*)
                FROM notifications
                WHERE user_id = %s
                  AND ticket_id = %s
                  AND message = %s
            """, (
                admin_id,
                ticket_id,
                message
            ))

            exists = cursor.fetchone()[0]

            if exists == 0:

                add_notification(
                    cursor,
                    admin_id,
                    ticket_id,
                    message
                )

        # ---------------------------------------------
        # NOTIFY ASSIGNED IT SUPPORT
        # ---------------------------------------------

        if assigned_to:

            cursor.execute("""
                SELECT COUNT(*)
                FROM notifications
                WHERE user_id = %s
                  AND ticket_id = %s
                  AND message = %s
            """, (
                assigned_to,
                ticket_id,
                message
            ))

            exists = cursor.fetchone()[0]

            if exists == 0:

                add_notification(
                    cursor,
                    assigned_to,
                    ticket_id,
                    message
                )

        connection.commit()

    except Exception:

        connection.rollback()

    finally:

        cursor.close()
        connection.close()

def get_unread_notification_count(user_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM notifications
        WHERE user_id = %s AND is_read = 0
    """, (user_id,))

    count = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    return count

def edit_profile(user, profile_window):

    edit_window = open_in_app_dialog(720, 700)

    add_header(
        edit_window,
        "Edit Profile",
        "Update your account information",
        closable=True
    )

    card = tk.Frame(
        edit_window,
        bg=WHITE,
        highlightbackground="#D7E4FA",
        highlightthickness=1
    )
    card.pack(
        fill="x",
        padx=70,
        pady=25
    )

    # ==================================================
    # USERNAME
    # ==================================================

    tk.Label(
        card,
        text="Username",
        bg=WHITE,
        fg="#0B1F42",
        font=("Arial", 10, "bold")
    ).pack(
        anchor="w",
        padx=30,
        pady=(20, 6)
    )

    username_entry = tk.Entry(
        card,
        font=("Arial", 10),
        bg="#F7FAFF",
        fg=TEXT,
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightbackground="#C9DCF8",
        highlightcolor=BLUE
    )

    username_entry.pack(
        fill="x",
        padx=30,
        ipady=8
    )

    username_entry.insert(
        0,
        user[2]
    )

    # ==================================================
    # DEPARTMENT
    # ==================================================

    tk.Label(
        card,
        text="Department",
        bg=WHITE,
        fg="#0B1F42",
        font=("Arial", 10, "bold")
    ).pack(
        anchor="w",
        padx=30,
        pady=(15, 6)
    )

    department_entry = tk.Entry(
        card,
        font=("Arial", 10),
        bg="#F7FAFF",
        fg=TEXT,
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightbackground="#C9DCF8",
        highlightcolor=BLUE
    )

    department_entry.pack(
        fill="x",
        padx=30,
        ipady=8
    )

    department_entry.insert(
        0,
        user[5]
    )

    # ==================================================
    # NEW PASSWORD
    # ==================================================

    tk.Label(
        card,
        text="New Password",
        bg=WHITE,
        fg="#0B1F42",
        font=("Arial", 10, "bold")
    ).pack(
        anchor="w",
        padx=30,
        pady=(15, 6)
    )

    password_entry = tk.Entry(
        card,
        show="*",
        font=("Arial", 10),
        bg="#F7FAFF",
        fg=TEXT,
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightbackground="#C9DCF8",
        highlightcolor=BLUE
    )

    password_entry.pack(
        fill="x",
        padx=30,
        ipady=8
    )

    tk.Label(
        card,
        text="Leave blank if you don't want to change the password.",
        bg=WHITE,
        fg="#8093B8",
        font=("Arial", 8)
    ).pack(
        anchor="w",
        padx=30,
        pady=(2, 0)
    )

    # ==================================================
    # CONFIRM NEW PASSWORD
    # ==================================================

    tk.Label(
        card,
        text="Confirm New Password",
        bg=WHITE,
        fg="#0B1F42",
        font=("Arial", 10, "bold")
    ).pack(
        anchor="w",
        padx=30,
        pady=(12, 6)
    )

    confirm_password_entry = tk.Entry(
        card,
        show="*",
        font=("Arial", 10),
        bg="#F7FAFF",
        fg=TEXT,
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightbackground="#C9DCF8",
        highlightcolor=BLUE
    )

    confirm_password_entry.pack(
        fill="x",
        padx=30,
        ipady=8
    )

    # ==================================================
    # ROLE - DISPLAY ONLY
    # ==================================================

    tk.Label(
        card,
        text="Role",
        bg=WHITE,
        fg="#0B1F42",
        font=("Arial", 10, "bold")
    ).pack(
        anchor="w",
        padx=30,
        pady=(15, 6)
    )

    role_display = tk.Label(
        card,
        text=user[4],
        bg="#F1F5F9",
        fg="#6076A4",
        font=("Arial", 10),
        anchor="w"
    )

    role_display.pack(
        fill="x",
        padx=30,
        ipady=8
    )

    # ==================================================
    # PHOTO
    # ==================================================

    photo_label = tk.Label(
        card,
        text="No new photo selected",
        bg=WHITE,
        fg="#6076A4",
        font=("Arial", 9)
    )

    photo_label.pack(
        pady=(15, 5)
    )

    selected_photo = {
        "path": None
    }

    def choose_photo():

        file_path = filedialog.askopenfilename(
            title="Choose Profile Photo",
            filetypes=[
                ("Image Files", "*.jpg *.jpeg *.png")
            ]
        )

        if not file_path:
            return

        # ----------------------------------------------
        # FILE FORMAT VALIDATION
        # ----------------------------------------------

        extension = os.path.splitext(file_path)[1].lower()

        if extension not in (".jpg", ".jpeg", ".png"):
            messagebox.showwarning(
                "Invalid Format",
                "Please select a JPG, JPEG, or PNG image.",
                parent=edit_window
            )
            return

        # ----------------------------------------------
        # FILE SIZE VALIDATION
        # ----------------------------------------------

        max_size = 2 * 1024 * 1024  # 2 MB

        if os.path.getsize(file_path) > max_size:
            messagebox.showwarning(
                "File Too Large",
                "Profile photo must be 2 MB or smaller.",
                parent=edit_window
            )
            return

        # ----------------------------------------------
        # IMAGE DIMENSION & RATIO VALIDATION
        # ----------------------------------------------

        try:
            image = Image.open(file_path)

            width, height = image.size

            if width < 150 or height < 150:
                image.close()

                messagebox.showwarning(
                    "Image Too Small",
                    "Profile photo must be at least 150 × 150 pixels.",
                    parent=edit_window
                )
                return

            if width > 2000 or height > 2000:
                image.close()

                messagebox.showwarning(
                    "Image Too Large",
                    "Profile photo must not exceed 2000 × 2000 pixels.",
                    parent=edit_window
                )
                return

            if width != height:
                image.close()

                messagebox.showwarning(
                    "Invalid Image Ratio",
                    "Profile photo must be a square image (1:1 ratio).",
                    parent=edit_window
                )
                return

            image.close()

        except Exception:
            messagebox.showerror(
                "Invalid Image",
                "The selected file could not be opened as an image.",
                parent=edit_window
            )
            return

        # ----------------------------------------------
        # PHOTO ACCEPTED
        # ----------------------------------------------

        selected_photo["path"] = file_path

        photo_label.config(
            text=os.path.basename(file_path),
            fg="#315A96"
        )

    tk.Button(
        card,
        text="📷 Change Photo",
        command=choose_photo,
        bg=WHITE,
        fg="#315A96",
        activebackground="#F1F6FF",
        activeforeground="#173F73",
        relief="solid",
        bd=1,
        highlightthickness=0,
        font=("Arial", 10, "bold"),
        cursor="hand2",
        padx=18,
        pady=7
    ).pack(
        pady=(0, 15)
    )

    # ==================================================
    # SAVE PROFILE
    # ==================================================

    def save_profile():

        username = username_entry.get().strip()
        department = department_entry.get().strip()

        new_password = password_entry.get()
        confirm_password = confirm_password_entry.get()

        # ----------------------------------------------
        # BASIC VALIDATION
        # ----------------------------------------------

        if not username or not department:

            messagebox.showwarning(
                "Missing Information",
                "Username and Department are required.",
                parent=edit_window
            )
            return

        # ----------------------------------------------
        # PASSWORD VALIDATION
        # ----------------------------------------------

        if new_password or confirm_password:

            if not new_password:

                messagebox.showwarning(
                    "Password Required",
                    "Please enter the new password.",
                    parent=edit_window
                )
                return

            if not confirm_password:

                messagebox.showwarning(
                    "Confirm Password",
                    "Please confirm the new password.",
                    parent=edit_window
                )
                return

            if new_password != confirm_password:

                messagebox.showwarning(
                    "Password Mismatch",
                    "New password and confirm password do not match.",
                    parent=edit_window
                )
                return

        connection = get_connection()
        cursor = connection.cursor()

        photo_filename = None

        try:

            # ------------------------------------------
            # CHECK DUPLICATE USERNAME
            # ------------------------------------------

            cursor.execute("""
                SELECT id
                FROM users
                WHERE username = %s
                  AND id != %s
            """, (
                username,
                user[0]
            ))

            existing_user = cursor.fetchone()

            if existing_user:

                messagebox.showwarning(
                    "Username Exists",
                    "This username is already being used.",
                    parent=edit_window
                )

                cursor.close()
                connection.close()
                return

            # ------------------------------------------
            # SAVE NEW PHOTO
            # ------------------------------------------

            if selected_photo["path"]:

                photos_folder = os.path.join(
                    os.path.dirname(__file__),
                    "photos"
                )

                os.makedirs(
                    photos_folder,
                    exist_ok=True
                )

                photo_filename = (
                    f"user_{user[0]}_"
                    f"{os.urandom(4).hex()}.jpg"
                )

                photo_destination = os.path.join(
                    photos_folder,
                    photo_filename
                )

                image = Image.open(
                    selected_photo["path"]
                )

                image = image.convert("RGB")

                image.save(
                    photo_destination,
                    "JPEG"
                )

                image.close()

            # ------------------------------------------
            # UPDATE DATABASE
            # ------------------------------------------

            if new_password:

                if photo_filename:

                    cursor.execute("""
                        UPDATE users
                        SET username = %s,
                            password = %s,
                            department = %s,
                            photo = %s
                        WHERE id = %s
                    """, (
                        username,
                        new_password,
                        department,
                        photo_filename,
                        user[0]
                    ))

                else:

                    cursor.execute("""
                        UPDATE users
                        SET username = %s,
                            password = %s,
                            department = %s
                        WHERE id = %s
                    """, (
                        username,
                        new_password,
                        department,
                        user[0]
                    ))

            else:

                if photo_filename:

                    cursor.execute("""
                        UPDATE users
                        SET username = %s,
                            department = %s,
                            photo = %s
                        WHERE id = %s
                    """, (
                        username,
                        department,
                        photo_filename,
                        user[0]
                    ))

                else:

                    cursor.execute("""
                        UPDATE users
                        SET username = %s,
                            department = %s
                        WHERE id = %s
                    """, (
                        username,
                        department,
                        user[0]
                    ))

            connection.commit()

        except Exception as error:

            connection.rollback()

            messagebox.showerror(
                "Profile Error",
                f"Profile could not be updated.\n\n{error}",
                parent=edit_window
            )

            cursor.close()
            connection.close()
            return

        cursor.close()
        connection.close()

        messagebox.showinfo(
            "Profile Updated",
            "Your profile has been updated successfully.",
            parent=edit_window
        )

        edit_window.destroy()
        profile_window.destroy()

        # ----------------------------------------------
        # LOAD UPDATED USER
        # ----------------------------------------------

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE id = %s",
            (user[0],)
        )

        updated_user = cursor.fetchone()

        cursor.close()
        connection.close()

        show_profile(updated_user)

    # ==================================================
    # BUTTONS
    # ==================================================

    button_frame = tk.Frame(
        edit_window,
        bg=BACKGROUND
    )

    button_frame.pack(
        pady=(0, 15)
    )

    tk.Button(
        button_frame,
        text="💾 Save Changes",
        command=save_profile,
        bg=BLUE,
        fg=WHITE,
        activebackground="#2858C7",
        activeforeground=WHITE,
        relief="flat",
        bd=0,
        font=("Arial", 10, "bold"),
        cursor="hand2",
        padx=22,
        pady=8
    ).pack(
        side="left",
        padx=5
    )

    tk.Button(
        button_frame,
        text="Cancel",
        command=edit_window.destroy,
        bg=WHITE,
        fg="#315A96",
        activebackground="#F1F6FF",
        activeforeground="#173F73",
        relief="solid",
        bd=1,
        font=("Arial", 10, "bold"),
        cursor="hand2",
        padx=22,
        pady=8
    ).pack(
        side="left",
        padx=5
    )

def show_profile(user):

    profile = open_in_app_dialog(720, 560)

    add_header(
        profile,
        "My Profile",
        "Your IT Support account information",
        closable=True
    )

    card = tk.Frame(
        profile,
        bg=WHITE,
        highlightbackground="#D7E4FA",
        highlightthickness=1
    )
    card.pack(
        fill="x",
        padx=70,
        pady=30
    )

    photo_path = None

    if user[6]:
        photo_path = os.path.join(
            os.path.dirname(__file__),
            "photos",
            user[6]
        )

    if photo_path and os.path.exists(photo_path):

        profile_image = Image.open(photo_path)
        profile_image.thumbnail((90, 90))

        profile_photo = ImageTk.PhotoImage(
            profile_image
        )

        photo_label = tk.Label(
            card,
            image=profile_photo,
            bg=WHITE
        )

        photo_label.image = profile_photo

        photo_label.pack(
            pady=(25, 8)
        )

    else:

        tk.Label(
            card,
            text="👤",
            bg=WHITE,
            fg=BLUE,
            font=("Arial", 32)
        ).pack(
            pady=(25, 8)
        )

    tk.Label(
        card,
        text=user[2],
        bg=WHITE,
        fg="#0B1F42",
        font=("Arial", 18, "bold")
    ).pack()

    tk.Label(
        card,
        text=user[4],
        bg=WHITE,
        fg="#5370A8",
        font=("Arial", 10)
    ).pack(
        pady=(2, 20)
    )

    details = tk.Frame(
        card,
        bg=WHITE
    )
    details.pack(
        fill="x",
        padx=60,
        pady=(0, 15)
    )

    profile_data = [
        ("Username", user[2]),
        ("Role", user[4]),
        ("Department", user[5])
    ]

    for label, value in profile_data:

        row = tk.Frame(
            details,
            bg="#F7FAFF"
        )
        row.pack(
            fill="x",
            pady=4
        )

        tk.Label(
            row,
            text=label,
            bg="#F7FAFF",
            fg="#6076A4",
            font=("Arial", 10, "bold"),
            width=15,
            anchor="w"
        ).pack(
            side="left",
            padx=12,
            pady=9
        )

        tk.Label(
            row,
            text=value,
            bg="#F7FAFF",
            fg=TEXT,
            font=("Arial", 10),
            anchor="w"
        ).pack(
            side="left",
            padx=10
        )

    tk.Button(
        profile,
        text="✏ Edit Profile",
        command=lambda: edit_profile(user, profile),
        bg=BLUE,
        fg=WHITE,
        activebackground="#2858C7",
        activeforeground=WHITE,
        relief="flat",
        bd=0,
        font=("Arial", 10, "bold"),
        cursor="hand2",
        padx=22,
        pady=8
    ).pack(
        pady=(0, 15)
    )

def show_current_profile(user_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE id = %s",
        (user_id,)
    )

    current_user = cursor.fetchone()

    cursor.close()
    connection.close()

    if current_user:
        show_profile(current_user)

def show_dashboard_menu(parent, user, refresh_command,workload_command):
    menu = tk.Menu(
        parent,
        tearoff=0,
        bg=WHITE,
        fg=NAVY,
        activebackground="#E8F1FF",
        activeforeground=NAVY,
        font=("Arial", 10)
    )

    menu.add_command(
        label="My Profile",
        command=lambda: show_current_profile(user[0])
    )

    menu.add_command(
        label="Refresh Dashboard",
        command=refresh_command
    )
    if workload_command:
        menu.add_command(
            label="Support Staff Workload",
            command=workload_command
        )
    menu.add_separator()

    menu.add_command(
        label="Logout",
        command=show_login_window
    )

    try:
        menu.tk_popup(
            parent.winfo_rootx() + parent.winfo_width() - 160,
            parent.winfo_rooty() + parent.winfo_height()
        )
    finally:
        menu.grab_release()

def show_notifications(user):
    notification_window = open_in_app_dialog(850, 430) if IN_APP_MODE else tk.Toplevel(window)
    if not IN_APP_MODE:
        setup_window(notification_window, "Notifications", "850x430")
    add_header(
        notification_window,
        "Notifications",
        "Your latest support updates",
        closable=IN_APP_MODE
    )

    table_frame = tk.Frame(notification_window, bg=BACKGROUND)
    table_frame.pack(fill="both", expand=True, padx=18, pady=18)

    columns = ("ID", "Ticket", "Message", "Status", "Date")

    notification_tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings"
    )

    configure_tree(notification_tree)

    widths = (60, 80, 300, 80, 130)

    for column, width in zip(columns, widths):
        notification_tree.heading(column, text=column)
        notification_tree.column(
            column,
            width=width,
            anchor="center" if column != "Message" else "w"
        )

    notification_tree.pack(fill="both", expand=True)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, ticket_id, message, is_read, created_at
        FROM notifications
        WHERE user_id = %s
        ORDER BY id DESC
    """, (user[0],))

    notifications = cursor.fetchall()

    for notification in notifications:
        notification_id, ticket_id, message, is_read, created_at = notification

        read_status = "Read" if is_read else "New"

        notification_tree.insert(
            "",
            tk.END,
            values=(
                notification_id,
                ticket_id,
                message,
                read_status,
                created_at.strftime("%Y-%m-%d %H:%M")
            )
        )

    cursor.close()
    connection.close()

    # Mark all unread notifications as read
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE notifications
        SET is_read = 1
        WHERE user_id = %s AND is_read = 0
    """, (user[0],))


    connection.commit()

    cursor.close()
    connection.close()

    add_button(
        notification_window,
        "Close",
        notification_window.destroy,
        18,
        True
    ).pack(side="bottom", pady=(0, 15))
 

def setup_window(target, title, size):
    target.title(title)
    target.geometry(size)
    target.configure(bg=BACKGROUND)


def add_header(parent, title, subtitle="", closable=False):
    header = tk.Frame(parent, bg=NAVY, height=78)
    header.pack(fill="x")
    header.pack_propagate(False)
    if closable:
        tk.Button(header, text="×", command=parent.destroy, bg=NAVY, fg=WHITE,
                  activebackground="#28528A", activeforeground=WHITE, relief="flat", bd=0,
                  cursor="hand2", font=("Arial", 20), padx=18).pack(side="right", fill="y")
    tk.Label(header, text=title, bg=NAVY, fg=WHITE,
             font=("Arial", 18, "bold")).pack(anchor="w", padx=24, pady=(14, 0))
    if subtitle:
        tk.Label(header, text=subtitle, bg=NAVY, fg="#C7D9F8",
                 font=("Arial", 10)).pack(anchor="w", padx=24, pady=(2, 0))


def add_button(parent, text, command, width=20, secondary=False):
    return tk.Button(
        parent, text=text, command=command, width=width,
        bg=WHITE if secondary else BLUE,
        fg=NAVY if secondary else WHITE,
        activebackground="#DCE8FF" if secondary else "#1D4ED8",
        activeforeground=NAVY if secondary else WHITE,
        relief="flat", bd=0, highlightthickness=0, cursor="hand2", font=("Arial", 10, "bold"), pady=7
    )


def show_login_window():
    global username_entry, password_entry

    if not window.winfo_exists():
        return

    for child in window.winfo_children():
        child.destroy()

    window.deiconify()
    window.geometry("1280x760")
    maximize_window(window)
    window.configure(bg="#EEF4FC")

    window.protocol(
        "WM_DELETE_WINDOW",
        window.destroy
    )

    top = tk.Frame(window, bg="#17365D", height=52)
    top.pack(fill="x")
    top.pack_propagate(False)
    tk.Label(top, text="◉  IT Support Management System", bg="#17365D",
             fg=WHITE, font=("Arial", 12, "bold")).pack(side="left", padx=20, pady=15)

    main = tk.Frame(window, bg="#EEF4FC")
    main.pack(fill="both", expand=True)
    main.columnconfigure(0, weight=1,uniform="login")
    main.columnconfigure(1, weight=1,uniform="login")
    main.rowconfigure(0, weight=1)

    left = tk.Frame(main, bg="#0F2E61")
    left.grid(row=0, column=0, sticky="nsew")
    left.grid_propagate(False) 
    left_image_label = tk.Label(left, bg="#0F2E61", bd=0)
    left_image_label.pack(fill="both", expand=True)

    image_path = os.path.join(os.path.dirname(__file__), "reference_left_panel.png")
    if os.path.exists(image_path):
        original = Image.open(image_path)
        def resize_reference(event=None):
            w, h = left.winfo_width(), left.winfo_height()
            if w > 1 and h > 1:
                photo = ImageTk.PhotoImage(original.resize((w, h), Image.Resampling.LANCZOS))
                left_image_label.config(image=photo)
                left_image_label.image = photo
        left.bind("<Configure>", resize_reference)
        left.after(100, resize_reference)
    else:
        tk.Label(left, text="🎧\nIT Support\nManagement System",
                 bg="#0F2E61", fg=WHITE, font=("Arial", 24, "bold"),
                 justify="center").place(relx=.5, rely=.5, anchor="center")

    right = tk.Frame(main, bg="#EEF4FC")
    right.grid(row=0, column=1, sticky="nsew")

    login_card = tk.Frame(right, bg=WHITE, highlightbackground="#C9DCF8",
                          highlightthickness=1)
    login_card.place(relx=.5, rely=.48, anchor="center", relwidth=.78, relheight=.88)

    tk.Label(login_card, text="🎧", bg=WHITE, fg=BLUE,
             font=("Segoe UI Emoji", 30)).pack(pady=(18, 2))
    tk.Label(login_card, text="Welcome Back!", bg=WHITE, fg="#163C78",
             font=("Arial", 22, "bold")).pack()
    tk.Label(login_card, text="Sign in to continue to your support dashboard",
             bg=WHITE, fg="#6076A4", font=("Arial", 9)).pack(pady=(4, 20))

    tk.Label(login_card, text="Username", bg=WHITE, fg="#3F5F98",
             font=("Arial", 10, "bold")).pack(anchor="w", padx=42)
    username_frame = tk.Frame(login_card, bg=WHITE,
                              highlightbackground="#C9DCF8", highlightthickness=1)
    username_frame.pack(fill="x", padx=42, pady=(5, 14))
    username_entry = tk.Entry(username_frame, font=("Arial", 12), relief="flat", bd=0)
    username_entry.pack(fill="x", ipady=9, padx=10)

    tk.Label(login_card, text="Password", bg=WHITE, fg="#3F5F98",
             font=("Arial", 10, "bold")).pack(anchor="w", padx=42)
    password_frame = tk.Frame(login_card, bg=WHITE,
                              highlightbackground="#C9DCF8", highlightthickness=1)
    password_frame.pack(fill="x", padx=42, pady=(5, 18))
    password_entry = tk.Entry(password_frame, show="•", font=("Arial", 12),
                              relief="flat", bd=0)
    password_entry.pack(side="left", fill="x", expand=True, ipady=9, padx=10)

    def toggle_password():
        if password_entry.cget("show") == "":
            password_entry.config(show="•")
            eye_button.config(text="Show")
        else:
            password_entry.config(show="")
            eye_button.config(text="Hide")

    eye_button = tk.Button(password_frame, text="Show", command=toggle_password,
                           bg=WHITE, fg="#5578B5", activebackground=WHITE,
                           activeforeground=BLUE, relief="flat", bd=0,
                           cursor="hand2", font=("Arial", 8, "bold"))
    eye_button.pack(side="right", padx=10)

    tk.Button(login_card, text="⇥   Login", command=login, bg=BLUE, fg=WHITE,
              activebackground="#174EC8", activeforeground=WHITE, relief="flat",
              cursor="hand2", font=("Arial", 12, "bold"), pady=11).pack(fill="x", padx=42)

    tk.Label(login_card, text="────────  Login access  ────────",
             bg=WHITE, fg="#5873A8", font=("Arial", 9)).pack(pady=(15, 8))
    role_cards = tk.Frame(login_card, bg=WHITE)
    role_cards.pack(fill="x", padx=35)
    for icon, title, subtitle, icon_color in [
        ("👤", "Employee", "Create & view\nyour tickets", "#2563EB"),
        ("🛠", "IT Support", "Manage & resolve\ntickets", "#12A66A"),
        ("⚙", "Admin", "Manage users,\nsettings & reports", "#7655D9")
    ]:
        role_card = tk.Frame(role_cards, bg="#F7FAFF",
                             highlightbackground="#D8E5FA", highlightthickness=1)
        role_card.pack(side="left", fill="both", expand=True, padx=4)
        tk.Label(role_card, text=icon, bg="#F7FAFF", fg=icon_color,
                 font=("Segoe UI Emoji", 18)).pack(pady=(8, 1))
        tk.Label(role_card, text=title, bg="#F7FAFF", fg="#163C78",
                 font=("Arial", 9, "bold")).pack()
        tk.Label(role_card, text=subtitle, bg="#F7FAFF", fg="#6076A4",
                 justify="center", font=("Arial", 7)).pack(pady=(2, 8))

    from datetime import datetime
    clock_label = tk.Label(right, bg="#EEF4FC", fg="#6076A4", font=("Arial", 9))
    clock_label.pack(side="bottom", pady=(0, 12))
    def update_clock():
        if clock_label.winfo_exists():
            clock_label.config(text="📅  " + datetime.now().strftime("%d %b %Y  |  %I:%M:%S %p"))
            clock_label.after(1000, update_clock)
    update_clock()

    password_entry.bind("<Return>", lambda event: login())
    username_entry.focus_set()


def hide_login_window():
    window.withdraw()


def configure_tree(tree):
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("Treeview", font=("Arial", 10), rowheight=30,
                    background=WHITE, fieldbackground=WHITE, foreground=TEXT)
    style.configure("Treeview.Heading", font=("Arial", 10, "bold"),
                    background=NAVY, foreground=WHITE, relief="raised", padding=(8, 7))
    style.map("Treeview.Heading", background=[("active", BLUE)])
    style.configure("TCombobox", font=("Arial", 10), padding=(8, 6),
                    fieldbackground=WHITE, background="#EAF2FF", foreground=TEXT,
                    bordercolor="#C9DCF8", lightcolor="#C9DCF8", darkcolor="#C9DCF8")
    style.map("TCombobox", fieldbackground=[("readonly", WHITE)],
              selectbackground=[("readonly", WHITE)], selectforeground=[("readonly", TEXT)])
    tree.tag_configure("OPEN", background=YELLOW)
    tree.tag_configure("ASSIGNED", background="#E0E7FF")
    tree.tag_configure("IN PROGRESS", background=LIGHT_BLUE)
    tree.tag_configure("RESOLVED", background=GREEN)



def insert_ticket(tree, values, status_index):
    tree.insert("", tk.END, values=values, tags=(values[status_index],))

def insert_category_ticket(tree, values, category_index):
    category = values[category_index]

    category_colors = {
        "Hardware": "#FFF3E0",
        "Software": "#F3E8FF",
        "Network": "#E0F2FE",
        "Access": "#FEF9C3",
        "Email": "#DCFCE7",
        "Other": "#F1F5F9"
    }

    tag_name = f"category_{category}"

    tree.tag_configure(
        tag_name,
        background=category_colors.get(category, WHITE)
    )

    tree.insert(
        "",
        tk.END,
        values=values,
        tags=(tag_name,)
    )


def login():
    username = username_entry.get().strip()
    password = password_entry.get()

    if not username or not password:
        messagebox.showwarning("Missing Login Details", "Enter your username and password.")
        return

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE BINARY username = BINARY %s
        AND BINARY password = BINARY %s
        """,
        (username, password)
    )

    user = cursor.fetchone()

    if user and user[7] == 0:
        messagebox.showwarning(
            "Account Deactivated",
            "Your account has been deactivated. Please contact the administrator."
        )
        cursor.close()
        connection.close()
        return

    if not user:
        messagebox.showerror("Login Failed", "Invalid username or password.")
        return

    role = user[4]
    if role == "Employee":
        employee_dashboard(user)
    elif role == "IT Support":
        it_support_dashboard(user)
    elif role == "Admin":
        admin_dashboard(user)

def contact_it_support(user):
    import webbrowser

    subject = f"IT Support Request - {user[1]}"
    mailto = f"mailto:itsupport@company.com?subject={subject}"

    webbrowser.open(mailto)


def employee_dashboard(user):
    for child in window.winfo_children():
        child.destroy()
    dashboard = window
    setup_window(dashboard, "Employee Dashboard", "1360x800")
    maximize_window(dashboard)
    dashboard.minsize(1100, 680)
    dashboard.protocol("WM_DELETE_WINDOW", dashboard.destroy)
    dashboard.configure(bg="#F5F8FF")

    
    main = tk.Frame(dashboard, bg="#F5F8FF")
    main.pack(side="left", fill="both", expand=True)
    topbar = tk.Frame(main, bg=WHITE, height=64)
    topbar.pack(fill="x")
    topbar.pack_propagate(False)
    body = tk.Frame(main, bg="#F5F8FF")
    body.pack(fill="both", expand=True, padx=28, pady=20)

    header = tk.Frame(topbar, bg=WHITE)
    header.pack(fill="both", expand=True, padx=28)

    def show_employee_menu():
            menu = tk.Menu(
                dashboard,
                tearoff=0,
                bg=WHITE,
                fg=NAVY,
                activebackground="#E8F1FF",
                activeforeground=NAVY,
                font=("Arial", 10)
            )
    
            menu.add_command(label="Dashboard", command=refresh_dashboard)
            menu.add_command(label="My Tickets", command=lambda: my_tickets(user))
            menu.add_command(label="New Ticket", command=lambda: create_ticket(user))
            menu.add_command(label="Ticket History", command=open_selected_history)
    
            menu.add_separator()
    
            menu.add_command(
                label="Contact IT Support",
                command=lambda: contact_it_support(user)
            )
    
            menu.add_separator()
    
            menu.add_command(label="My Profile", command=show_profile)
    
            menu.add_separator()
    
            menu.add_command(label="Logout", command=show_login_window)
    
            try:
                menu.tk_popup(
                    hamburger_button.winfo_rootx() - 130,
                    hamburger_button.winfo_rooty() + hamburger_button.winfo_height()
                )
            finally:
                menu.grab_release()
    
        
        
    
    hamburger_button = tk.Button(
        header,
        text="☰",
        command=show_employee_menu,
        bg=WHITE,
        fg=NAVY,
        activebackground="#E8F1FF",
        relief="flat",
        bd=0,
        font=("Arial", 16, "bold"),
        cursor="hand2",
        padx=8
    )
    hamburger_button.pack(side="right", padx=(8, 0))
    unread_var = tk.StringVar(
        value=f"🔔 {get_unread_notification_count(user[0])}"
    )
    tk.Button(
        header,
        textvariable=unread_var,
        command=lambda: (show_notifications(user), unread_var.set("🔔 0")),
        bg=WHITE,
        fg=NAVY,
        relief="flat",
        font=("Arial", 11, "bold"),
        cursor="hand2"
    ).pack(side="right", padx=(12, 0)) 
    tk.Label(header, text=f"●  {user[1]}", bg=WHITE, fg=NAVY,
             font=("Arial", 11, "bold")).pack(side="right")
    tk.Label(header, text="Employee", bg=WHITE, fg="#6076A4", font=("Arial", 9)).pack(side="right", padx=(0, 18))

    content = tk.Frame(body, bg="#F5F8FF")
    content.pack(side="left", fill="both", expand=True)
    right = tk.Frame(body, bg="#F5F8FF", width=255)
    right.pack(side="right", fill="y", padx=(18, 0))
    right.pack_propagate(False)

    tk.Label(content, text=f"Welcome back, {user[1]}!", bg="#F5F8FF", fg="#0B1F42",
             font=("Arial", 22, "bold")).pack(anchor="w")
    tk.Label(content, text="Here's what's happening with your support tickets.", bg="#F5F8FF", fg="#5370A8",
             font=("Arial", 11)).pack(anchor="w", pady=(3, 18))

    cards = tk.Frame(content, bg="#F5F8FF")
    cards.pack(fill="x", pady=(0, 18))
    card_specs = [
        ("Total Tickets", "All your tickets", "#E8F1FF", "#2563EB"),
        ("Open Tickets", "Need attention", "#FFF5DD", "#E59A00"),
        ("Resolved Tickets", "Completed", "#E6FBF1", "#0CA66B"),
        ("Critical Tickets", "High priority", "#FFEBED", "#E53E49"),
    ]
    card_vars = [tk.StringVar(value="0") for _ in card_specs]
    for index, ((title, subtitle, background, accent), value) in enumerate(zip(card_specs, card_vars)):
        card = tk.Frame(cards, bg=background, highlightbackground=accent, highlightthickness=1)
        card.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 9, 0))
        tk.Label(card, text=title, bg=background, fg="#183461", font=("Arial", 10, "bold")).pack(anchor="w", padx=16, pady=(13, 3))
        tk.Label(card, textvariable=value, bg=background, fg="#0B1F42", font=("Arial", 22, "bold")).pack(anchor="w", padx=16)
        tk.Label(card, text=subtitle, bg=background, fg="#5370A8", font=("Arial", 9)).pack(anchor="w", padx=16, pady=(2, 13))
        cards.columnconfigure(index, weight=1)

    table_card = tk.Frame(content, bg=WHITE, highlightbackground="#D7E4FA", highlightthickness=1)
    table_card.pack(fill="both", expand=True)
    table_heading = tk.Frame(table_card, bg=WHITE)
    table_heading.pack(fill="x", padx=18, pady=(16, 8))
    tk.Label(table_heading, text="My Tickets", bg=WHITE, fg="#0B1F42", font=("Arial", 16, "bold")).pack(side="left")
    add_button(table_heading, "+  New Ticket", lambda: create_ticket(user), 15).pack(side="right")

    filters = tk.Frame(table_card, bg=WHITE)
    filters.pack(fill="x", padx=18, pady=(0, 10))
    search_var = tk.StringVar()
    search_box = tk.Frame(filters, bg=WHITE, highlightbackground="#C9DCF8", highlightthickness=1)
    search_box.pack(side="right")
    tk.Button(search_box, text="🔎", command=lambda: refresh_dashboard(), bg=WHITE, fg="#5370A8",
              activebackground="#EAF3FF", activeforeground=BLUE, relief="flat", bd=0,
              cursor="hand2", font=("Arial", 15, "bold"), padx=9).pack(side="left")
    search_entry = tk.Entry(search_box, textvariable=search_var, width=23, font=("Arial", 10), relief="flat", bd=0)
    search_entry.pack(side="left", ipady=7, padx=(0, 8))
    status_var = tk.StringVar(value="All Status")
    priority_var = tk.StringVar(value="All Priorities")
    category_var = tk.StringVar(value="All Categories")
    for variable, options in ((category_var, ["All Categories", "Hardware", "Software", "Network", "Access", "Email", "Other"]),
                              (priority_var, ["All Priorities", "Low", "Medium", "High", "Critical"]),
                              (status_var, ["All Status", "OPEN", "ASSIGNED", "IN PROGRESS", "RESOLVED"])):
        ttk.Combobox(filters, textvariable=variable, values=options, state="readonly", width=15).pack(side="left", padx=(0, 7))

    ticket_frame = tk.Frame(table_card, bg=WHITE)
    ticket_frame.pack(fill="both", expand=True, padx=18, pady=(0, 15))
    columns = ("ID", "Title", "Category", "Priority", "Status", "Created On")
    ticket_tree = ttk.Treeview(ticket_frame, columns=columns, show="headings", height=10)
    configure_tree(ticket_tree)
    for column, width in zip(columns, (55, 245, 120, 90, 115, 155)):
        ticket_tree.heading(column, text=column)
        ticket_tree.column(column, width=width, anchor="w" if column == "Title" else "center")
    ticket_tree.pack(fill="both", expand=True)

    def open_selected_history():
        selected = ticket_tree.selection()
        if not selected:
            messagebox.showwarning("No Ticket Selected", "Select a ticket first.")
            return
        show_ticket_history(dashboard, ticket_tree.item(selected[0])["values"][0])

    def refresh_dashboard(*_):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT COUNT(*), SUM(status = 'OPEN'), SUM(status = 'RESOLVED'), SUM(priority = 'Critical') FROM tickets WHERE user_id = %s", (user[0],))
            total, open_count, resolved, critical = cursor.fetchone()
            for value, number in zip(card_vars, (total, open_count or 0, resolved or 0, critical or 0)):
                value.set(str(number))
            cursor.execute("SELECT COUNT(*) FROM notifications WHERE user_id = %s AND is_read = 0", (user[0],))
            unread_var.set(f"🔔 {cursor.fetchone()[0]}")
            ticket_tree.delete(*ticket_tree.get_children())
            query = "SELECT tickets.id, tickets.title, categories.category_name, tickets.priority, tickets.status, tickets.created_at FROM tickets JOIN categories ON tickets.category_id = categories.id WHERE tickets.user_id = %s"
            params = [user[0]]
            if category_var.get() != "All Categories":
                query += " AND categories.category_name = %s"; params.append(category_var.get())
            if priority_var.get() != "All Priorities":
                query += " AND tickets.priority = %s"; params.append(priority_var.get())
            if status_var.get() != "All Status":
                query += " AND tickets.status = %s"; params.append(status_var.get())
            if search_var.get().strip():
                query += " AND tickets.title LIKE %s"; params.append(f"%{search_var.get().strip()}%")
            cursor.execute(query + " ORDER BY tickets.id DESC", tuple(params))
            for ticket in cursor.fetchall():
                ticket_tree.insert("", tk.END, values=ticket, tags=(ticket[4],))
        finally:
            cursor.close(); connection.close()

    
    def show_profile():

        profile = open_in_app_dialog(720, 560)

        add_header(
            profile,
            "My Profile",
            "Your IT Support account information",
            closable=True
        )

        # --------------------------------------------------
        # GET LATEST USER DATA
        # --------------------------------------------------

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, name, username, password, role, department, photo
            FROM users
            WHERE id = %s
        """, (user[0],))

        current_user = cursor.fetchone()

        cursor.close()
        connection.close()

        if not current_user:
            messagebox.showerror(
                "Error",
                "Unable to load your profile.",
                parent=profile
            )
            profile.destroy()
            return

        user_id = current_user[0]
        name = current_user[1]
        username = current_user[2]
        current_password = current_user[3]
        role = current_user[4]
        department = current_user[5]
        photo = current_user[6]

        # ==================================================
        # EDIT PROFILE FUNCTION
        # ==================================================

        def edit_profile():

            profile.destroy()

            edit_window = open_in_app_dialog(720, 620)

            add_header(
                edit_window,
                "Edit Profile",
                "Update your IT Support account information",
                closable=True
            )

            card = tk.Frame(
                edit_window,
                bg=WHITE,
                highlightbackground="#D7E4FA",
                highlightthickness=1
            )

            card.pack(
                fill="x",
                padx=60,
                pady=25
            )

            # --------------------------------------------------
            # PHOTO
            # --------------------------------------------------

            photo_frame = tk.Frame(
                card,
                bg=WHITE
            )

            photo_frame.pack(
                pady=(20, 5)
            )

            photo_label = tk.Label(
                photo_frame,
                bg=WHITE
            )

            photo_label.pack()

            selected_photo = {"path": None}

            def load_photo(photo_name):

                if photo_name:

                    photo_path = os.path.join(
                        os.path.dirname(__file__),
                        "photos",
                        photo_name
                    )

                    if os.path.exists(photo_path):

                        image = Image.open(photo_path)
                        image = image.resize((90, 90))

                        photo_image = ImageTk.PhotoImage(image)

                        photo_label.configure(
                            image=photo_image,
                            text=""
                        )

                        photo_label.image = photo_image

                        return

                photo_label.configure(
                    image="",
                    text="👤",
                    fg=BLUE,
                    font=("Arial", 32)
                )

                photo_label.image = None

            load_photo(photo)

            def change_photo():

                file_path = filedialog.askopenfilename(
                    title="Select Profile Photo",
                    filetypes=[
                        (
                            "Image Files",
                            "*.png *.jpg *.jpeg"
                        )
                    ]
                )

                if file_path:

                    selected_photo["path"] = file_path

                    image = Image.open(file_path)
                    image = image.resize((90, 90))

                    photo_image = ImageTk.PhotoImage(image)

                    photo_label.configure(
                        image=photo_image,
                        text=""
                    )

                    photo_label.image = photo_image

            tk.Button(
                card,
                text="Change Photo",
                command=change_photo,
                bg="#E8F1FF",
                fg=BLUE,
                activebackground="#D7E7FF",
                activeforeground=NAVY,
                relief="flat",
                bd=0,
                font=("Arial", 9, "bold"),
                cursor="hand2",
                padx=12,
                pady=5
            ).pack(
                pady=(5, 15)
            )

            # --------------------------------------------------
            # NAME / ROLE
            # --------------------------------------------------

            tk.Label(
                card,
                text=name,
                bg=WHITE,
                fg="#0B1F42",
                font=("Arial", 18, "bold")
            ).pack()

            tk.Label(
                card,
                text=role,
                bg=WHITE,
                fg="#5370A8",
                font=("Arial", 10)
            ).pack(
                pady=(2, 15)
            )

            details = tk.Frame(
                card,
                bg=WHITE
            )

            details.pack(
                fill="x",
                padx=70,
                pady=(0, 15)
            )

            # --------------------------------------------------
            # USERNAME
            # --------------------------------------------------

            tk.Label(
                details,
                text="Username",
                bg=WHITE,
                fg="#6076A4",
                font=("Arial", 10, "bold")
            ).pack(
                anchor="w",
                pady=(5, 3)
            )

            username_entry = tk.Entry(
                details,
                font=("Arial", 10),
                bg="#F7FAFF",
                fg=TEXT,
                relief="solid",
                bd=1
            )

            username_entry.pack(
                fill="x",
                ipady=7
            )

            username_entry.insert(
                0,
                username
            )

            # --------------------------------------------------
            # DEPARTMENT
            # --------------------------------------------------

            tk.Label(
                details,
                text="Department",
                bg=WHITE,
                fg="#6076A4",
                font=("Arial", 10, "bold")
            ).pack(
                anchor="w",
                pady=(12, 3)
            )

            department_entry = tk.Entry(
                details,
                font=("Arial", 10),
                bg="#F7FAFF",
                fg=TEXT,
                relief="solid",
                bd=1
            )

            department_entry.pack(
                fill="x",
                ipady=7
            )

            department_entry.insert(
                0,
                department
            )

            # --------------------------------------------------
            # NEW PASSWORD
            # --------------------------------------------------

            tk.Label(
                details,
                text="New Password",
                bg=WHITE,
                fg="#6076A4",
                font=("Arial", 10, "bold")
            ).pack(
                anchor="w",
                pady=(12, 3)
            )

            password_entry = tk.Entry(
                details,
                show="*",
                font=("Arial", 10),
                bg="#F7FAFF",
                fg=TEXT,
                relief="solid",
                bd=1
            )

            password_entry.pack(
                fill="x",
                ipady=7
            )

            tk.Label(
                details,
                text="Leave blank if you don't want to change the password.",
                bg=WHITE,
                fg="#8093B8",
                font=("Arial", 8)
            ).pack(
                anchor="w",
                pady=(2, 0)
            )

            # --------------------------------------------------
            # CONFIRM PASSWORD
            # --------------------------------------------------

            tk.Label(
                details,
                text="Confirm New Password",
                bg=WHITE,
                fg="#6076A4",
                font=("Arial", 10, "bold")
            ).pack(
                anchor="w",
                pady=(10, 3)
            )

            confirm_password_entry = tk.Entry(
                details,
                show="*",
                font=("Arial", 10),
                bg="#F7FAFF",
                fg=TEXT,
                relief="solid",
                bd=1
            )

            confirm_password_entry.pack(
                fill="x",
                ipady=7
            )

            # --------------------------------------------------
            # ROLE - DISPLAY ONLY
            # --------------------------------------------------

            tk.Label(
                details,
                text="Role",
                bg=WHITE,
                fg="#6076A4",
                font=("Arial", 10, "bold")
            ).pack(
                anchor="w",
                pady=(12, 3)
            )

            tk.Label(
                details,
                text=role,
                bg="#F1F5F9",
                fg="#526A91",
                font=("Arial", 10),
                anchor="w"
            ).pack(
                fill="x",
                ipady=7
            )

            # --------------------------------------------------
            # SAVE CHANGES
            # --------------------------------------------------

            def save_profile():

                new_username = username_entry.get().strip()
                new_department = department_entry.get().strip()

                new_password = password_entry.get()
                confirm_password = confirm_password_entry.get()

                if not new_username:

                    messagebox.showwarning(
                        "Validation",
                        "Username cannot be empty.",
                        parent=edit_window
                    )
                    return

                if not new_department:

                    messagebox.showwarning(
                        "Validation",
                        "Department cannot be empty.",
                        parent=edit_window
                    )
                    return

                # Password
                if new_password or confirm_password:

                    if not new_password:

                        messagebox.showwarning(
                            "Validation",
                            "Please enter the new password.",
                            parent=edit_window
                        )
                        return

                    if new_password != confirm_password:

                        messagebox.showwarning(
                            "Validation",
                            "New password and confirm password do not match.",
                            parent=edit_window
                        )
                        return

                    password_to_save = new_password

                else:

                    password_to_save = current_password

                connection = get_connection()
                cursor = connection.cursor()

                # Check duplicate username
                cursor.execute("""
                    SELECT id
                    FROM users
                    WHERE username = %s
                    AND id != %s
                """, (
                    new_username,
                    user_id
                ))

                if cursor.fetchone():

                    cursor.close()
                    connection.close()

                    messagebox.showwarning(
                        "Username Exists",
                        "This username is already being used.",
                        parent=edit_window
                    )
                    return

                # --------------------------------------------------
                # SAVE PHOTO
                # --------------------------------------------------

                new_photo = photo

                if selected_photo["path"]:

                    photos_folder = os.path.join(
                        os.path.dirname(__file__),
                        "photos"
                    )

                    os.makedirs(
                        photos_folder,
                        exist_ok=True
                    )

                    extension = os.path.splitext(
                        selected_photo["path"]
                    )[1]

                    new_photo = (
                        f"user_{user_id}_profile{extension}"
                    )

                    destination = os.path.join(
                        photos_folder,
                        new_photo
                    )

                    shutil.copy2(
                        selected_photo["path"],
                        destination
                    )

                # --------------------------------------------------
                # UPDATE DATABASE
                # --------------------------------------------------

                cursor.execute("""
                    UPDATE users
                    SET username = %s,
                        password = %s,
                        department = %s,
                        photo = %s
                    WHERE id = %s
                """, (
                    new_username,
                    password_to_save,
                    new_department,
                    new_photo,
                    user_id
                ))

                connection.commit()

                cursor.close()
                connection.close()

                messagebox.showinfo(
                    "Profile Updated",
                    "Your profile has been updated successfully.",
                    parent=edit_window
                )

                edit_window.destroy()

                show_profile()

            # --------------------------------------------------
            # BUTTONS
            # --------------------------------------------------

            button_frame = tk.Frame(
                edit_window,
                bg=BACKGROUND
            )

            button_frame.pack(
                pady=(0, 20)
            )

            add_button(
                button_frame,
                "Save Changes",
                save_profile,
                12,
                True
            ).pack(
                side="left",
                padx=6
            )

            add_button(
                button_frame,
                "Cancel",
                edit_window.destroy,
                12,
                False
            ).pack(
                side="left",
                padx=6
            )

        # ==================================================
        # VIEW PROFILE PAGE
        # ==================================================

        card = tk.Frame(
            profile,
            bg=WHITE,
            highlightbackground="#D7E4FA",
            highlightthickness=1
        )

        card.pack(
            fill="x",
            padx=80,
            pady=45
        )

        # --------------------------------------------------
        # PHOTO
        # --------------------------------------------------

        if photo:

            photo_path = os.path.join(
                os.path.dirname(__file__),
                "photos",
                photo
            )

            if os.path.exists(photo_path):

                profile_image = Image.open(photo_path)
                profile_image = profile_image.resize((90, 90))

                profile_photo = ImageTk.PhotoImage(
                    profile_image
                )

                photo_label = tk.Label(
                    card,
                    image=profile_photo,
                    bg=WHITE
                )

                photo_label.image = profile_photo
                photo_label.pack(
                    pady=(25, 5)
                )

            else:

                tk.Label(
                    card,
                    text="👤",
                    bg=WHITE,
                    fg=BLUE,
                    font=("Arial", 32)
                ).pack(
                    pady=(25, 5)
                )

        else:

            tk.Label(
                card,
                text="👤",
                bg=WHITE,
                fg=BLUE,
                font=("Arial", 32)
            ).pack(
                pady=(25, 5)
            )

        # --------------------------------------------------
        # NAME / ROLE
        # --------------------------------------------------

        tk.Label(
            card,
            text=name,
            bg=WHITE,
            fg="#0B1F42",
            font=("Arial", 18, "bold")
        ).pack()

        tk.Label(
            card,
            text=role,
            bg=WHITE,
            fg="#5370A8",
            font=("Arial", 10)
        ).pack(
            pady=(2, 20)
        )

        # --------------------------------------------------
        # PROFILE DETAILS
        # --------------------------------------------------

        details = tk.Frame(
            card,
            bg=WHITE
        )

        details.pack(
            fill="x",
            padx=80,
            pady=(0, 20)
        )

        profile_data = [
            ("Username", username),
            ("Role", role),
            ("Department", department)
        ]

        for label, value in profile_data:

            row = tk.Frame(
                details,
                bg="#F7FAFF"
            )

            row.pack(
                fill="x",
                pady=4
            )

            tk.Label(
                row,
                text=label,
                bg="#F7FAFF",
                fg="#6076A4",
                font=("Arial", 10, "bold"),
                width=15,
                anchor="w"
            ).pack(
                side="left",
                padx=12,
                pady=9
            )

            tk.Label(
                row,
                text=value,
                bg="#F7FAFF",
                fg=TEXT,
                font=("Arial", 10),
                anchor="w"
            ).pack(
                side="left",
                padx=10
            )

        # --------------------------------------------------
        # BUTTONS
        # --------------------------------------------------

        button_frame = tk.Frame(
            profile,
            bg=BACKGROUND
        )

        button_frame.pack(
            pady=(0, 20)
        )

        add_button(
            button_frame,
            "Edit Profile",
            edit_profile,
            12,
            True
        ).pack(
            side="left",
            padx=6
        )

        add_button(
            button_frame,
            "Close",
            profile.destroy,
            12,
            False
        ).pack(
            side="left",
            padx=6
        )

    activity = tk.Frame(right, bg=WHITE, highlightbackground="#D7E4FA", highlightthickness=1)
    activity.pack(fill="both", expand=True, pady=(16, 0))
    tk.Label(activity, text="Recent Activity", bg=WHITE, fg="#0B1F42", font=("Arial", 13, "bold")).pack(anchor="w", padx=16, pady=14)
    recent_frame = tk.Frame(activity, bg=WHITE)
    recent_frame.pack(fill="both", expand=True, padx=16, pady=(0, 14))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, title, status
        FROM tickets
        WHERE user_id = %s
        ORDER BY id DESC
        LIMIT 5
    """, (user[0],))

    recent_tickets = cursor.fetchall()

    cursor.close()
    connection.close() 

    if recent_tickets:
        for ticket_id, title, status in recent_tickets:
            item = tk.Frame(
                recent_frame,
                bg="#F7FAFF",
                highlightbackground="#D7E4FA",
                highlightthickness=1
            )
            item.pack(fill="x", pady=5)

            tk.Label(
                item,
                text=f"Ticket {ticket_id}",
                bg="#F7FAFF",
                fg="#17417C",
                font=("Arial", 10, "bold")
            ).pack(anchor="w", padx=10, pady=(7, 1))

            tk.Label(
                item,
                text=title,
                bg="#F7FAFF",
                fg="#6076A4",
                font=("Arial", 9)
            ).pack(anchor="w", padx=10)

            tk.Label(
                item,
                text=status,
                bg="#F7FAFF",
                fg="#2563EB",
                font=("Arial", 8, "bold")
            ).pack(anchor="w", padx=10, pady=(1, 7))
    else:
        tk.Label(
            recent_frame,
            text="No recent ticket activity.",
            bg=WHITE,
            fg="#6076A4",
            font=("Arial", 10)
        ).pack(pady=20) 

    for variable in (category_var, priority_var, status_var):
        variable.trace_add("write", refresh_dashboard)
    search_entry.bind("<Return>", refresh_dashboard)
    ticket_tree.bind("<Double-1>", lambda event: open_selected_history())
    refresh_dashboard()


def my_tickets(user):
    for child in window.winfo_children():
        child.destroy()

    tickets_window = window
    setup_window(tickets_window, "My Tickets", "1360x800")
    maximize_window(tickets_window)
    tickets_window.minsize(1100, 680) 
    add_header(tickets_window, "My Tickets", "Double-click a ticket to see its details")

    search_frame = tk.Frame(tickets_window, bg=BACKGROUND)
    search_frame.pack(fill="x", padx=18, pady=14)
    tk.Label(search_frame, text="Search", bg=BACKGROUND, fg=TEXT,
             font=("Arial", 10, "bold")).pack(side="left")
    search_entry = tk.Entry(search_frame, width=38, font=("Arial", 10))
    search_entry.pack(side="left", padx=10, ipady=4)

    table_frame = tk.Frame(tickets_window, bg=BACKGROUND)
    table_frame.pack(fill="both", expand=True, padx=18, pady=(0, 12))
    columns = ("ID", "Title", "Category", "Priority", "Status")
    ticket_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
    configure_tree(ticket_tree)
    for column, width in zip(columns, (60, 290, 150, 110, 120)):
        ticket_tree.heading(column, text=column)
        ticket_tree.column(column, width=width, anchor="center" if column != "Title" else "w")
    ticket_tree.pack(fill="both", expand=True)

    def load_tickets(search_text=""):
        ticket_tree.delete(*ticket_tree.get_children())
        connection = get_connection()
        cursor = connection.cursor()
        query = """
            SELECT tickets.id, tickets.title, categories.category_name,
                   tickets.priority, tickets.status
            FROM tickets
            JOIN categories ON tickets.category_id = categories.id
            WHERE tickets.user_id = %s
        """
        parameters = [user[0]]
        if search_text:
            query += " AND (tickets.title LIKE %s OR categories.category_name LIKE %s OR tickets.status LIKE %s)"
            pattern = f"%{search_text}%"
            parameters.extend([pattern, pattern, pattern])
        cursor.execute(query + " ORDER BY tickets.id DESC", tuple(parameters))
        for ticket in cursor.fetchall():
            insert_ticket(ticket_tree, ticket, 4)
        cursor.close()
        connection.close()

    def show_ticket_details(event):

        selected = ticket_tree.selection()
        if not selected:
            return
        ticket_id = ticket_tree.item(selected[0])["values"][0]
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT tickets.id, tickets.title, categories.category_name,
                   tickets.description, tickets.priority, tickets.status,
                   COALESCE(support_staff.username, 'Not Assigned'),
                   COALESCE(tickets.resolution_note, 'No resolution note yet.'),
                   tickets.created_at, tickets.updated_at
            FROM tickets
            JOIN categories ON tickets.category_id = categories.id
            LEFT JOIN users AS support_staff ON tickets.assigned_to = support_staff.id
            WHERE tickets.id = %s AND tickets.user_id = %s
        """, (ticket_id, user[0]))
        ticket = cursor.fetchone()

    
        cursor.close()
        connection.close()

        if not ticket:
            messagebox.showerror("Error", "Ticket details could not be found.")
            return
        details = tk.Toplevel(tickets_window)
        setup_window(details, "Ticket Details", "900x650")
        maximize_window(details)

        add_header(
            details,
            f"Ticket #{ticket[0]}",
            "Ticket details and resolution"
        )


        table_frame = tk.Frame(
            details,
            bg=BACKGROUND
        )
        table_frame.pack(
            fill="x",
            padx=25,
            pady=(18, 10), 
            anchor="center"
        )
        

        # Table Header
        header = tk.Frame(
            table_frame,
            bg=NAVY
        )
        header.pack(
            fill="x"
        )

        tk.Label(
            header,
            text="Field",
            bg=NAVY,
            fg=WHITE,
            font=("Arial", 12, "bold"),
            width=18,
            anchor="w"
        ).pack(
            side="left",
            padx=12,
            pady=9
        )

        tk.Label(
            header,
            text="Details",
            bg=NAVY,
            fg=WHITE,
            font=("Arial", 12, "bold"),
            anchor="w"
        ).pack(
            side="left",
            padx=12,
            pady=9
        )

        detail_rows = [
            ("Ticket ID", ticket[0]),
            ("Title", ticket[1]),
            ("Category", ticket[2]),
            ("Priority", ticket[4]),
            ("Status", ticket[5]),
            ("Assigned To", ticket[6]),
            ("Created", ticket[8]),
            ("Last Updated", ticket[9]),
            ("Description", ticket[3] or ""),
            ("Resolution Note", ticket[7])
        ]

        for index, (field, value) in enumerate(detail_rows):

            row = tk.Frame(
                table_frame,
                bg=WHITE,
                highlightbackground="#E1E8F2",
                highlightthickness=1
            )
            row.pack(
                fill="x"
            )

            tk.Label(
                row,
                text=field,
                bg=WHITE,
                fg="#0B1F42",
                font=("Arial", 11, "bold"),
                width=18,
                anchor="w"
            ).pack(
                side="left",
                padx=12,
                pady=5
            )

            tk.Label(
                row,
                text=str(value),
                bg=WHITE,
                fg="#536987",
                font=("Arial", 11),
                anchor="w",
                justify="left",
                wraplength=680
            ).pack(
                side="left",
                fill="x",
                expand=True,
                padx=12,
                pady=8
            )

        actions = tk.Frame(
            details,
            bg=BACKGROUND
        )
        actions.pack(
            pady=(0, 15)
        )

                # ---------- RESOLUTION VERIFICATION ----------
        if ticket[5] == "RESOLVED":

            def confirm_resolution():
                confirm = messagebox.askyesno(
                    "Confirm Resolution",
                    "Is the issue completely resolved?",
                    parent=details
                )

                if not confirm:
                    return

                connection = get_connection()
                cursor = connection.cursor()

                cursor.execute(
                    """
                    UPDATE tickets
                    SET status = 'CLOSED',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    AND user_id = %s
                    AND status = 'RESOLVED'
                    """,
                    (ticket[0], user[0])
                )

                connection.commit()
                cursor.close()
                connection.close()

                messagebox.showinfo(
                    "Ticket Closed",
                    "The ticket has been closed successfully.",
                    parent=details
                )

                details.destroy()
                load_tickets()

            def issue_still_exists():
                confirm = messagebox.askyesno(
                    "Issue Still Exists",
                    "Is the issue still present?",
                    parent=details
                )

                if not confirm:
                    return

                connection = get_connection()
                cursor = connection.cursor()

                cursor.execute(
                    """
                    UPDATE tickets
                    SET status = 'REOPENED',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    AND user_id = %s
                    AND status = 'RESOLVED'
                    """,
                    (ticket[0], user[0])
                )

                connection.commit()
                cursor.close()
                connection.close()

                messagebox.showinfo(
                    "Ticket Reopened",
                    "The ticket has been reopened and will be sent back to IT Support.",
                    parent=details
                )

                details.destroy()
                load_tickets()

            add_button(
                actions,
                "Confirm Resolution",
                confirm_resolution,
                20
            ).pack(
                side="left",
                padx=5
            )

            add_button(
                actions,
                "Issue Still Exists",
                issue_still_exists,
                20,
                True
            ).pack(
                side="left",
                padx=5
            )

        

        add_button(
            actions,
            "View Ticket History",
            lambda: show_ticket_history(details, ticket[0]),
            22
        ).pack(
            side="left",
            padx=5
        )

        add_button(
            actions,
            "Comments",
            lambda: show_comments_window(ticket[0]),
            14
        ).pack(
            side="left",
            padx=5
        )

        def close_ticket_details():

            details.destroy()

        add_button(
            actions,
            "Close",
            close_ticket_details,
            12,
            True
        ).pack(
            side="left",
            padx=5
        )

    add_button(search_frame, "Search", lambda: load_tickets(search_entry.get().strip()), 10).pack(side="left", padx=3)
    add_button(search_frame, "Clear", lambda: (search_entry.delete(0, tk.END), load_tickets()), 9, True).pack(side="left", padx=3)
    ticket_tree.bind("<Double-1>", show_ticket_details)
    search_entry.bind("<Return>", lambda event: load_tickets(search_entry.get().strip()))
    load_tickets()

    add_button(
        tickets_window,
        "Back to Dashboard",
        lambda: employee_dashboard(user),
        18,
        True
    ).pack(side="bottom", pady=(0, 15))

    def show_comments_window(ticket_id):

        comments_window = tk.Toplevel(tickets_window)

        setup_window(
            comments_window,
            f"Comments - Ticket #{ticket_id}",
            "800x600"
        )

        maximize_window(comments_window)

        add_header(
            comments_window,
            f"Comments - Ticket #{ticket_id}",
            "View and add ticket comments"
        )

    # =========================================================
    # COMMENTS LIST
    # =========================================================

        list_container = tk.Frame(
            comments_window,
            bg=BACKGROUND
        )

        list_container.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=(15, 10)
        )

        comments_canvas = tk.Canvas(
            list_container,
            bg=BACKGROUND,
            highlightthickness=0
        )

        comments_scrollbar = ttk.Scrollbar(
            list_container,
            orient="vertical",
            command=comments_canvas.yview
        )

        comments_canvas.configure(
            yscrollcommand=comments_scrollbar.set
        )

        comments_scrollbar.pack(
            side="right",
            fill="y"
        )

        comments_canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        comments_frame = tk.Frame(
            comments_canvas,
            bg=BACKGROUND
        )

        comments_canvas_window = comments_canvas.create_window(
            (0, 0),
            window=comments_frame,
            anchor="nw"
        )

        def update_comments_scroll(event=None):

            comments_canvas.configure(
                scrollregion=comments_canvas.bbox("all")
            )

        comments_frame.bind(
            "<Configure>",
            update_comments_scroll
        )

        def resize_comments_frame(event):

            comments_canvas.itemconfig(
                comments_canvas_window,
                width=event.width
            )

        comments_canvas.bind(
            "<Configure>",
            resize_comments_frame
        )

    # =========================================================
    # LOAD COMMENTS
    # =========================================================

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                users.name,
                users.role,
                users.department,
                ticket_comments.comment,
                ticket_comments.created_at
            FROM ticket_comments
            JOIN users
                ON ticket_comments.user_id = users.id
            WHERE ticket_comments.ticket_id = %s
            ORDER BY ticket_comments.created_at ASC
            """,
            (ticket_id,)
        )

        comments = cursor.fetchall()

        cursor.close()
        connection.close()

        if comments:

            for name, role, department, comment_text, created_at in comments:

                comment_box = tk.Frame(
                    comments_frame,
                    bg=WHITE,
                    highlightbackground="#D7E4FA",
                    highlightthickness=1
                )

                comment_box.pack(
                    fill="x"
                )

                tk.Label(
                    comment_box,
                    text=f"{name} — {role}" if role == "IT Support" else f"{name} — {department}",
                    bg=WHITE,
                    fg="#0B1F42",
                    font=("Arial", 10, "bold"),
                    anchor="w"
                ).pack(
                    fill="x",
                    padx=12,
                    pady=(8, 0)
                )

                tk.Label(
                    comment_box,
                    text=str(comment_text),
                    bg=WHITE,
                    fg="#536987",
                    font=("Arial", 10),
                    anchor="w",
                    justify="left",
                    wraplength=650
                ).pack(
                    fill="x",
                    padx=12,
                    pady=(4, 2)
                )

                tk.Label(
                    comment_box,
                    text=str(created_at),
                    bg=WHITE,
                    fg="#7A8CA5",
                    font=("Arial", 9),
                    anchor="w"
                ).pack(
                    fill="x",
                    padx=12,
                    pady=(0, 8)
                )

        else:

            tk.Label(
                comments_frame,
                text="No comments yet.",
                bg=BACKGROUND,
                fg="#7A8CA5",
                font=("Arial", 10)
            ).pack(
                pady=30
            )



    # =========================================================
    # CHECK TICKET STATUS
    # =========================================================

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT status
            FROM tickets
            WHERE id = %s
            """,
            (ticket_id,)
        )

        ticket_status = cursor.fetchone()

        cursor.close()
        connection.close()

        # =========================================================
        # ADD COMMENT
        # =========================================================

        if ticket_status and str(ticket_status[0]).upper() != "CLOSED":

            input_frame = tk.Frame(
                comments_window,
                bg=BACKGROUND
            )

            input_frame.pack(
                fill="x",
                padx=25,
                pady=(0, 10)
            )

            tk.Label(
                input_frame,
                text="Add Comment",
                bg=BACKGROUND,
                fg="#0B1F42",
                font=("Arial", 10, "bold")
            ).pack(
                anchor="w"
            )

            comment_entry = tk.Text(
                input_frame,
                height=2,
                font=("Arial", 10),
                wrap="word"
            )

            comment_entry.pack(
                fill="x",
                pady=(5, 8)
            )

            def add_employee_comment():

                comment_text = comment_entry.get(
                    "1.0",
                    tk.END
                ).strip()

                if not comment_text:

                    messagebox.showwarning(
                        "Empty Comment",
                        "Please enter a comment.",
                        parent=comments_window
                    )

                    return

                connection = get_connection()
                cursor = connection.cursor()

                cursor.execute(
                    """
                    INSERT INTO ticket_comments
                    (
                        ticket_id,
                        user_id,
                        comment
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        ticket_id,
                        user[0],
                        comment_text
                    )
                )

                # Get assigned IT Support
                cursor.execute(
                    """
                    SELECT assigned_to
                    FROM tickets
                    WHERE id = %s
                    """,
                    (ticket_id,)
                )

                assigned_to = cursor.fetchone()

                if assigned_to and assigned_to[0]:

                    add_notification(
                        cursor,
                        assigned_to[0],
                        ticket_id,
                        f"Employee added a new comment to Ticket #{ticket_id}."
                    )

                connection.commit()

                cursor.close()
                connection.close()

                messagebox.showinfo(
                    "Comment Added",
                    "Your comment has been added successfully.",
                    parent=comments_window
                )

                comments_window.destroy()

                show_comments_window(ticket_id)

            add_button(
                input_frame,
                "Add Comment",
                add_employee_comment,
                14
            ).pack(
                anchor="e"
            )

        else:

            tk.Label(
                comments_window,
                text="This ticket is closed. Comments can only be viewed.",
                bg=BACKGROUND,
                fg="#B3261E",
                font=("Arial", 10, "bold")
            ).pack(
                padx=25,
                pady=(5, 15)
            )

        # =========================================================
        # CLOSE
        # =========================================================

        add_button(
            comments_window,
            "Close",
            comments_window.destroy,
            12,
            True
        ).pack(
            pady=(0, 15)
        )

def admin_dashboard(user):
    for child in window.winfo_children():
        child.destroy()
    admin_window = window

    # ==================================================
    # ADMIN USER MANAGEMENT
    # ==================================================

    def show_user_management():

        user_window = tk.Toplevel(admin_window)

        setup_window(
            user_window,
            "User Management",
            "1100x650"
        )

        maximize_window(user_window)

        add_header(
            user_window,
            "User Management",
            "Manage Employees and IT Support staff",
            closable=True
        )

        # --------------------------------------------------
        # TOP ACTIONS
        # --------------------------------------------------

        action_frame = tk.Frame(
            user_window,
            bg=BACKGROUND
        )

        action_frame.pack(
            fill="x",
            padx=25,
            pady=(10, 5)
        )

        add_user_button = add_button(
            action_frame,
            "+ Add User",
            lambda: open_add_user(),
            14
        )

        add_user_button.pack(side="left", padx=(0, 10))

        # --------------------------------------------------
        # USER SEARCH & FILTER
        # --------------------------------------------------

        search_var = tk.StringVar()
        role_filter_var = tk.StringVar(value="All")

        tk.Label(
            action_frame,
            text="Search:",
            bg=BACKGROUND,
            fg="#1F2937",
            font=("Segoe UI", 10, "bold")
        ).pack(side="left", padx=(20, 5))

        search_entry = tk.Entry(
            action_frame,
            textvariable=search_var,
            width=25,
            font=("Segoe UI", 10)
        )

        search_entry.pack(side="left", padx=(0, 10))

        tk.Label(
            action_frame,
            text="Role:",
            bg=BACKGROUND,
            fg="#1F2937",
            font=("Segoe UI", 10, "bold")
        ).pack(side="left", padx=(5, 5))

        role_filter = ttk.Combobox(
            action_frame,
            textvariable=role_filter_var,
            values=("All", "Employee", "IT Support"),
            state="readonly",
            width=15
        )

        role_filter.pack(side="left", padx=(0, 10))

        search_entry.bind(
            "<KeyRelease>",
            lambda event: load_users()
        )

        role_filter.bind(
            "<<ComboboxSelected>>",
            lambda event: load_users()
        )

 
        # --------------------------------------------------
        # USER TABLE
        # --------------------------------------------------

        table_card = tk.Frame(
            user_window,
            bg=WHITE,
            highlightbackground="#D7E4FA",
            highlightthickness=1
        )

        table_card.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=15
        )

        table_frame = tk.Frame(
            table_card,
            bg=WHITE
        )

        table_frame.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=12
        )

        columns = (
            "ID",
            "Name",
            "Username",
            "Role",
            "Department",
            "Status"
        )

        user_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        configure_tree(user_tree)

        widths = (
            60,
            200,
            180,
            150,
            180,
            120
        )

        for column, width in zip(columns, widths):

            user_tree.heading(
                column,
                text=column
            )

            user_tree.column(
                column,
                width=width,
                anchor="center"
            )

        user_tree.pack(
            fill="both",
            expand=True
        )

        # --------------------------------------------------
        # LOAD USERS
        # --------------------------------------------------

        def load_users():

            user_tree.delete(
                *user_tree.get_children()
            )

            search_text = search_var.get().strip()
            selected_role = role_filter_var.get()

            connection = get_connection()
            cursor = connection.cursor()

            query = """
                SELECT
                    id,
                    name,
                    username,
                    role,
                    department,
                    CASE
                        WHEN active = 1 THEN 'Active'
                        ELSE 'Inactive'
                    END AS status
                FROM users
                WHERE role IN ('Employee', 'IT Support')
            """

            params = []

            # Search by name or username
            if search_text:
                query += """
                    AND (
                        name LIKE %s
                        OR username LIKE %s
                    )
                """

                search_pattern = f"%{search_text}%"

                params.extend([
                    search_pattern,
                    search_pattern
                ])

            # Filter by role
            if selected_role != "All":
                query += """
                    AND role = %s
                """

                params.append(selected_role)

            query += """
                ORDER BY role, name
            """

            cursor.execute(
                query,
                tuple(params)
            )

            users = cursor.fetchall()

            cursor.close()
            connection.close()

            for user_row in users:

                user_tree.insert(
                    "",
                    tk.END,
                    values=user_row
                )

        # --------------------------------------------------
        # EDIT USER
        # --------------------------------------------------

        def edit_selected_user():

            selected = user_tree.selection()

            if not selected:
                messagebox.showwarning(
                    "Edit User",
                    "Please select a user to edit.",
                    parent=user_window
                )
                return

            user_data = user_tree.item(
                selected[0],
                "values"
            )

            user_id = user_data[0]
            current_name = user_data[1]
            current_username = user_data[2]
            current_role = user_data[3]
            current_department = user_data[4]

            edit_window = tk.Toplevel(user_window)

            setup_window(
                edit_window,
                "Edit User",
                "700x600"
            )

            maximize_window(edit_window)

            add_header(
                edit_window,
                "Edit User",
                "Update Employee or IT Support details",
                closable=False
            )

            form_frame = tk.Frame(
                edit_window,
                bg=BACKGROUND
            )

            form_frame.pack(
                fill="both",
                expand=True,
                padx=40,
                pady=20
            )

            # Name
            tk.Label(
                form_frame,
                text="Full Name",
                bg=BACKGROUND,
                font=("Segoe UI", 11, "bold")
            ).pack(anchor="w", pady=(5, 5))

            name_var = tk.StringVar(
                value=current_name
            )

            name_entry = tk.Entry(
                form_frame,
                textvariable=name_var,
                font=("Segoe UI", 11)
            )

            name_entry.pack(
                fill="x",
                pady=(0, 15)
            )

            # Username
            tk.Label(
                form_frame,
                text="Username",
                bg=BACKGROUND,
                font=("Segoe UI", 11, "bold")
            ).pack(anchor="w", pady=(5, 5))

            username_var = tk.StringVar(
                value=current_username
            )

            username_entry = tk.Entry(
                form_frame,
                textvariable=username_var,
                font=("Segoe UI", 11)
            )

            username_entry.pack(
                fill="x",
                pady=(0, 15)
            )

            # Department
            tk.Label(
                form_frame,
                text="Department",
                bg=BACKGROUND,
                font=("Segoe UI", 11, "bold")
            ).pack(anchor="w", pady=(5, 5))

            department_var = tk.StringVar(
                value=current_department
            )

            department_entry = tk.Entry(
                form_frame,
                textvariable=department_var,
                font=("Segoe UI", 11)
            )

            department_entry.pack(
                fill="x",
                pady=(0, 15)
            )

            # Role
            tk.Label(
                form_frame,
                text="Role",
                bg=BACKGROUND,
                font=("Segoe UI", 11, "bold")
            ).pack(anchor="w", pady=(5, 5))

            role_var = tk.StringVar(
                value=current_role
            )

            role_combo = ttk.Combobox(
                form_frame,
                textvariable=role_var,
                values=("Employee", "IT Support"),
                state="readonly",
                font=("Segoe UI", 11)
            )

            role_combo.pack(
                fill="x",
                pady=(0, 25)
            )

            def save_user_changes():

                name = name_var.get().strip()
                username = username_var.get().strip()
                department = department_var.get().strip()
                role = role_var.get()

                if not name or not username or not department:
                    messagebox.showwarning(
                        "Edit User",
                        "Please fill all fields.",
                        parent=edit_window
                    )
                    return

                connection = get_connection()
                cursor = connection.cursor()

                cursor.execute(
                    """
                    SELECT id
                    FROM users
                    WHERE username = %s
                    AND id != %s
                    """,
                    (username, user_id)
                )

                existing_user = cursor.fetchone()

                if existing_user:
                    cursor.close()
                    connection.close()

                    messagebox.showerror(
                        "Edit User",
                        "Username already exists."
                    )
                    return

                cursor.execute(
                    """
                    UPDATE users
                    SET
                        name = %s,
                        username = %s,
                        role = %s,
                        department = %s
                    WHERE id = %s
                    """,
                    (
                        name,
                        username,
                        role,
                        department,
                        user_id
                    )
                )

                connection.commit()

                cursor.close()
                connection.close()

                messagebox.showinfo(
                    "Edit User",
                    "User details updated successfully.",
                    parent=user_window
                )

                

                load_users()

            save_button = add_button(
                form_frame,
                "Save Changes",
                save_user_changes,
                16
            )

            save_button.pack(
                pady=10
            )

        # --------------------------------------------------
        # EDIT BUTTON
        # --------------------------------------------------

        edit_button = add_button(
            action_frame,
            "Edit Selected User",
            edit_selected_user,
            18
        )

        edit_button.pack(
            side="left",
            padx=(0, 10)
        )

        # --------------------------------------------------
        # DEACTIVATE USER
        # --------------------------------------------------

        def deactivate_selected_user():

            selected = user_tree.selection()

            if not selected:
                messagebox.showwarning(
                    "Deactivate User",
                    "Please select a user to deactivate.",
                    parent=user_window
                )
                return

            user_data = user_tree.item(
                selected[0],
                "values"
            )

            user_id = user_data[0]
            current_status = user_data[5]

            if current_status == "Inactive":
                messagebox.showinfo(
                    "Deactivate User",
                    "This user is already inactive.",
                    parent=user_window
                )
                return

            confirm = messagebox.askyesno(
                "Deactivate User",
                f"Are you sure you want to deactivate\n"
                f"{user_data[1]} ({user_data[2]})?",
                parent=user_window
            )

            if not confirm:
                return

            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE users
                SET active = 0
                WHERE id = %s
                """,
                (user_id,)
            )

            connection.commit()

            cursor.close()
            connection.close()

            messagebox.showinfo(
                "Deactivate User",
                "User has been deactivated successfully.",
                parent=user_window
            )

            load_users()

        deactivate_button = add_button(
            action_frame,
            "Deactivate User",
            deactivate_selected_user,
            18
        )

        deactivate_button.pack(
            side="left",
            padx=(0, 10)
        )

        # --------------------------------------------------
        # REACTIVATE USER
        # --------------------------------------------------

        def reactivate_selected_user():

            selected = user_tree.selection()

            if not selected:
                messagebox.showwarning(
                    "Reactivate User",
                    "Please select a user to reactivate.",
                    parent=user_window
                )
                return

            user_data = user_tree.item(
                selected[0],
                "values"
            )

            user_id = user_data[0]
            current_status = user_data[5]

            if current_status == "Active":
                messagebox.showinfo(
                    "Reactivate User",
                    "This user is already active.",
                    parent=user_window
                )
                return

            confirm = messagebox.askyesno(
                "Reactivate User",
                f"Are you sure you want to reactivate\n"
                f"{user_data[1]} ({user_data[2]})?",
                parent=user_window
            )

            if not confirm:
                return

            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE users
                SET active = 1
                WHERE id = %s
                """,
                (user_id,)
            )

            connection.commit()

            cursor.close()
            connection.close()

            messagebox.showinfo(
                "Reactivate User",
                "User has been reactivated successfully.",
                parent=user_window
            )

            load_users()

        reactivate_button = add_button(
            action_frame,
            "Reactivate User",
            reactivate_selected_user,
            18
        )

        reactivate_button.pack(
            side="left",
            padx=(0, 10)
        )

        # --------------------------------------------------
        # ADD USER WINDOW
        # --------------------------------------------------

        def open_add_user():

            add_window = tk.Toplevel(user_window)

            setup_window(
                add_window,
                "Add User",
                "1100x700"
            )

            maximize_window(add_window)
            add_window.transient(
                user_window
            )

            add_window.grab_set()

            add_header(
                add_window,
                "Add User",
                "Create a new Employee or IT Support account",
                closable=False
            )
        
            form = tk.Frame(
                add_window,
                bg=BACKGROUND
            )

            form.pack(
                fill="both",
                expand=True,
                padx=35,
                pady=25
            )

            # -----------------------------
            # NAME
            # -----------------------------

            tk.Label(
                form,
                text="Full Name",
                bg=BACKGROUND,
                fg=NAVY,
                font=("Arial", 10, "bold")
            ).pack(
                anchor="w",
                pady=(0, 5)
            )

            name_entry = tk.Entry(
                form,
                font=("Arial", 11)
            )

            name_entry.pack(
                fill="x",
                pady=(0, 15)
            )

            # -----------------------------
            # USERNAME
            # -----------------------------

            tk.Label(
                form,
                text="Username",
                bg=BACKGROUND,
                fg=NAVY,
                font=("Arial", 10, "bold")
            ).pack(
                anchor="w",
                pady=(0, 5)
            )

            username_entry = tk.Entry(
                form,
                font=("Arial", 11)
            )

            username_entry.pack(
                fill="x",
                pady=(0, 15)
            )

            # -----------------------------
            # PASSWORD
            # -----------------------------

            tk.Label(
                form,
                text="Password",
                bg=BACKGROUND,
                fg=NAVY,
                font=("Arial", 10, "bold")
            ).pack(
                anchor="w",
                pady=(0, 5)
            )

            password_entry = tk.Entry(
                form,
                font=("Arial", 11),
                show="*"
            )

            password_entry.pack(
                fill="x",
                pady=(0, 15)
            )

            # -----------------------------
            # DEPARTMENT
            # -----------------------------

            tk.Label(
                form,
                text="Department",
                bg=BACKGROUND,
                fg=NAVY,
                font=("Arial", 10, "bold")
            ).pack(
                anchor="w",
                pady=(0, 5)
            )

            department_entry = tk.Entry(
                form,
                font=("Arial", 11)
            )

            department_entry.pack(
                fill="x",
                pady=(0, 15)
            )

            # -----------------------------
            # ROLE
            # -----------------------------

            tk.Label(
                form,
                text="Role",
                bg=BACKGROUND,
                fg=NAVY,
                font=("Arial", 10, "bold")
            ).pack(
                anchor="w",
                pady=(0, 5)
            )

            role_var = tk.StringVar(value="Employee")
            

            role_entry = ttk.Combobox(
                form,
                textvariable=role_var,
                values=[
                    "Employee",
                    "IT Support"
                ],
                state="readonly",
                width=30
            )

            role_entry.pack(
                fill="x",
                pady=(0, 25)
            )

            # -----------------------------
            # CREATE USER
            # -----------------------------

            def create_user():

                name = name_entry.get().strip()
                username = username_entry.get().strip()
                password = password_entry.get()
                department = department_entry.get().strip()
                selected_role = role_var.get()

                if not name:
                    messagebox.showwarning(
                        "Missing Name",
                        "Enter the user's name.",
                        parent=add_window
                    )
                    return

                if not username:
                    messagebox.showwarning(
                        "Missing Username",
                        "Enter a username.",
                        parent=add_window
                    )
                    return

                if not password:
                    messagebox.showwarning(
                        "Missing Password",
                        "Enter a password.",
                        parent=add_window
                    )
                    return

                if not department:
                    messagebox.showwarning(
                        "Missing Department",
                        "Enter the department.",
                        parent=add_window
                    )
                    return

                connection = get_connection()
                cursor = connection.cursor()

                try:

                    cursor.execute(
                        """
                        SELECT id
                        FROM users
                        WHERE BINARY username = BINARY %s
                        """,
                        (username,)
                    )

                    existing_user = cursor.fetchone()

                    if existing_user:

                        messagebox.showwarning(
                            "Username Exists",
                            "This username is already in use.",
                            parent=add_window
                        )

                        return

                    cursor.execute(
                        """
                        INSERT INTO users
                        (
                            name,
                            username,
                            password,
                            role,
                            department
                        )
                        VALUES
                        (%s, %s, %s, %s, %s)
                        """,
                        (
                            name,
                            username,
                            password,
                            selected_role,
                            department
                        )
                    )

                    connection.commit()

                    messagebox.showinfo(
                        "User Created",
                        f"{selected_role} account created successfully.",
                        parent=add_window
                    )

                    add_window.destroy()

                    load_users()

                except Exception as error:

                    connection.rollback()

                    messagebox.showerror(
                        "Database Error",
                        f"Unable to create user.\n\n{error}",
                        parent=add_window
                    )

                finally:

                    cursor.close()
                    connection.close()

            button_frame = tk.Frame(
                form,
                bg=BACKGROUND
            )

            button_frame.pack(
                fill="x"
            )

            add_button(
                button_frame,
                "Create User",
                create_user,
                14
            ).pack(
                side="left",
                padx=(0, 8)
            )

            add_button(
                button_frame,
                "Cancel",
                add_window.destroy,
                14,
                True
            ).pack(
                side="left"
            )

            name_entry.focus_set()

        # Initial load
        load_users()

        add_button(
            user_window,
            "Close",
            user_window.destroy,
            14,
            True
        ).pack(
            side="bottom",
            pady=12
        )
    setup_window(admin_window, "Admin Dashboard", "1360x800")
    maximize_window(admin_window)

    # ---------- SIDEBAR ----------
    sidebar = tk.Frame(
        admin_window,
        bg="#102C55",
        width=230
    )

    sidebar.pack(
        side="left",
        fill="y"
    )

    sidebar.pack_propagate(False)

    # ---------- SIDEBAR BRAND ----------
    brand = tk.Frame(
        sidebar,
        bg="#102C55"
    )

    brand.pack(
        fill="x",
        padx=20,
        pady=(25, 35)
    )

    tk.Label(
        brand,
        text="🎧",
        bg="#102C55",
        fg=WHITE,
        font=("Segoe UI Emoji", 21)
    ).pack(
        side="left",
        padx=(0, 8)
    )

    tk.Label(
        brand,
        text="IT Support",
        bg="#102C55",
        fg=WHITE,
        font=("Arial", 17, "bold")
    ).pack(
        side="left"
    )


    # ---------- SIDEBAR MENU ----------
    dashboard_button = tk.Button(
        sidebar,
        text="⌂   Dashboard",
        bg="#183E70",
        fg=WHITE,
        activebackground="#1D4C86",
        activeforeground=WHITE,
        relief="flat",
        bd=0,
        anchor="w",
        font=("Arial", 10, "bold"),
        cursor="hand2",
        padx=20,
        pady=10
    )

    dashboard_button.pack(
        fill="x",
        padx=12,
        pady=(0, 5)
    )

    # ---------- TICKETS ----------
    tickets_button = tk.Button(
        sidebar,
        text="🎫   Tickets",
        command=lambda: ticket_tree.focus_set(),
        bg="#102C55",
        fg=WHITE,
        activebackground="#183E70",
        activeforeground=WHITE,
        relief="flat",
        bd=0,
        anchor="w",
        font=("Arial", 10, "bold"),
        cursor="hand2",
        padx=20,
        pady=10
    )

    tickets_button.pack(
        fill="x",
        padx=12,
        pady=2
    )


    # ---------- USER MANAGEMENT ----------
    user_management_button = tk.Button(
        sidebar,
        text="👥   User Management",
        command=lambda: show_user_management(),
        bg="#102C55",
        fg=WHITE,
        activebackground="#183E70",
        activeforeground=WHITE,
        relief="flat",
        bd=0,
        anchor="w",
        font=("Arial", 10, "bold"),
        cursor="hand2",
        padx=20,
        pady=10
    )

    user_management_button.pack(
        fill="x",
        padx=12,
        pady=2
    )

    # ---------- REPORTS ----------
    reports_button = tk.Button(
        sidebar,
        text="📊   Reports",
        command=lambda: show_reports(user),
        bg="#102C55",
        fg=WHITE,
        activebackground="#183E70",
        activeforeground=WHITE,
        relief="flat",
        bd=0,
        anchor="w",
        font=("Arial", 10, "bold"),
        cursor="hand2",
        padx=20,
        pady=10
    )

    reports_button.pack(
        fill="x",
        padx=12,
        pady=2
    )


    # ---------- WORKLOAD ----------
    workload_button = tk.Button(
        sidebar,
        text="📋   Workload",
        command=lambda: show_workload_details(),
        bg="#102C55",
        fg=WHITE,
        activebackground="#183E70",
        activeforeground=WHITE,
        relief="flat",
        bd=0,
        anchor="w",
        font=("Arial", 10, "bold"),
        cursor="hand2",
        padx=20,
        pady=10
    )

    workload_button.pack(
        fill="x",
        padx=12,
        pady=2
    )


    # ---------- NOTIFICATIONS ----------
    notifications_button = tk.Button(
        sidebar,
        text="🔔   Notifications",
        command=lambda: show_notifications(user),
        bg="#102C55",
        fg=WHITE,
        activebackground="#183E70",
        activeforeground=WHITE,
        relief="flat",
        bd=0,
        anchor="w",
        font=("Arial", 10, "bold"),
        cursor="hand2",
        padx=20,
        pady=10
    )

    notifications_button.pack(
        fill="x",
        padx=12,
        pady=2
    )


    # ---------- MY PROFILE ----------
    profile_button = tk.Button(
        sidebar,
        text="👤   My Profile",
        command=lambda: show_current_profile(user[0]),
        bg="#102C55",
        fg=WHITE,
        activebackground="#183E70",
        activeforeground=WHITE,
        relief="flat",
        bd=0,
        anchor="w",
        font=("Arial", 10, "bold"),
        cursor="hand2",
        padx=20,
        pady=10
    )

    profile_button.pack(
        fill="x",
        padx=12,
        pady=2
    )

    # ---------- SIDEBAR SPACER ----------
    sidebar_spacer = tk.Frame(
        sidebar,
        bg="#102C55"
    )

    sidebar_spacer.pack(
        fill="both",
        expand=True
    )


    # ---------- LOGOUT ----------
    logout_button = tk.Button(
        sidebar,
        text="↪   Logout",
        command=show_login_window,
        bg="#102C55",
        fg=WHITE,
        activebackground="#183E70",
        activeforeground=WHITE,
        relief="flat",
        bd=0,
        anchor="w",
        font=("Arial", 10, "bold"),
        cursor="hand2",
        padx=20,
        pady=10
    )

    logout_button.pack(
        fill="x",
        padx=12,
        pady=(5, 20)
    )

    # ---------- MAIN CONTENT ----------
    admin_main = tk.Frame(
        admin_window,
        bg=BACKGROUND
    )

    admin_main.pack(
        side="left",
        fill="both",
        expand=True
    )
    admin_window.protocol("WM_DELETE_WINDOW", admin_window.destroy)
    admin_topbar = tk.Frame(
        admin_main,
        bg=WHITE,
        height=64
    )
    admin_topbar.pack(fill="x")
    admin_topbar.pack_propagate(False)

    admin_title_frame = tk.Frame(
        admin_topbar,
        bg=WHITE
    )
    admin_title_frame.pack(
        side="left",
        padx=28
    )

    tk.Label(
        admin_title_frame,
        text="Admin Dashboard",
        bg=WHITE,
        fg="#0B1F42",
        font=("Arial", 18, "bold")
    ).pack(anchor="w")

    tk.Label(
        admin_title_frame,
        text=f"Welcome, {user[1]}",
        bg=WHITE,
        fg="#6076A4",
        font=("Arial", 9)
    ).pack(anchor="w")
    admin_top_actions = tk.Frame(
        admin_topbar,
        bg=WHITE 
    )
    admin_top_actions.pack(
        side="right",
        padx=25
    )

    admin_unread_var = tk.StringVar(
        value=f"🔔 {get_unread_notification_count(user[0])}"
    )

    def refresh_admin_notification_count():

        try:
            if admin_window.winfo_exists():

                admin_unread_var.set(
                    f"🔔 {get_unread_notification_count(user[0])}"
                )

                admin_window.after(
                    2000,
                    refresh_admin_notification_count
                )

        except tk.TclError:
            pass

    refresh_admin_notification_count()

    tk.Button(
        admin_top_actions,
        textvariable=admin_unread_var,
        command=lambda: (
            show_notifications(user),
            admin_unread_var.set("🔔 0")
        ), 
        bg=NAVY,
        fg=WHITE,
        activebackground="#E8F1FF",
        activeforeground=NAVY,
        relief="flat",
        bd=0,
        cursor="hand2",
        font=("Arial", 10, "bold")
    ).pack(side="left", padx=4)

    tk.Button(
        admin_top_actions,
        text="📊 Reports",
        command=lambda: show_reports(user),
        bg=NAVY,
        fg=WHITE,
        activebackground="#E8F1FF",
        activeforeground=NAVY,
        relief="flat",
        bd=0,
        cursor="hand2",
        font=("Arial", 10, "bold"),
        padx=10,
        pady=6
    ).pack(side="left", padx=4)

    tk.Button(
        admin_top_actions,
        text="☰",
        command=lambda: show_dashboard_menu(
            admin_top_actions,
            user,
            lambda: (
                load_staff(),
                load_summary(),
                load_employee_filter(),
                load_tickets(),
                admin_unread_var.set(
                    f"🔔 {get_unread_notification_count(user[0])}"
                )
            ),
            show_workload_details
        ),
        bg=NAVY,
        fg=WHITE,
        activebackground="#E8F1FF",
        activeforeground=WHITE,
        relief="flat",
        bd=0,
        cursor="hand2",
        font=("Arial", 16, "bold"),
        padx=8
    ).pack(side="left")

    summary_frame = tk.Frame(
        admin_main,
        bg="#F5F8FF"
    )
    summary_frame.pack(
        fill="x",
        padx=28,
        pady=(20, 12)
    )

    summary_vars = {
        status: tk.StringVar(value=f"{status}: 0")
        for status in (
            "Total",
            "OPEN",
            "ASSIGNED",
            "IN PROGRESS",
            "RESOLVED"
        )
    }

    summary_colors = {
        "Total": "#FFFFFF",
        "OPEN": "#FFF8D8",
        "ASSIGNED": "#EEF2FF",
        "IN PROGRESS": "#E8F4FF",
        "RESOLVED": "#E8F8EE"
    }

    for status, variable in summary_vars.items():

        card = tk.Frame(
            summary_frame,
            bg=summary_colors[status],
            highlightbackground="#D7E4FA",
            highlightthickness=1
        )

        card.pack(
            side="left",
            fill="x",
            expand=True,
            padx=5
        )

        tk.Label(
            card,
            textvariable=variable,
            bg=summary_colors[status],
            fg="#0B1F42",
            font=("Arial", 11, "bold")
        ).pack(
            pady=14
        )

    filter_card = tk.Frame(
        admin_main,
        bg=WHITE,
        highlightbackground="#D7E4FA",
        highlightthickness=1
    )
    filter_card.pack(
        fill="x",
        padx=28,
        pady=(0, 12)
    )

    filter_frame = tk.Frame(
        filter_card,
        bg=WHITE
    )
    filter_frame.pack(
        fill="x",
        padx=18,
        pady=14
    )
    tk.Label(filter_frame, text="Show tickets:", bg=BACKGROUND, fg=TEXT,
             font=("Arial", 10, "bold")).pack(side="left")
    status_filter_var = tk.StringVar(value="All")

    status_filter = ttk.Combobox(
        filter_frame,
        textvariable=status_filter_var,
        values=[
            "All",
            "OPEN",
            "ASSIGNED",
            "IN PROGRESS",
            "RESOLVED",
            "CLOSED",
            "REOPENED"
        ],
        state="readonly",
        width=16
    )

    status_filter.bind(
        "<<ComboboxSelected>>",
        lambda event: load_tickets()
    )

    status_filter.pack(side="left", padx=8)
    tk.Label(
        filter_frame,
        text="Employee Tickets:",
        bg=BACKGROUND,
        fg=TEXT,
        font=("Arial", 10, "bold")
    ).pack(side="left", padx=(18, 5))

    employee_filter_var = tk.StringVar(value="All Employees")

    employee_filter = ttk.Combobox(
        filter_frame,
        textvariable=employee_filter_var,
        state="readonly",
        width=24
    )

    employee_filter.bind(
        "<<ComboboxSelected>>",
        lambda event: load_tickets()
    )
    employee_filter.pack(side="left", padx=5)

    employee_filter_lookup = {}
    tk.Label(filter_frame, text="Search:", bg=BACKGROUND, fg=TEXT,
         font=("Arial", 10, "bold")).pack(side="left", padx=(20, 5))

    search_var = tk.StringVar()
    search_entry = tk.Entry(
        filter_frame,
        textvariable=search_var,
        width=28,
        font=("Arial", 10)
    )
    search_entry.pack(side="left", padx=5)
    search_entry.bind(
        "<KeyRelease>",
        lambda event: load_tickets()
    )

    ticket_card = tk.Frame(
        admin_main,
        bg=WHITE,
        highlightbackground="#D7E4FA",
        highlightthickness=1
    )
    ticket_card.pack(
        fill="x",
        padx=28,
        pady=(0, 10)
    )

    table_frame = tk.Frame(
        ticket_card,
        bg=WHITE
    )
    table_frame.pack(
        fill="x",
        padx=12,
        pady=12
)
    columns = ("ID", "Employee", "Title", "Category", "Priority", "Status", "Assigned To","SLA Status")
    ticket_tree = ttk.Treeview(table_frame, columns=columns, show="headings",height=8)
    configure_tree(ticket_tree)
    widths = (55, 115, 220, 110, 85, 105, 130, 110)
    for column, width in zip(columns, widths):
        ticket_tree.heading(column, text=column)
        ticket_tree.column(column, width=width, anchor="center" if column not in ("Title",) else "w")
    ticket_tree.pack(fill="both", expand=True)

        # --------------------------------------------------
    # SLA MONITORING
    # --------------------------------------------------

    sla_monitor_card = tk.Frame(
        admin_main,
        bg=WHITE,
        highlightbackground="#D7E4FA",
        highlightthickness=1
    )

    sla_monitor_card.pack(
        fill="x",
        padx=18,
        pady=(0, 10)
    )

    tk.Label(
        sla_monitor_card,
        text="SLA Monitoring",
        bg=WHITE,
        fg=NAVY,
        font=("Arial", 11, "bold")
    ).pack(
        anchor="w",
        padx=18,
        pady=(10, 2)
    )

    tk.Label(
        sla_monitor_card,
        text="Overview of ticket SLA performance",
        bg=WHITE,
        fg="#6076A4",
        font=("Arial", 9)
    ).pack(
        anchor="w",
        padx=18,
        pady=(0, 8)
    )

    sla_summary_frame = tk.Frame(
        sla_monitor_card,
        bg=WHITE
    )

    sla_summary_frame.pack(
        fill="x",
        padx=12,
        pady=(0, 10)
    )

    sla_monitor_vars = {
        "Within SLA": tk.StringVar(value="0"),
        "Due Soon": tk.StringVar(value="0"),
        "SLA Breached": tk.StringVar(value="0"),
        "SLA Met": tk.StringVar(value="0")
    }

    sla_colors = {
        "Within SLA": "#16A34A",
        "Due Soon": "#D97706",
        "SLA Breached": "#DC2626",
        "SLA Met": "#2563EB"
    }

    for index, label in enumerate(
        (
            "Within SLA",
            "Due Soon",
            "SLA Breached",
            "SLA Met"
        )
    ):

        card = tk.Frame(
            sla_summary_frame,
            bg="#F7FAFF",
            highlightbackground="#D7E4FA",
            highlightthickness=1
        )

        card.grid(
            row=0,
            column=index,
            sticky="nsew",
            padx=5
        )

        sla_summary_frame.columnconfigure(
            index,
            weight=1
        )

        tk.Label(
            card,
            textvariable=sla_monitor_vars[label],
            bg="#F7FAFF",
            fg=sla_colors[label],
            font=("Arial", 18, "bold")
        ).pack(
            pady=(10, 2)
        )

        tk.Label(
            card,
            text=label,
            bg="#F7FAFF",
            fg="#6076A4",
            font=("Arial", 9, "bold")
        ).pack(
            pady=(0, 10)
        )

    sla_alert_frame = tk.Frame(
        sla_monitor_card,
        bg=WHITE
    )

    sla_alert_frame.pack(
        fill="x",
        padx=18,
        pady=(0, 12)
    )

    sla_alert_label = tk.Label(
        sla_alert_frame,
        text="",
        bg=WHITE,
        fg="#DC2626",
        font=("Arial", 10, "bold")
    )

    sla_alert_label.pack(
        side="left"
    )

    sla_details_button = add_button(
        sla_alert_frame,
        "View SLA Details",
        lambda: show_sla_details(),
        11
    )

    sla_details_button.pack(
        side="right",
        padx=(10, 0)
    )

    sla_details_button.config(
        width=18
    )
    
    


    

    staff_lookup = {} 

    def load_summary():
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT status, COUNT(*) FROM tickets GROUP BY status")
        counts = dict(cursor.fetchall())
        cursor.close()
        connection.close()
        summary_vars["Total"].set(f"Total Tickets: {sum(counts.values())}")
        summary_labels = {
            "OPEN": "Open Tickets",
            "ASSIGNED": "Assigned Tickets",
            "IN PROGRESS": "In Progress Tickets",
            "RESOLVED": "Resolved Tickets"
        }
        for status in ("OPEN", "ASSIGNED", "IN PROGRESS", "RESOLVED"):
            summary_vars[status].set(
                f"{summary_labels[status]}: {counts.get(status, 0)}"
            )



    def load_staff():
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id, username FROM users WHERE role = %s ORDER BY username",
            ("IT Support",)
        )

        staff_lookup.clear()

        for staff_id, name in cursor.fetchall():
            staff_lookup[name] = staff_id

        cursor.close()
        connection.close()

    def open_assign_dialog(ticket_id):
    # Fetch ticket, ensure it’s still OPEN
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT tickets.status, tickets.title, employee.username "
            "FROM tickets JOIN users AS employee ON tickets.user_id = employee.id "
            "WHERE tickets.id = %s", (ticket_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row or row[0] != "OPEN":
            messagebox.showwarning("Cannot Assign", "Ticket is not OPEN.", parent=admin_window)
            load_tickets()
            return

        # Popup window for assignment
        assign_win = tk.Toplevel(admin_window)
        setup_window(assign_win, f"Assign Ticket {ticket_id}", "500x320")
        assign_win.transient(admin_window); assign_win.grab_set()
        add_header(assign_win, f"Assign Ticket {ticket_id}", "Select an IT Support staff member", closable=False)

        form = tk.Frame(assign_win, bg=BACKGROUND)
        form.pack(fill="both", expand=True, padx=30, pady=25)

        tk.Label(form, text=f"Ticket: {ticket_id}", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0,8))
        tk.Label(form, text=f"Title: {row[1]}", font=("Arial", 10)).pack(anchor="w", pady=(0,4))
        tk.Label(form, text=f"Employee: {row[2]}", font=("Arial", 10)).pack(anchor="w", pady=(0,18))
        tk.Label(form, text="Assign To", bg=BACKGROUND, fg=NAVY, font=("Arial", 10, "bold")).pack(anchor="w")

        var_staff = tk.StringVar()
        dropdown = ttk.Combobox(form, textvariable=var_staff, values=list(staff_lookup.keys()), state="readonly", width=30)
        dropdown.pack(anchor="w", pady=(6,20))

        def confirm_assignment():
            staff_name = var_staff.get().strip()
            if not staff_name:
                messagebox.showwarning("Select Staff", "Please select an IT Support staff.", parent=assign_win)
                return
            support_id = staff_lookup[staff_name]

            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE tickets SET assigned_to = %s, status = %s WHERE id = %s AND status = %s",
                    (support_id, "ASSIGNED", ticket_id, "OPEN")
                )
                if cursor.rowcount != 1:
                    conn.rollback()
                    messagebox.showwarning("Not Updated", "Ticket is no longer OPEN. Refresh and retry.", parent=assign_win)
                    assign_win.destroy()
                    load_tickets()
                    return

                add_ticket_history(cursor, ticket_id, f"Ticket Assigned to {staff_name}", user[0], "OPEN", "ASSIGNED")
                add_notification(cursor, support_id, ticket_id, f"Ticket #{ticket_id} has been assigned to you.")

                conn.commit()
            except Exception:
                conn.rollback()
                messagebox.showerror("DB Error", "Failed to assign ticket.", parent=assign_win)
                return
            finally:
                cursor.close(); conn.close()

            assign_win.destroy()
            load_tickets()
            load_summary()
            messagebox.showinfo("Assigned", f"Ticket #{ticket_id} assigned to {staff_name}.")

        btn_frame = tk.Frame(form, bg=BACKGROUND)
        btn_frame.pack(fill="x")
        add_button(btn_frame, "Assign Ticket", confirm_assignment, 14).pack(side="left", padx=(0,8))
        add_button(btn_frame, "Cancel", assign_win.destroy, 14, True).pack(side="left")

        ticket_tree.pack(fill="both", expand=True)

    # ... all function definitions ...
    
    def handle_ticket_status_click(event):
        row = ticket_tree.identify_row(event.y)
        col = ticket_tree.identify_column(event.x)

        if not row or col != "#6":
            return

        values = ticket_tree.item(row, "values")

        if values and values[5] == "OPEN":
            open_assign_dialog(values[0])
            return "break"

    # NOW bind
    ticket_tree.bind(
        "<Button-1>",
        handle_ticket_status_click
    )
    

    def load_employee_filter():
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT username
            FROM users
            WHERE role = 'Employee'
            ORDER BY username
        """)

        employee_filter_lookup.clear()
        employee_values = ["All Employees"]

        for (username,) in cursor.fetchall():
            employee_values.append(username)
            employee_filter_lookup[username] = username

        employee_filter["values"] = employee_values

        cursor.close()
        connection.close()

    def show_workload_details():

        details_window = tk.Toplevel(admin_window)

        setup_window(
            details_window,
            "Support Staff Workload",
            "900x550"
        )

        maximize_window(details_window)

        add_header(
            details_window,
            "Support Staff Workload",
            "Detailed workload of IT Support staff",
            closable=True
        )

        table_frame = tk.Frame(
            details_window,
            bg=BACKGROUND
        )

        table_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=15
        )

        columns = (
            "Support Staff",
            "Assigned",
            "In Progress",
            "Resolved",
            "Active Tickets"
        )

        details_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        configure_tree(details_tree)

        widths = (
            220,
            130,
            150,
            130,
            150
        )

        for column, width in zip(columns, widths):

            details_tree.heading(
                column,
                text=column
            )

            details_tree.column(
                column,
                width=width,
                anchor="center"
            )

        details_tree.pack(
            fill="both",
            expand=True
        )

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                users.username,

                COALESCE(SUM(
                    CASE
                        WHEN tickets.status = 'ASSIGNED'
                        THEN 1
                        ELSE 0
                    END
                ), 0) AS assigned_count,

                COALESCE(SUM(
                    CASE
                        WHEN tickets.status = 'IN PROGRESS'
                        THEN 1
                        ELSE 0
                    END
                ), 0) AS progress_count,

                COALESCE(SUM(
                    CASE
                        WHEN tickets.status = 'RESOLVED'
                        THEN 1
                        ELSE 0
                    END
                ), 0) AS resolved_count,

                COALESCE(SUM(
                    CASE
                        WHEN tickets.status IN ('ASSIGNED', 'IN PROGRESS')
                        THEN 1
                        ELSE 0
                    END
                ), 0) AS active_count

            FROM users

            LEFT JOIN tickets
                ON users.id = tickets.assigned_to

            WHERE users.role = 'IT Support'

            GROUP BY users.id, users.username

            ORDER BY users.username
        """)

        workload_rows = cursor.fetchall()

        cursor.close()
        connection.close()

        for staff, assigned, progress, resolved, active in workload_rows:

            details_tree.insert(
                "",
                tk.END,
                values=(
                    staff,
                    assigned,
                    progress,
                    resolved,
                    active
                )
            )

        add_button(
            details_window,
            "Close",
            details_window.destroy,
            14,
            True
        ).pack(
            side="bottom",
            pady=12
        )


    def load_workload():

        workload_tree.delete(*workload_tree.get_children())

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                users.username,
                COALESCE(SUM(
                    CASE WHEN tickets.status = 'ASSIGNED' THEN 1 ELSE 0 END
                ), 0) AS assigned_count,
                COALESCE(SUM(
                    CASE WHEN tickets.status = 'IN PROGRESS' THEN 1 ELSE 0 END
                ), 0) AS progress_count,
                COALESCE(SUM(
                    CASE WHEN tickets.status = 'RESOLVED' THEN 1 ELSE 0 END
                ), 0) AS resolved_count,
                COALESCE(SUM(
                    CASE WHEN tickets.status IN ('ASSIGNED', 'IN PROGRESS')
                    THEN 1 ELSE 0 END
                ), 0) AS active_count
            FROM users
            LEFT JOIN tickets
                ON users.id = tickets.assigned_to
            WHERE users.role = 'IT Support'
            GROUP BY users.id, users.username
            ORDER BY users.username
        """)

        for staff, assigned, progress, resolved, active in cursor.fetchall():
            workload_tree.insert(
                "",
                tk.END,
                values=(
                    staff,
                    assigned,
                    progress,
                    resolved,
                    active
                )
            )

        cursor.close()
        connection.close()

    def show_sla_details():

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                tickets.id,
                employee.username,
                tickets.priority,
                tickets.status,
                tickets.created_at,
                tickets.resolved_at
            FROM tickets
            JOIN users AS employee
                ON tickets.user_id = employee.id
            ORDER BY tickets.id DESC
        """)

        tickets = cursor.fetchall()

        cursor.close()
        connection.close()

        sla_limits = {
            "Critical": 4,
            "High": 8,
            "Medium": 24,
            "Low": 48
        }

        details_window = tk.Toplevel(admin_window)

        setup_window(
            details_window,
            "SLA Monitoring Details",
            "1050x600"
        )

        maximize_window(details_window)

        add_header(
            details_window,
            "SLA Monitoring Details",
            "Detailed SLA performance of support tickets",
            closable=True
        )

        table_frame = tk.Frame(
            details_window,
            bg=BACKGROUND
        )

        table_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=15
        )

        columns = (
            "Ticket ID",
            "Employee",
            "Priority",
            "SLA Limit",
            "Elapsed Time",
            "SLA Status"
        )

        details_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        configure_tree(details_tree)

        widths = (
            90,
            180,
            120,
            120,
            160,
            160
        )

        for column, width in zip(columns, widths):

            details_tree.heading(
                column,
                text=column
            )

            details_tree.column(
                column,
                width=width,
                anchor="center"
            )

        details_tree.pack(
            fill="both",
            expand=True
        )

        for ticket in tickets:

            ticket_id = ticket[0]
            employee = ticket[1]
            priority = ticket[2]
            status = ticket[3]
            created_at = ticket[4]
            resolved_at = ticket[5]

            sla_hours = sla_limits.get(
                priority,
                24
            )

            end_time = (
                resolved_at
                if status == "RESOLVED" and resolved_at
                else datetime.now()
            )

            elapsed_seconds = (
                end_time - created_at
            ).total_seconds()

            elapsed_hours = (
                elapsed_seconds / 3600
            )

            elapsed_minutes = int(
                elapsed_seconds / 60
            )

            hours = elapsed_minutes // 60
            minutes = elapsed_minutes % 60

            elapsed_display = (
                f"{hours}h {minutes}m"
            )

            if status == "RESOLVED":

                if elapsed_hours <= sla_hours:
                    sla_status = "SLA Met"
                else:
                    sla_status = "SLA Breached"

            else:

                if elapsed_hours > sla_hours:
                    sla_status = "SLA Breached"

                elif elapsed_hours >= sla_hours * 0.75:
                    sla_status = "Due Soon"

                else:
                    sla_status = "Within SLA"

            details_tree.insert(
                "",
                tk.END,
                values=(
                    ticket_id,
                    employee,
                    priority,
                    f"{sla_hours} hrs",
                    elapsed_display,
                    sla_status
                )
            )

        add_button(
            details_window,
            "Close",
            details_window.destroy,
            14,
            True
        ).pack(
            side="bottom",
            pady=12
        )

    def load_sla_monitoring():

        

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                tickets.id,
                employee.username,
                tickets.priority,
                tickets.status,
                tickets.created_at,
                tickets.resolved_at
            FROM tickets
            JOIN users AS employee
                ON tickets.user_id = employee.id
            ORDER BY tickets.id DESC
        """)

        tickets = cursor.fetchall()

        cursor.close()
        connection.close()

        counts = {
            "Within SLA": 0,
            "Due Soon": 0,
            "SLA Breached": 0,
            "SLA Met": 0
        }

        sla_limits = {
            "Critical": 4,
            "High": 8,
            "Medium": 24,
            "Low": 48
        }

        for ticket in tickets:

            ticket_id = ticket[0]
            employee = ticket[1]
            priority = ticket[2]
            status = ticket[3]
            created_at = ticket[4]
            resolved_at = ticket[5]

            sla_hours = sla_limits.get(
                priority,
                24
            )

            # ------------------------------------------
            # ELAPSED TIME
            # ------------------------------------------

            end_time = (
                resolved_at
                if status == "RESOLVED" and resolved_at
                else datetime.now()
            )

            elapsed_seconds = (
                end_time - created_at
            ).total_seconds()

            elapsed_hours = (
                elapsed_seconds / 3600
            )

            elapsed_minutes = int(
                elapsed_seconds / 60
            )

            hours = elapsed_minutes // 60
            minutes = elapsed_minutes % 60

            elapsed_display = (
                f"{hours}h {minutes}m"
            )

            # ------------------------------------------
            # SLA STATUS
            # ------------------------------------------

            if status == "RESOLVED":

                if elapsed_hours <= sla_hours:
                    sla_status = "SLA Met"
                else:
                    sla_status = "SLA Breached"

            else:

                if elapsed_hours > sla_hours:
                    sla_status = "SLA Breached"

                elif elapsed_hours >= sla_hours * 0.75:
                    sla_status = "Due Soon"

                else:
                    sla_status = "Within SLA"

            counts[sla_status] += 1

           

       # ------------------------------------------
        # UPDATE SUMMARY CARDS
        # ------------------------------------------

        for label in counts:

            sla_monitor_vars[label].set(
                str(counts[label])
            )

        # ------------------------------------------
        # SLA WARNING
        # ------------------------------------------

        if counts["SLA Breached"] > 0:

            sla_alert_label.config(
                text=f"⚠ {counts['SLA Breached']} ticket(s) have breached SLA."
            )

        elif counts["Due Soon"] > 0:

            sla_alert_label.config(
                text=f"⚠ {counts['Due Soon']} ticket(s) are due soon."
            )

        else:

            sla_alert_label.config(
                text="✓ All active tickets are within SLA."
            )

    def load_tickets():
        ticket_tree.delete(*ticket_tree.get_children())
        connection = get_connection()
        cursor = connection.cursor()
        query = """
            SELECT tickets.id,
                    employee.username,
                    tickets.title,
                    categories.category_name,
                    tickets.priority,
                    tickets.status,
                    COALESCE(support_staff.username, 'Not Assigned'),
                    CASE
                        WHEN tickets.status = 'RESOLVED' THEN
                            CASE
                                WHEN TIMESTAMPDIFF(
                                    HOUR,
                                    tickets.created_at,
                                    tickets.resolved_at
                                ) <=
                                CASE tickets.priority
                                    WHEN 'Critical' THEN 4
                                    WHEN 'High' THEN 8
                                    WHEN 'Medium' THEN 24
                                    WHEN 'Low' THEN 48
                                END
                                THEN 'SLA Met'
                                ELSE 'SLA Breached'
                            END
                        ELSE
                            CASE
                                WHEN TIMESTAMPDIFF(
                                    HOUR,
                                    tickets.created_at,
                                    CURRENT_TIMESTAMP
                                ) <=
                                CASE tickets.priority
                                    WHEN 'Critical' THEN 4
                                    WHEN 'High' THEN 8
                                    WHEN 'Medium' THEN 24
                                    WHEN 'Low' THEN 48
                                END
                                THEN 'Within SLA'
                                ELSE 'SLA Breached'
                            END
                    END AS sla_status
            FROM tickets
            JOIN users AS employee ON tickets.user_id = employee.id
            JOIN categories ON tickets.category_id = categories.id
            LEFT JOIN users AS support_staff ON tickets.assigned_to = support_staff.id
        """
        conditions = []
        params = []
        if status_filter_var.get() != "All":
            conditions.append("tickets.status = %s")
            params.append(status_filter_var.get())

        if employee_filter_var.get() != "All Employees":
            conditions.append("employee.username = %s")
            params.append(
                employee_filter_lookup[employee_filter_var.get()]
            )

        search_text = search_var.get().strip()

        if search_text:
            conditions.append("""
                (
                    tickets.title LIKE %s
                    OR employee.username LIKE %s
                    OR categories.category_name LIKE %s
                    OR tickets.priority LIKE %s
                    OR tickets.status LIKE %s
                    OR support_staff.username LIKE %s
                )
            """)

            search_pattern = f"%{search_text}%"
            params.extend([search_pattern] * 6)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY tickets.id DESC"

        cursor.execute(query, tuple(params))

        for ticket in cursor.fetchall():
            insert_category_ticket(ticket_tree, ticket, 3)

        cursor.close()
        connection.close()
        
    def assign_ticket():
        selected = ticket_tree.selection()
        if not selected or not staff_var.get():
            messagebox.showwarning("Missing Selection", "Select an OPEN ticket and an IT Support staff member.")
            return
        values = ticket_tree.item(selected[0])["values"]
        if values[5] != "OPEN":
            messagebox.showwarning("Ticket Cannot Be Assigned", "Only OPEN tickets can be assigned.")
            return
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""UPDATE tickets SET assigned_to = %s, status = %s
                              WHERE id = %s AND status = %s""",
                           (staff_lookup[staff_var.get()], "ASSIGNED", values[0], "OPEN"))
            updated = cursor.rowcount
            if updated != 1:
                connection.rollback()
                messagebox.showwarning("Ticket Not Updated", "Refresh and try again.")
                return

            add_ticket_history(
                cursor, values[0], f"Ticket Assigned to {staff_var.get()}",
                user[0], "OPEN", "ASSIGNED"
            )
            add_notification(
                cursor,
                staff_lookup[staff_var.get()],
                values[0],
                f"Ticket #{values[0]} has been assigned to you."
                )
            
            connection.commit()
        except mysql.connector.Error:
            connection.rollback()
            messagebox.showerror("Database Error", "Ticket assignment could not be completed.")
            return
        finally:
            cursor.close()
            connection.close()

        if updated:
            messagebox.showinfo("Ticket Assigned", f"Ticket #{values[0]} was assigned to {staff_var.get()}.")
            staff_var.set("")
            load_tickets()
            load_summary()
            load_workload()
        else:
            messagebox.showwarning("Ticket Not Updated", "Refresh and try again.")


    def show_details(event):
        selected = ticket_tree.selection()

        if not selected:
            return

        ticket_id = ticket_tree.item(
            selected[0]
        )["values"][0]

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                tickets.id,
                employee.username,
                tickets.title,
                categories.category_name,
                tickets.description,
                tickets.priority,
                tickets.status,
                COALESCE(
                    support_staff.username,
                    'Not Assigned'
                ),
                tickets.created_at,
                tickets.updated_at,
                COALESCE(
                    tickets.resolution_note,
                    'No resolution note yet.'
                )
            FROM tickets
            JOIN users AS employee
                ON tickets.user_id = employee.id
            JOIN categories
                ON tickets.category_id = categories.id
            LEFT JOIN users AS support_staff
                ON tickets.assigned_to = support_staff.id
            WHERE tickets.id = %s
        """, (ticket_id,))

        ticket = cursor.fetchone()

    # --------------------------------------------------
    # COMMENTS
    # --------------------------------------------------

        cursor.execute("""
            SELECT
                users.name,
                users.role,
                users.department,
                ticket_comments.comment,
                ticket_comments.created_at
            FROM ticket_comments
            JOIN users
                ON ticket_comments.user_id = users.id
            WHERE ticket_comments.ticket_id = %s
            ORDER BY ticket_comments.created_at ASC
        """, (ticket_id,))

        comments = cursor.fetchall()

        cursor.close()
        connection.close()

        if not ticket:
            return

        details = (
            open_in_app_dialog(850, 650)
            if IN_APP_MODE
            else tk.Toplevel(admin_window)
        )

        if not IN_APP_MODE:
            setup_window(
                details,
                "Admin Ticket Details",
                "850x650"
            )

        add_header(
            details,
            f"Ticket {ticket[0]}",
            "Administrative ticket details",
            closable=IN_APP_MODE
        )

        # --------------------------------------------------
        # TICKET DETAILS TABLE
        # --------------------------------------------------

        table_frame = tk.Frame(
            details,
            bg=BACKGROUND
        )

        table_frame.pack(
            fill="both",
            expand=True,
            padx=60,
            pady=20
        )

        columns = (
            "Field",
            "Details"
        )

        details_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        configure_tree(details_tree)

        details_tree.heading(
            "Field",
            text="Field"
        )

        details_tree.heading(
            "Details",
            text="Details"
        )

        details_tree.column(
            "Field",
            width=240,
            anchor="w"
        )

        details_tree.column(
            "Details",
            width=600,
            anchor="w"
        )

        details_tree.pack(
            fill="both",
            expand=True
        )

        detail_rows = [
            ("Ticket ID", ticket[0]),
            ("Employee", ticket[1]),
            ("Title", ticket[2]),
            ("Category", ticket[3]),
            ("Description", ticket[4] or "No description"),
            ("Priority", ticket[5]),
            ("Status", ticket[6]),
            ("Assigned To", ticket[7]),
            ("Created On", ticket[8]),
            ("Last Updated", ticket[9]),
            ("Resolution Note", ticket[10])
        ]

        for field, value in detail_rows:

            details_tree.insert(
                "",
                tk.END,
                values=(
                    field,
                    value
                )
            )

    # --------------------------------------------------
    # COMMENTS
    # --------------------------------------------------

        comments_label = tk.Label(
            details,
            text="Comments",
            bg=BACKGROUND,
            fg=NAVY,
            font=("Arial", 12, "bold")
        )

        comments_label.pack(
            anchor="w",
            padx=60,
            pady=(5, 5)
        )

        comments_box = tk.Frame(
            details,
            bg=WHITE,
            highlightbackground="#D7E4FA",
            highlightthickness=1
        )

        comments_box.pack(
            fill="x",
            padx=60,
            pady=(0, 10)
        )

        if comments:

            for name, role, department, comment_text, created_at in comments:

                comment_frame = tk.Frame(
                    comments_box,
                    bg="#F7FAFF",
                    highlightbackground="#E1EAF8",
                    highlightthickness=1
                )

                comment_frame.pack(
                    fill="x",
                    padx=10,
                    pady=5
                )

                tk.Label(
                    comment_frame,
                    text=(
                        f"{name} — {role}"
                        if role == "IT Support"
                        else f"{name} — {department}"
                    ),
                    bg="#F7FAFF",
                    fg=NAVY,
                    font=("Arial", 10, "bold")
                ).pack(
                    anchor="w",
                    padx=10,
                    pady=(8, 2)
                )

                tk.Label(
                    comment_frame,
                    text=str(comment_text),
                    bg="#F7FAFF",
                    fg="#536987",
                    font=("Arial", 10),
                    justify="left",
                    anchor="w",
                    wraplength=750
                ).pack(
                    fill="x",
                    padx=10,
                    pady=(0, 4)
                )

                tk.Label(
                    comment_frame,
                    text=(
                        created_at.strftime("%d-%m-%Y %H:%M")
                        if created_at
                        else ""
                    ),
                    bg="#F7FAFF",
                    fg="#8A9AB8",
                    font=("Arial", 8)
                ).pack(
                    anchor="e",
                    padx=10,
                    pady=(0, 8)
                )

        else:

            tk.Label(
                comments_box,
                text="No comments yet.",
                bg=WHITE,
                fg="#6076A4",
                font=("Arial", 10)
            ).pack(
                pady=15
            )

        # --------------------------------------------------
        # VIEW HISTORY
        # --------------------------------------------------

        add_button(
            details,
            "View Ticket History",
            lambda: show_ticket_history(
                details,
                ticket[0]
            ),
            20
        ).pack(
            pady=(0, 15)
        )
    add_button(filter_frame, "Show All", lambda: (status_filter_var.set("All"),employee_filter_var.set("All Employees"), load_tickets()), 10, True).pack(side="left", padx=3) 
    ticket_tree.bind("<Double-1>", show_details)
    load_staff()
    load_employee_filter()
    load_summary()
    load_sla_monitoring() 
    load_tickets()


def it_support_dashboard(user):
    for child in window.winfo_children():
        child.destroy()
    support_window = window
    setup_window(support_window, "IT Support Dashboard", "820x540")
    maximize_window(support_window)
    support_window.protocol(
        "WM_DELETE_WINDOW",
        show_login_window
    )
    add_header(support_window, f"IT Support Dashboard - {user[1]}", "Tickets assigned to you")
    support_top_actions = tk.Frame(
        support_window,
        bg=NAVY
    )
    support_top_actions.place(
        relx=0.97,
        y=8,
        anchor="ne"
    )

    support_unread_var = tk.StringVar(
        value=f"🔔 {get_unread_notification_count(user[0])}"
    )

    tk.Button(
        support_top_actions,
        textvariable=support_unread_var,
        command=lambda: (
            show_notifications(user),
            support_unread_var.set("🔔 0")
        ),
        bg=NAVY,
        fg=WHITE,
        activebackground="#28528A",
        activeforeground=WHITE,
        relief="flat",
        bd=0,
        cursor="hand2",
        font=("Arial", 10, "bold")
    ).pack(side="left", padx=4)

    tk.Button(
        support_top_actions,
        text="☰",
        command=lambda: show_dashboard_menu(
            support_top_actions,
            user,
            load_tickets,
            None 
        ),
        bg=NAVY,
        fg=WHITE,
        activebackground="#28528A",
        activeforeground=WHITE,
        relief="flat",
        bd=0,
        cursor="hand2",
        font=("Arial", 16, "bold"),
        padx=8
    ).pack(side="left")
    
    
    def load_work_summary():

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(status IN ('ASSIGNED', 'IN PROGRESS')) AS active,
                SUM(status = 'IN PROGRESS') AS in_progress,
                SUM(status = 'RESOLVED') AS resolved
            FROM tickets
            WHERE assigned_to = %s
        """, (user[0],))

        total, active, in_progress, resolved = cursor.fetchone()

        cursor.close()
        connection.close()

        total = total or 0
        active = active or 0
        in_progress = in_progress or 0
        resolved = resolved or 0

        summary_card = tk.Frame(
            support_window,
            bg=WHITE,
            highlightbackground="#D7E4FA",
            highlightthickness=1
        )

        summary_card.pack(
            fill="x",
            padx=18,
            pady=(5, 10)
        )

        tk.Label(
            summary_card,
            text="My Work Summary",
            bg=WHITE,
            fg=NAVY,
            font=("Arial", 12, "bold")
        ).pack(
            anchor="w",
            padx=18,
            pady=(12, 2)
        )

        tk.Label(
            summary_card,
            text="Overview of your assigned support work",
            bg=WHITE,
            fg="#6076A4",
            font=("Arial", 9)
        ).pack(
            anchor="w",
            padx=18,
            pady=(0, 10)
        )

        stats_frame = tk.Frame(
            summary_card,
            bg=WHITE
        )
        stats_frame.pack(
            fill="x",
            padx=12,
            pady=(0, 12)
        )

        summary_data = [
            ("Total Tickets", total, "#315A96"),
            ("Active", active, "#D97706"),
            ("In Progress", in_progress, "#2563EB"),
            ("Resolved", resolved, "#16A34A")
        ]

        for title, value, color in summary_data:

            card = tk.Frame(
                stats_frame,
                bg="#F7FAFF",
                highlightbackground="#E1EAF8",
                highlightthickness=1
            )

            card.pack(
                side="left",
                fill="x",
                expand=True,
                padx=5
            )

            tk.Label(
                card,
                text=str(value),
                bg="#F7FAFF",
                fg=color,
                font=("Arial", 18, "bold")
            ).pack(
                pady=(8, 0)
            )

            tk.Label(
                card,
                text=title,
                bg="#F7FAFF",
                fg="#6076A4",
                font=("Arial", 9, "bold")
            ).pack(
                pady=(0, 8)
            )


    load_work_summary()
     # ---------------- TICKET TABLE ----------------

    table_frame = tk.Frame(
        support_window,
        bg=BACKGROUND
    )
    table_frame.pack(
        fill="x",
        padx=18,
        pady=(16, 8)
    )

    columns = (
        "Ticket ID",
        "Title",
        "Category",
        "Priority",
        "Status"
    )

    ticket_tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        height=8
    )

    configure_tree(ticket_tree)

    for column, width in zip(
        columns,
        (80, 300, 160, 120, 140)
    ):
        ticket_tree.heading(
            column,
            text=column
        )

        ticket_tree.column(
            column,
            width=width,
            anchor="center" if column != "Title" else "w"
        )

    ticket_tree.pack(
        fill="x",
        ipady=8
    )

    # ---------------- TICKET FILTER ----------------

    ticket_filter_var = tk.StringVar(
        value="Active Tickets"
    )

    filter_frame = tk.Frame(
        support_window,
        bg=BACKGROUND
    )
    filter_frame.pack(
        fill="x",
        padx=18,
        pady=(0, 8)
    )

    tk.Label(
        filter_frame,
        text="My Tickets:",
        bg=BACKGROUND,
        fg=NAVY,
        font=("Arial", 10, "bold")
    ).pack(side="left")

    ticket_filter = ttk.Combobox(
        filter_frame,
        textvariable=ticket_filter_var,
        values=[
            "Active Tickets",
            "Resolved Tickets",
            "All My Tickets"
        ],
        state="readonly",
        width=20
    )

    ticket_filter.pack(
        side="left",
        padx=8
    )

    ticket_filter.bind(
        "<<ComboboxSelected>>",
        lambda event: load_tickets()
    )

    


    def load_tickets():
        ticket_tree.delete(*ticket_tree.get_children())

        connection = get_connection()
        cursor = connection.cursor()

        query = """
            SELECT tickets.id,
                tickets.title,
                categories.category_name,
                tickets.priority,
                tickets.status
            FROM tickets
            JOIN categories
                ON tickets.category_id = categories.id
            WHERE tickets.assigned_to = %s
        """

        parameters = [user[0]]

        selected_filter = ticket_filter_var.get()

        if selected_filter == "Active Tickets":

            query += """
                AND tickets.status IN ('ASSIGNED', 'IN PROGRESS')
            """

        elif selected_filter == "Resolved Tickets":

            query += """
                AND tickets.status = 'RESOLVED'
            """

        query += " ORDER BY tickets.id DESC"

        cursor.execute(
            query,
            tuple(parameters)
        )

        tickets = cursor.fetchall()

        cursor.close()
        connection.close()

        if not tickets:

            if selected_filter == "Active Tickets":
                message = "No active tickets assigned to you."

            elif selected_filter == "Resolved Tickets":
                message = "You have not resolved any tickets yet."

            else:
                message = "No tickets assigned to you."

            ticket_tree.insert(
                "",
                tk.END,
                values=(
                    "—",
                    message,
                    "—",
                    "—",
                    "—"
                )
            )

        else:

            for ticket in tickets:
                insert_ticket(
                    ticket_tree,
                    ticket,
                    4
                )

    load_tickets()

    def show_ticket_details(event=None):

        selected = ticket_tree.selection()

        if not selected:
            return

        values = ticket_tree.item(
            selected[0]
        )["values"]

        ticket_id = values[0]

        connection = get_connection()
        cursor = connection.cursor()

        # ---------- TICKET DETAILS ----------
        cursor.execute(
            """
            SELECT
                employee.name,
                employee.department,
                employee.username,
                tickets.title,
                categories.category_name,
                tickets.priority,
                tickets.description,
                tickets.status,
                COALESCE(
                    tickets.resolution_note,
                    'No resolution note yet.'
                ),
                tickets.created_at,
                tickets.updated_at
            FROM tickets
            JOIN users AS employee
                ON tickets.user_id = employee.id
            JOIN categories
                ON tickets.category_id = categories.id
            WHERE tickets.id = %s
            AND tickets.assigned_to = %s
            """,
            (ticket_id, user[0])
        )

        ticket = cursor.fetchone()

        if not ticket:

            cursor.close()
            connection.close()

            messagebox.showerror(
                "Ticket Not Found",
                "The selected ticket could not be found."
            )

            return

        # ---------- COMMENTS ----------
        cursor.execute(
            """
            SELECT
                users.name,
                users.role,
                users.department,
                ticket_comments.comment,
                ticket_comments.created_at
            FROM ticket_comments
            JOIN users
                ON ticket_comments.user_id = users.id
            WHERE ticket_comments.ticket_id = %s
            ORDER BY ticket_comments.created_at ASC
            """,
            (ticket_id,)
        )

        comments = cursor.fetchall()

        cursor.close()
        connection.close()

        # ---------- DETAILS WINDOW ----------
        details = tk.Toplevel(support_window)

        setup_window(
            details,
            "Ticket Details",
            "900x700"
        )

        maximize_window(details)

        add_header(
            details,
            f"Ticket {ticket_id}",
            "Employee, ticket and comment details"
        )

        # =========================================================
        # TICKET DETAILS
        # =========================================================

        table_frame = tk.Frame(
            details,
            bg=BACKGROUND
        )

        table_frame.pack(
            fill="x",
            padx=25,
            pady=(20, 10)
        )

        detail_rows = [
            ("Employee", ticket[0]),
            ("Department", ticket[1]),
            ("Username", ticket[2]),
            ("Ticket", ticket[3]),
            ("Category", ticket[4]),
            ("Priority", ticket[5]),
            ("Status", ticket[7]),
            ("Created", ticket[9]),
            ("Last Updated", ticket[10]),
            ("Description", ticket[6] or ""),
            ("Resolution Note", ticket[8])
        ]

        for field, value in detail_rows:

            row = tk.Frame(
                table_frame,
                bg=WHITE,
                highlightbackground="#D7E4FA",
                highlightthickness=1
            )

            row.pack(
                fill="x"
            )

            tk.Label(
                row,
                text=field,
                bg=WHITE,
                fg="#0B1F42",
                font=("Arial", 10, "bold"),
                width=18,
                anchor="w"
            ).pack(
                side="left",
                padx=12,
                pady=5
            )

            tk.Label(
                row,
                text=str(value),
                bg=WHITE,
                fg="#536987",
                font=("Arial", 10),
                anchor="w",
                justify="left",
                wraplength=650
            ).pack(
                side="left",
                fill="x",
                expand=True,
                padx=12,
                pady=8
            )

        # =========================================================
        # COMMENTS
        # =========================================================

        comments_frame = tk.Frame(
            details,
            bg=BACKGROUND
        )

        comments_frame.pack(
            fill="x",
            padx=25,
            pady=(5, 5)
        )

        tk.Label(
            comments_frame,
            text="Comments",
            bg=BACKGROUND,
            fg=NAVY,
            font=("Arial", 12, "bold")
        ).pack(
            anchor="w",
            pady=(5, 8)
        )

        comments_box = tk.Frame(
            comments_frame,
            bg=WHITE,
            highlightbackground="#D7E4FA",
            highlightthickness=1
        )

        comments_box.pack(
            fill="both",
            expand=True
        )

        if comments:

            for name, role, department, comment_text, created_at in comments:

                comment_frame = tk.Frame(
                    comments_box,
                    bg="#F7FAFF",
                    highlightbackground="#E1EAF8",
                    highlightthickness=1
                )

                comment_frame.pack(
                    fill="x",
                    padx=10,
                    pady=5
                )

                # Username / Role / Department
                tk.Label(
                    comment_frame,
                    text=(
                        f"{name} — {role}"
                        if role == "IT Support"
                        else f"{name} — {department}"
                    ),
                    bg="#F7FAFF",
                    fg=NAVY,
                    font=("Arial", 10, "bold")
                ).pack(
                    anchor="w",
                    padx=10,
                    pady=(8, 2)
                )

                # Comment
                tk.Label(
                    comment_frame,
                    text=str(comment_text),
                    bg="#F7FAFF",
                    fg="#536987",
                    font=("Arial", 10),
                    justify="left",
                    anchor="w",
                    wraplength=750
                ).pack(
                    fill="x",
                    padx=10,
                    pady=(0, 4)
                )

                # Date / Time
                tk.Label(
                    comment_frame,
                    text=(
                        created_at.strftime("%d-%m-%Y %H:%M")
                        if created_at
                        else ""
                    ),
                    bg="#F7FAFF",
                    fg="#8A9AB8",
                    font=("Arial", 8)
                ).pack(
                    anchor="e",
                    padx=10,
                    pady=(0, 8)
                )

        else:

            tk.Label(
                comments_box,
                text="No comments yet.",
                bg=WHITE,
                fg="#6076A4",
                font=("Arial", 10)
            ).pack(
                pady=20
            )
    # =========================================================
    # ADD COMMENT
    # =========================================================

        if str(ticket[7]).upper() != "CLOSED":

            input_frame = tk.Frame(
                details,
                bg=BACKGROUND
            )

            input_frame.pack(
                fill="x",
                padx=25,
                pady=(0, 5)
            )

            tk.Label(
                input_frame,
                text="Add Comment",
                bg=BACKGROUND,
                fg=NAVY,
                font=("Arial", 10, "bold")
            ).pack(
                anchor="w"
            )

            comment_entry = tk.Text(
                input_frame,
                height=2,
                font=("Arial", 10),
                wrap="word"
            )

            comment_entry.pack(
                fill="x",
                pady=(5, 8)
            )

            def add_it_support_comment():

                comment_text = comment_entry.get(
                    "1.0",
                    tk.END
                ).strip()

                if not comment_text:

                    messagebox.showwarning(
                        "Empty Comment",
                        "Please enter a comment.",
                        parent=details
                    )

                    return

                connection = get_connection()
                cursor = connection.cursor()

                cursor.execute(
                    """
                    INSERT INTO ticket_comments
                    (
                        ticket_id,
                        user_id,
                        comment
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        ticket_id,
                        user[0],
                        comment_text
                    )
                )

                # Get ticket owner (Employee)
                cursor.execute(
                    """
                    SELECT user_id
                    FROM tickets
                    WHERE id = %s
                    """,
                    (ticket_id,)
                )

                ticket_owner = cursor.fetchone()

                if ticket_owner and ticket_owner[0]:

                    add_notification(
                        cursor,
                        ticket_owner[0],
                        ticket_id,
                        f"IT Support added a new comment to Ticket #{ticket_id}."
                    )

                connection.commit()

                cursor.close()
                connection.close()

                messagebox.showinfo(
                    "Comment Added",
                    "Your comment has been added successfully.",
                    parent=details
                )

                details.destroy()

                show_ticket_details()

            add_button(
                input_frame,
                "Add Comment",
                add_it_support_comment,
                14
            ).pack(
                anchor="e"
            )

        else:

            tk.Label(
                details,
                text="This ticket is closed. Comments can only be viewed.",
                bg=BACKGROUND,
                fg="#B3261E",
                font=("Arial", 10, "bold")
            ).pack(
                padx=25,
                pady=(5, 15)
            )

    def update_status():
        selected = ticket_tree.selection()

        if not selected:
            messagebox.showwarning(
                "No Ticket Selected",
                "Select a ticket first."
            )
            return

        values = ticket_tree.item(selected[0])["values"]

        ticket_id = values[0]
        current_status = values[4]

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                tickets.description,
                categories.category_name,
                tickets.priority,
                tickets.created_at,
                tickets.resolved_at
            FROM tickets
            JOIN categories
                ON tickets.category_id = categories.id
            WHERE tickets.id = %s
            AND tickets.assigned_to = %s
            """,
            (ticket_id, user[0])
        )

        ticket_data = cursor.fetchone()

        cursor.close()
        connection.close()

        if not ticket_data:
            messagebox.showerror(
                "Ticket Not Found",
                "The selected ticket could not be found."
            )
            return

        ticket_description = (
            ticket_data[0]
            if ticket_data[0]
            else "No description provided."
        )

        category = ticket_data[1]
        priority = ticket_data[2]
        created_at = ticket_data[3]
        resolved_at = ticket_data[4]


        # Strict workflow
        if current_status == "ASSIGNED":
            allowed_statuses = ["IN PROGRESS"]

        elif current_status == "IN PROGRESS":
            allowed_statuses = ["RESOLVED"]

        else:
            messagebox.showwarning(
                "Status Cannot Be Updated",
                f"Ticket {ticket_id} is already {current_status}.\n\n"
                "Only ASSIGNED or IN PROGRESS tickets can be updated."
            )
            return

    # ---------------------------------------------------------
    # UPDATE WINDOW
    # ---------------------------------------------------------

        update_window = (
            open_in_app_dialog(1100, 650)
            if IN_APP_MODE
            else tk.Toplevel(support_window)
        )

        if not IN_APP_MODE:
            setup_window(
                update_window,
                "Update Ticket Status",
                "1100x650"
            )
            maximize_window(update_window)

        add_header(
            update_window,
            f"Update Ticket {ticket_id}",
            "Record the latest support progress",
            closable=IN_APP_MODE
        )

    # ---------------------------------------------------------
    # MAIN BODY
    # ---------------------------------------------------------

        body = tk.Frame(
            update_window,
            bg=BACKGROUND
        )
        body.pack(
            fill="both",
            expand=True,
            padx=45,
            pady=25
        )

    # ---------------------------------------------------------
    # TICKET SUMMARY
    # ---------------------------------------------------------

        summary_card = tk.Frame(
            body,
            bg=WHITE,
            highlightbackground="#D7E4FA",
            highlightthickness=1
        )
        summary_card.pack(
            fill="x",
            pady=(0, 15)
        )

        summary_inner = tk.Frame(
            summary_card,
            bg="#F7FAFF"
        )
        summary_inner.pack(
            fill="x",
            padx=10,
            pady=10
        )

        summary_items = [
            ("🎫", "Ticket ID", str(ticket_id)),
            ("🏷", "Category", category),
            ("⚠", "Priority", priority),
            ("●", "Current Status", current_status),
            (
                "📅",
                "Created On",
                created_at.strftime("%d-%m-%Y %H:%M")
                if created_at
                else "—"
            )
        ]

        for index, (icon, label, value) in enumerate(summary_items):

            item = tk.Frame(
                summary_inner,
                bg="#F7FAFF"
            )

            item.grid(
                row=0,
                column=index,
                sticky="nsew",
                padx=8,
                pady=5
            )

            summary_inner.columnconfigure(
                index,
                weight=1
            )

            tk.Label(
                item,
                text=icon,
                bg="#F7FAFF",
                fg=BLUE,
                font=("Segeo UI", 16)
            ).pack(
                side="left",
                padx=(4, 8)
            )

            text_frame = tk.Frame(
                item,
                bg="#F7FAFF"
            )
            text_frame.pack(
                side="left"
            )

            tk.Label(
                text_frame,
                text=label,
                bg="#F7FAFF",
                fg="#6076A4",
                font=("Segeo UI", 9)
            ).pack(
                anchor="w"
            )

            tk.Label(
                text_frame,
                text=value,
                bg="#F7FAFF",
                fg=NAVY,
                font=("Segeo UI", 10, "bold")
            ).pack(
                anchor="w"
            )

    # ---------------------------------------------------------
    # CONTENT AREA
    # ---------------------------------------------------------

        content = tk.Frame(
            body,
            bg=BACKGROUND
        )
        content.pack(
            fill="x",

        )

        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=0)

    # ---------------------------------------------------------
    # LEFT CARD
    # ---------------------------------------------------------

        left_card = tk.Frame(
            content,
            bg=WHITE,
            highlightbackground="#D7E4FA",
            highlightthickness=1
        )
        left_card.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 8)
        )

        left_inner = tk.Frame(
            left_card,
            bg=WHITE
        )
        left_inner.pack(
            fill="x",
            padx=28,
            pady=25
        )

    # Issue Description heading

        description_heading = tk.Frame(
            left_inner,
            bg=WHITE
        )
        description_heading.pack(
            fill="x"
        )

        tk.Label(
            description_heading,
            text="📄",
            bg=WHITE,
            fg=BLUE,
            font=("Segeo UI", 16)
        ).pack(
            side="left",
            padx=(0, 8)
        )

        tk.Label(
            description_heading,
            text="Issue Description",
            bg=WHITE,
            fg="#173F73",
            font=("Segoe UI", 11, "bold")
        ).pack(
            side="left"
        )

    # Description display

        tk.Label(
            left_inner,
            text=ticket_description,
            bg="#F7FAFF",
            fg=TEXT,
            font=("Segeo UI", 10),
            justify="left",
            anchor="nw",
            wraplength=650
        ).pack(
            fill="x",
            pady=(10, 25),
            ipadx=12,
            ipady=14
        )

        # Resolution heading

        resolution_heading = tk.Frame(
            left_inner,
            bg=WHITE
        )
        resolution_heading.pack(
            fill="x"
        )

        tk.Label(
            resolution_heading,
            text="✎",
            bg=WHITE,
            fg=BLUE,
            font=("Segeo UI", 16)
        ).pack(
            side="left",
            padx=(0, 8)
        )

        tk.Label(
            resolution_heading,
            text="Resolution Note (required for RESOLVED)",
            bg=WHITE,
            fg="#173F73",
            font=("Segeo UI", 11, "bold")
        ).pack(
            side="left"
        )

        # Resolution input

        resolution_entry = tk.Text(
            left_inner,
            height=5,
            wrap="word",
            font=("Segeo UI", 10),
            bg=WHITE,
            fg=TEXT,
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground="#C9DCF8",
            highlightcolor=BLUE
        )

        resolution_entry.pack(
            fill="x",
            pady=(10, 5)
        )

        resolution_placeholder = (
            "Add your resolution note here..."
        )

        resolution_entry.insert(
            "1.0",
            resolution_placeholder
        )

        resolution_entry.config(
            fg="#8A9AB8"
        )

        def clear_resolution_placeholder(event=None):

            if resolution_entry.get("1.0", tk.END).strip() == resolution_placeholder:
                resolution_entry.delete("1.0", tk.END)
                resolution_entry.config(
                    fg=TEXT
                )

        resolution_entry.bind(
            "<FocusIn>",
            clear_resolution_placeholder
        )

        # ---------------------------------------------------------
# RESOLUTION SUMMARY
# ---------------------------------------------------------

        summary_heading = tk.Frame(
            left_inner,
            bg=WHITE
        )
        summary_heading.pack(
            fill="x",
            pady=(20, 0)
        )

        tk.Label(
            summary_heading,
            text="⏱",
            bg=WHITE,
            fg="#3B82F6",
            font=("Segeo UI", 16)
        ).pack(
            side="left",
            padx=(0, 8)
        )

        tk.Label(
            summary_heading,
            text="Resolution Summary",
            bg=WHITE,
            fg="#173F73",
            font=("Segeo UI", 11, "bold")
        ).pack(
            side="left"
        )

        summary_box = tk.Frame(
            left_inner,
            bg="#F7FAFF",
            highlightbackground="#D7E4FA"
        )
        summary_box.pack(
            fill="x",
            pady=(10, 0),
            ipady=5
        )

# Calculate resolution time
        if resolved_at and created_at:

            resolution_seconds = int(
                (resolved_at - created_at).total_seconds()
            )

            hours = resolution_seconds // 3600
            minutes = (resolution_seconds % 3600) // 60

            if hours > 0:
                resolution_time = f"{hours} hr {minutes} min"
            else:
                resolution_time = f"{minutes} min"

            resolved_display = resolved_at.strftime(
                "%d-%m-%Y %H:%M"
            )

        else:

            resolved_display = "Not resolved yet"
            resolution_time = "Will be calculated after resolution"

        summary_items = [
            ("Created", created_at.strftime("%d-%m-%Y %H:%M")),
            ("Resolved", resolved_display),
            ("Time Taken", resolution_time)
        ]

        for label, value in summary_items:

            row = tk.Frame(
                summary_box,
                bg="#F7FAFF"
            )
            row.pack(
                fill="x",
                padx=15,
                pady=5
            )

            tk.Label(
                row,
                text=label,
                bg="#F4F8FF",
                fg="#6076A4",
                font=("Segeo UI", 9, "bold"),
                width=15,
                anchor="w"
            ).pack(
                side="left"
            )

            tk.Label(
                row,
                text=value,
                bg="#F4F8FF",
                fg="#173F73",
                font=("Segeo UI", 9),
                anchor="w"
            ).pack(
                side="left"
            )

    # ---------------------------------------------------------
    # RIGHT CARD
    # ---------------------------------------------------------

        right_card = tk.Frame(
            content,
            bg=WHITE,
            highlightbackground="#D7E4FA",
            highlightthickness=1
        )
        right_card.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(8, 0)
        )

        right_inner = tk.Frame(
            right_card,
            bg=WHITE
        )
        right_inner.pack(
            fill="x",
            padx=20,
            pady=25
        )

    # Update Status heading

        tk.Label(
            right_inner,
            text="🔄  Update Status",
            bg=WHITE,
            fg="#173F73",
            font=("Segeo UI", 12, "bold")
        ).pack(
            anchor="w",
            pady=(0, 22)
        )

        tk.Label(
            right_inner,
            text="New Status",
            bg=WHITE,
            fg="#6076A4",
            font=("Segeo", 9, "bold")
        ).pack(
            anchor="w",
            pady=(0, 7)
        )

        status_var = tk.StringVar(
            value=allowed_statuses[0]
        )

        status_entry = ttk.Combobox(
            right_inner,
            textvariable=status_var,
            values=allowed_statuses,
            state="readonly",
            font=("Segeo UI", 10)
        )

        status_entry.pack(
            fill="x",
            ipady=6,
            pady=(0, 25)
        )

    # ---------------------------------------------------------
    # STATUS FLOW
    # ---------------------------------------------------------

        tk.Label(
            right_inner,
            text="Status Flow",
            bg=WHITE,
            fg="#6076A4",
            font=("Segeo UI", 9, "bold")
        ).pack(
            anchor="w",
            pady=(0, 15)
        )

        status_flow = tk.Frame(
            right_inner,
            bg=WHITE
        )
        status_flow.pack(
            fill="x"
        )

        flow_statuses = [
            "OPEN",
            "ASSIGNED",
            "IN PROGRESS",
            "RESOLVED"
        ]

        for index, flow_status in enumerate(flow_statuses):

            flow_item = tk.Frame(
                status_flow,
                bg=WHITE
            )
            flow_item.grid(
                row=0,
                column=index * 2,
                sticky="n"
            )

            status_flow.columnconfigure(
                index * 2,
                weight=1
            )
            status_order = {
                "OPEN": 0,
                "ASSIGNED": 1,
                "IN PROGRESS": 2,
                "RESOLVED": 3
            }
            current_index = status_order.get(
                current_status,
                0
            )
            flow_index = status_order[flow_status]

            if flow_index < current_index:
                circle_bg = "#DCFCE7"
                circle_fg = "#159447"
                circle_text = "✓"

            elif flow_index == current_index:
                circle_bg = "#FFF1C7"
                circle_fg = "#D88A00"
                circle_text = "●"

            else:
                circle_bg = "#EEF2F7"
                circle_fg = "#8A9AB8"
                circle_text = "●"

            tk.Label(
                flow_item,
                text=circle_text,
                bg=circle_bg,
                fg=circle_fg,
                font=("Segeo UI", 12, "bold"),
                width=2
            ).pack()

            tk.Label(
                flow_item,
                text=flow_status,
                bg=WHITE,
                fg=(
                    "#D88A00"
                    if flow_index == current_index
                    else "#6076A4"
                ),
                font=("Segeo UI", 8, "bold")
            ).pack(
                pady=(5, 0)
            )

    # Arrow between statuses
            if index < len(flow_statuses) - 1:

                tk.Label(
                    status_flow,
                    text="→",
                    bg=WHITE,
                    fg="#9DB1D1",
                    font=("Segeo UI", 14, "bold")
                ).grid(
                    row=0,
                    column=index * 2 + 1,
                    padx=2,
                    pady=(3, 0)
                )

    # ---------------------------------------------------------
    # STATUS MESSAGE
    # ---------------------------------------------------------

        status_message = tk.Label(
            right_inner,
            text=(
                "This ticket will move to "
                f"{allowed_statuses[0]}."
            ),
            bg="#F4F8FF",
            fg="#315A96",
            font=("Segeo UI", 9,"bold"),
            wraplength=260,
            justify="left",
            anchor="w"
        )

        status_message.pack(
            fill="x",
            pady=(25, 20),
            ipadx=10,
            ipady=10
        )

        # ---------------------------------------------------------
        # BUTTONS
        # ---------------------------------------------------------

        button_frame = tk.Frame(
            right_inner,
            bg=WHITE
        )
        button_frame.pack(
            side="bottom",
            fill="x"
        )

        def save_status():

            new_status = status_var.get()

            resolution_note = resolution_entry.get(
                "1.0",
                tk.END
            ).strip()

            if resolution_note == resolution_placeholder:
                resolution_note = ""

            # Strict workflow validation

            if (
                current_status == "ASSIGNED"
                and new_status != "IN PROGRESS"
            ):
                messagebox.showwarning(
                    "Invalid Status Change",
                    "An ASSIGNED ticket must be moved to IN PROGRESS first."
                )
                return

            if (
                current_status == "IN PROGRESS"
                and new_status != "RESOLVED"
            ):
                messagebox.showwarning(
                    "Invalid Status Change",
                    "An IN PROGRESS ticket can only be moved to RESOLVED."
                )
                return

            if (
                new_status == "RESOLVED"
                and not resolution_note
            ):
                messagebox.showwarning(
                    "Missing Resolution Note",
                    "Describe how the ticket was resolved."
                )
                return

            connection = get_connection()
            cursor = connection.cursor()

            # Re-check the database before updating.

            cursor.execute(
                """
                SELECT status, assigned_to, user_id
                FROM tickets
                WHERE id = %s
                """,
                (ticket_id,)
            )

            db_ticket = cursor.fetchone()

            if not db_ticket:

                cursor.close()
                connection.close()

                messagebox.showerror(
                    "Error",
                    "Ticket was not found."
                )
                return

            db_status, assigned_to, ticket_user_id = db_ticket

            if assigned_to != user[0]:

                cursor.close()
                connection.close()

                messagebox.showwarning(
                    "Access Denied",
                    "This ticket is not assigned to you."
                )
                return

            if db_status != current_status:

                cursor.close()
                connection.close()

                messagebox.showwarning(
                    "Ticket Changed",
                    "This ticket was updated elsewhere. "
                    "Refresh and try again."
                )
                return

            try:

                if (
                    db_status == "ASSIGNED"
                    and new_status == "IN PROGRESS"
                ):

                    cursor.execute(
                        """
                        UPDATE tickets
                        SET status = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                        AND assigned_to = %s
                        AND status = %s
                        """,
                        (
                            "IN PROGRESS",
                            ticket_id,
                            user[0],
                            "ASSIGNED"
                        )
                    )

                    action = "Work Started"
                    old_status = "ASSIGNED"
                    history_status = "IN PROGRESS"

                elif (
                    db_status == "IN PROGRESS"
                    and new_status == "RESOLVED"
                ):

                    cursor.execute(
                        """
                        UPDATE tickets
                        SET status = %s,
                            resolution_note = %s,
                            resolved_at = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                        AND assigned_to = %s
                        AND status = %s
                        """,
                        (
                            "RESOLVED",
                            resolution_note,
                            ticket_id,
                            user[0],
                            "IN PROGRESS"
                        )
                    )

                    action = "Ticket Resolved"
                    old_status = "IN PROGRESS"
                    history_status = "RESOLVED"

                else:

                    connection.rollback()
                    cursor.close()
                    connection.close()

                    messagebox.showwarning(
                        "Invalid Status Change",
                        "Invalid ticket status transition."
                    )
                    return

                updated = cursor.rowcount

                if updated != 1:

                    connection.rollback()

                    cursor.close()
                    connection.close()

                    messagebox.showwarning(
                        "Ticket Not Updated",
                        "The ticket status could not be updated. "
                        "Refresh and try again."
                    )
                    return

                add_ticket_history(
                    cursor,
                    ticket_id,
                    action,
                    user[0],
                    old_status,
                    history_status
                )

                if history_status == "RESOLVED":

                    add_notification(
                        cursor,
                        ticket_user_id,
                        ticket_id,
                        f"Ticket {ticket_id} has been resolved."
                    )

                connection.commit()

            except mysql.connector.Error:

                connection.rollback()

                messagebox.showerror(
                    "Database Error",
                    "Ticket status update could not be completed."
                )

                cursor.close()
                connection.close()

                return

            finally:

                try:
                    cursor.close()
                    connection.close()
                except:
                    pass

            if not updated:

                messagebox.showwarning(
                    "Ticket Not Updated",
                    "The ticket status could not be updated. "
                    "Refresh and try again."
                )
                return

            update_window.destroy()

            load_tickets()

            

            messagebox.showinfo(
                "Success",
                "Ticket status updated successfully."
            )

        add_button(
            button_frame,
            "✓  Update Ticket",
            save_status,
            18
        ).pack(
            fill="x",
            pady=(0, 8)
        )

        tk.Button(
            button_frame,
            text="✕  Cancel",
            command=update_window.destroy,
            bg=WHITE,
            fg="#315A96",
            activebackground="#F4F8FF",
            activeforeground="#173F73",
            relief="solid",
            bd=1,
            highlightthickness=0,
            font=("Segeo UI", 10, "bold"),
            cursor="hand2",
            pady=8
        ).pack(
            fill="x"
        )
    def view_history():
        selected = ticket_tree.selection()

        if not selected:
            messagebox.showwarning("No Ticket Selected", "Select a ticket first.")
            return

        ticket_id = ticket_tree.item(selected[0])["values"][0]
        show_ticket_history(support_window, ticket_id)

    actions = tk.Frame(support_window, bg=BACKGROUND)
    actions.pack(pady=(0, 16))
    add_button(actions, "Update Ticket Status", update_status, 24).grid(row=0, column=0, padx=4)
    add_button(actions, "View Ticket History", view_history, 20).grid(row=0, column=1, padx=4)

    load_tickets()

    ticket_tree.bind(
        "<Double-1>",
        show_ticket_details
    )
    

def create_ticket(user):
    ticket_window = open_in_app_dialog(1100, 700) if IN_APP_MODE else tk.Toplevel(window)
    if not IN_APP_MODE:
        setup_window(ticket_window, "Create Support Ticket", "1100x700")
        maximize_window(ticket_window)

    add_header(
        ticket_window,
        "Create Support Ticket",
        "Tell us what you need help with and we'll route it to the right support team.",
        closable=IN_APP_MODE
    )
    # Main content area
    body = tk.Frame(
        ticket_window,
        bg=BACKGROUND
    )
    body.pack(
        fill="both",
        expand=True,
        padx=55,
        pady=28
    )

    # Page heading
    tk.Label(
        body,
        text="Create a Support Ticket",
        bg=BACKGROUND,
        fg="#0B1F42",
        font=("Arial", 22, "bold")
    ).pack(
        anchor="w"
    )

    tk.Label(
        body,
        text="Tell us what went wrong and provide the details needed to resolve your issue.",
        bg=BACKGROUND,
        fg="#6076A4",
        font=("Arial", 10)
    ).pack(
        anchor="w",
        pady=(5, 20)
    )
        # Ticket form card
    card = tk.Frame(
        body,
        bg=WHITE,
        highlightbackground="#D7E4FA",
        highlightthickness=1
    )
    card.pack(
        fill="x",
        pady=(5, 0)
    )    # Card header
    card_header = tk.Frame(
        card,
        bg="#F3F7FF",
        height=62
    )
    card_header.pack(
        fill="x"
    )
    card_header.pack_propagate(False)

    tk.Label(
        card_header,
        text="ⓘ",
        bg="#F3F7FF",
        fg=BLUE,
        font=("Arial", 16, "bold")
    ).pack(
        side="left",
        padx=(25, 8)
    )

    tk.Label(
        card_header,
        text="Ticket Information",
        bg="#F3F7FF",
        fg="#0B1F42",
        font=("Arial", 12, "bold")
    ).pack(
        side="left"
    )


        # Ticket title
    tk.Label(
        card,
        text="Issue Title",
        bg=WHITE,
        fg="#0B1F42",
        font=("Arial", 10, "bold")
    ).pack(
        anchor="w",
        padx=30,
        pady=(25, 6)
    )

    title_entry = tk.Entry(
        card,
        font=("Arial", 11),
        bg="#F7FAFF",
        fg=TEXT,
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightbackground="#C9DCF8",
        highlightcolor=BLUE
    )
    title_entry.pack(
        fill="x",
        padx=30,
        ipady=9
    )
    title_placeholder = "Enter a clear and short title for your issue..."

    title_entry.insert(0, title_placeholder)
    title_entry.config(fg="#8A9ABB")

    def clear_title_placeholder(event):
        if title_entry.get() == title_placeholder:
            title_entry.delete(0, tk.END)
            title_entry.config(fg=TEXT)

    def restore_title_placeholder(event):
        if not title_entry.get().strip():
            title_entry.insert(0, title_placeholder)
            title_entry.config(fg="#8A9ABB")

    title_entry.bind("<FocusIn>", clear_title_placeholder)
    title_entry.bind("<FocusOut>", restore_title_placeholder)
    
        # Category and Priority
    fields_frame = tk.Frame(
        card,
        bg=WHITE
    )
    fields_frame.pack(
        fill="x",
        padx=30,
        pady=(18, 0)
    )

    # Category
    category_frame = tk.Frame(
        fields_frame,
        bg=WHITE
    )
    category_frame.pack(
        side="left",
        fill="x",
        expand=True,
        padx=(0, 8)
    )
    

    tk.Label(
        category_frame,
        text="Category",
        bg=WHITE,
        fg="#0B1F42",
        font=("Arial", 10, "bold")
    ).pack(
        anchor="w",
        pady=(0,6)
    )

    category_box = tk.Frame(
        category_frame,
        bg="#F7FAFF",
        highlightbackground="#C9DCF8",
        highlightthickness=1
    )
    category_box.pack(
        fill="x"
    )

    category_icon = tk.Label(
        category_box,
        text="⚙",
        bg="#F7FAFF",
        fg=BLUE,
        font=("Arial", 11)
    )
    category_icon.pack(
        side="left",
        padx=(10, 4)
    )

    category_entry = ttk.Combobox(
        category_box,
        values=[
            "Hardware",
            "Software",
            "Network",
            "Access",
            "Email",
            "Other"
        ],
        state="readonly",
        font=("Arial", 10)
    )
    category_entry.pack(
        side="left",
        fill="x",
        expand=True,
        ipady=6,
    )

    category_entry.set("Select Category")
    priority_frame = tk.Frame(
        fields_frame,
        bg=WHITE
    )
    priority_frame.pack(
        side="left",
        fill="x",
        expand=True,
        padx=(8, 0)
    )
    category_icons = {
        "Hardware": "💻",
        "Software": "🖥",
        "Network": "🌐",
        "Access": "🔑",
        "Email": "✉",
        "Other": "⚙"
    }

    def update_category_icon(event=None):
        selected = category_entry.get()
        category_icon.config(
            text=category_icons.get(selected, "⚙")
        )

    category_entry.bind(
        "<<ComboboxSelected>>",
        update_category_icon
    )

    # Priority
    tk.Label(
        priority_frame,
        text="Priority",
        bg=WHITE,
        fg="#0B1F42",
        font=("Arial", 10, "bold")
    ).pack(
        anchor="w",
        pady=(0, 6)
    )



    priority_box = tk.Frame(
        priority_frame,
        bg="#F7FAFF",
        highlightbackground="#C9DCF8",
        highlightthickness=1
    )
    priority_box.pack(
        fill="x"
    )

    priority_icon = tk.Label(
        priority_box,
        text="●",
        bg="#F7FAFF",
        fg="#EAB308",
        font=("Arial", 20, "bold")
    )
    priority_icon.pack(
        side="left",
        padx=(10, 6)
    )

    priority_entry = ttk.Combobox(
        priority_box,
        values=[
            "Low",
            "Medium",
            "High",
            "Critical"
        ],
        state="readonly",
        font=("Arial", 10)
    )
    priority_entry.pack(
        side="left",
        fill="x",
        expand=True,
        ipady=6,
    )

    priority_entry.set("Medium")
    priority_icons = {
        "Low": ("●", "#16A34A"),
        "Medium": ("●", "#EAB308"),
        "High": ("●", "#F97316"),
        "Critical": ("●", "#DC2626")
    }

    def update_priority_icon(event=None):
        selected = priority_entry.get()

        icon, icon_color = priority_icons.get(
            selected,
            ("●", "#EAB308")
        )

        priority_icon.config(
            text=icon,
            fg=icon_color
        )

    priority_entry.bind(
        "<<ComboboxSelected>>",
        update_priority_icon
    )
        
       # Description label row
    description_label_frame = tk.Frame(
        card,
        bg=WHITE
    )
    description_label_frame.pack(
        fill="x",
        padx=30,
        pady=(22, 6)
    )

    tk.Label(
        description_label_frame,
        text="Issue Description",
        bg=WHITE,
        fg="#334E75",
        font=("Segoe UI", 10)
    ).pack(
        side="left"
    )

    tk.Label(
        description_label_frame,
        text="Be as specific as possible",
        bg=WHITE,
        fg="#8A9ABB",
        font=("Arial", 9)
    ).pack(
        side="right"
    )

    description_entry = tk.Text(
        card,
        height=6,
        font=("Segoe UI", 10),
        bg="#F4F8FF",
        fg="#334E75",
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightbackground="#C9DCF8",
        highlightcolor=BLUE,
        wrap="word",
        padx=10,
        pady=8
    )
    description_entry.pack(
        fill="x",
        padx=30,
        pady=(0, 20)
    )
    description_placeholder = (
        "Describe what happened, when it started, "
        "and any error message you received..."
    )

    description_entry.insert("1.0", description_placeholder)
    description_entry.config(fg="#8A9ABB")

    def clear_description_placeholder(event):
        current_text = description_entry.get("1.0", tk.END).strip()

        if current_text == description_placeholder:
            description_entry.delete("1.0", tk.END)
            description_entry.config(fg=TEXT)

    def restore_description_placeholder(event):
        current_text = description_entry.get("1.0", tk.END).strip()

        if not current_text:
            description_entry.insert("1.0", description_placeholder)
            description_entry.config(fg="#8A9ABB")

    description_entry.bind("<FocusIn>", clear_description_placeholder)
    description_entry.bind("<FocusOut>", restore_description_placeholder)
    
    tk.Label(
        card,
        text="💡 Example: Explain what happened, when it started, and any error message you received.",
        bg=WHITE,
        fg="#6076A4",
        font=("Arial", 9)
    ).pack(
        anchor="w",
        padx=30,
        pady=(0, 12)
    )
        
    
    def submit_ticket():
        title = title_entry.get().strip()
        category = category_entry.get().strip()
        priority = priority_entry.get().strip()
        description = description_entry.get("1.0", tk.END).strip()
        if title == title_placeholder:
            title = ""

        if description == description_placeholder:
            description = ""
        if not all((title, category, priority, description)):
            messagebox.showwarning("Missing Information", "Fill in all ticket fields.")
            return
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT id FROM categories WHERE category_name = %s", (category,))
            category_result = cursor.fetchone()
            if not category_result:
                connection.rollback()
                messagebox.showerror("Error", "The selected category was not found.")
                return

            cursor.execute("""
                INSERT INTO tickets (user_id, category_id, title, description, priority, status, assigned_to)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user[0], category_result[0], title, description, priority, "OPEN", None))
            ticket_id = cursor.lastrowid

            add_ticket_history(
                cursor, ticket_id, "Ticket Created", user[0], None, "OPEN"
            )
            cursor.execute("SELECT id FROM users WHERE role = 'Admin'")
            admins = cursor.fetchall()

            for admin in admins:
                add_notification(
                    cursor,
                    admin[0],
                    ticket_id,
                    f"New ticket {ticket_id} has been created."
                )
            connection.commit()
        except mysql.connector.Error:
            connection.rollback()
            messagebox.showerror("Database Error", "Ticket could not be created.")
            return
        finally:
            cursor.close()
            connection.close()

        ticket_window.destroy()
        messagebox.showinfo("Ticket Created", f"Ticket {ticket_id} was created successfully.")
       # Bottom action area
    buttons = tk.Frame(
        card,
        bg=WHITE,
        height=65
    )
    buttons.pack(
        fill="x",
        side="bottom"
    )
    buttons.pack_propagate(False)

    # Back button
    tk.Button(
        buttons,
        text="Back to Dashboard",
        command=lambda: employee_dashboard(user),
        bg=WHITE,
        fg="#315A96",
        activebackground="#F1F6FF",
        activeforeground="#173F73",
        relief="solid",
        bd=1,
        highlightthickness=0,
        font=("Arial", 10, "bold"),
        cursor="hand2",
        padx=18,
        pady=7
    ).pack(
        side="left",
        padx=25,
        pady=12
    )

    # Submit button
    tk.Button(
        buttons,
        text="Submit Support Ticket",
        command=submit_ticket,
        bg=BLUE,
        fg=WHITE,
        activebackground="#2858C7",
        activeforeground=WHITE,
        relief="flat",
        bd=0,
        font=("Arial", 10, "bold"),
        cursor="hand2",
        padx=20,
        pady=8
    ).pack(
        side="right",
        padx=25,
        pady=12
    )

    title_entry.focus_set()

def show_reports(user):

    report_window = tk.Toplevel(window)
    setup_window(
        report_window,
        "Reports & Analytics",
        "1100x850"
    )
    maximize_window(report_window)

    # -------------------------------------------------
    # HEADER
    # -------------------------------------------------

    add_header(
        report_window,
        "Reports & Analytics",
        "Live ticket analysis and support statistics",
        closable=True
    )

    # -------------------------------------------------
    # REPORT ACTIONS
    # -------------------------------------------------

    report_action_frame = tk.Frame(
        report_window,
        bg=BACKGROUND
    )

    report_action_frame.pack(
        fill="x",
        padx=25,
        pady=(10, 5)
    )

    sla_reports_button = add_button(
        report_action_frame,
        "SLA Reports",
        lambda: show_sla_reports(),
        11
    )

    sla_reports_button.pack(
        side="right"
    )

    sla_reports_button.config(
        width=16
    )

    # -------------------------------------------------
    # FILTER VARIABLES
    # -------------------------------------------------

    status_var = tk.StringVar(value="All")
    employee_var = tk.StringVar(value="All Employees")
    category_var = tk.StringVar(value="All Categories")
    priority_var = tk.StringVar(value="All Priorities")

    month_var = tk.StringVar(value="All Months")
    from_date_var = tk.StringVar()
    to_date_var = tk.StringVar()

    employee_lookup = {}

    # -------------------------------------------------
    # FILTER FRAME
    # -------------------------------------------------

    filter_card = tk.Frame(
        report_window,
        bg=WHITE,
        highlightbackground="#D7E4FA",
        highlightthickness=1
    )
    filter_card.pack(
        fill="x",
        padx=25,
        pady=(15, 10)
    )

    filter_frame = tk.Frame(
        filter_card,
        bg=WHITE
    )
    filter_frame.pack(
        fill="x",
        padx=15,
        pady=12
    )

    # STATUS

    tk.Label(
        filter_frame,
        text="Status",
        bg=WHITE,
        fg=NAVY,
        font=("Arial", 9, "bold")
    ).pack(side="left", padx=(0, 5))

    status_filter = ttk.Combobox(
        filter_frame,
        textvariable=status_var,
        values=[
            "All",
            "OPEN",
            "ASSIGNED",
            "IN PROGRESS",
            "RESOLVED",
            "CLOSED",
            "REOPENED"
        ],
        state="readonly",
        width=15
    )
    status_filter.pack(side="left", padx=(0, 15))

    # EMPLOYEE

    tk.Label(
        filter_frame,
        text="Employee",
        bg=WHITE,
        fg=NAVY,
        font=("Arial", 9, "bold")
    ).pack(side="left", padx=(0, 5))

    employee_filter = ttk.Combobox(
        filter_frame,
        textvariable=employee_var,
        state="readonly",
        width=20
    )
    employee_filter.pack(side="left", padx=(0, 15))

    # CATEGORY

    tk.Label(
        filter_frame,
        text="Category",
        bg=WHITE,
        fg=NAVY,
        font=("Arial", 9, "bold")
    ).pack(side="left", padx=(0, 5))

    category_filter = ttk.Combobox(
        filter_frame,
        textvariable=category_var,
        values=[
            "All Categories",
            "Hardware",
            "Software",
            "Network",
            "Access",
            "Email",
            "Other"
        ],
        state="readonly",
        width=18
    )
    category_filter.pack(side="left", padx=(0, 15))

    # PRIORITY

    tk.Label(
        filter_frame,
        text="Priority",
        bg=WHITE,
        fg=NAVY,
        font=("Arial", 9, "bold")
    ).pack(side="left", padx=(0, 5))

    priority_filter = ttk.Combobox(
        filter_frame,
        textvariable=priority_var,
        values=[
            "All Priorities",
            "Low",
            "Medium",
            "High",
            "Critical"
        ],
        state="readonly",
        width=16
    )
    priority_filter.pack(side="left", padx=(0, 15))

    # -------------------------------------------------
    # DATE FILTERS
    # -------------------------------------------------

    date_filter_frame = tk.Frame(
        filter_card,
        bg=WHITE
    )

    date_filter_frame.pack(
        fill="x",
        padx=15,
        pady=(0, 12)
    )

    # MONTH

    tk.Label(
        date_filter_frame,
        text="Month",
        bg=WHITE,
        fg=NAVY,
        font=("Arial", 9, "bold")
    ).pack(side="left", padx=(0, 5))

    month_filter = ttk.Combobox(
        date_filter_frame,
        textvariable=month_var,
        values=[
            "All Months",
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December"
        ],
        state="readonly",
        width=15
    )

    month_filter.pack(
        side="left",
        padx=(0, 15)
    )

    # FROM DATE

    tk.Label(
        date_filter_frame,
        text="From Date",
        bg=WHITE,
        fg=NAVY,
        font=("Arial", 9, "bold")
    ).pack(side="left", padx=(0, 5))

    from_date_entry = tk.Entry(
        date_filter_frame,
        textvariable=from_date_var,
        width=13,
        font=("Arial", 9)
    )

    from_date_entry.pack(
        side="left",
        padx=(0, 15),
        ipady=3
    )

    # TO DATE

    tk.Label(
        date_filter_frame,
        text="To Date",
        bg=WHITE,
        fg=NAVY,
        font=("Arial", 9, "bold")
    ).pack(side="left", padx=(0, 5))

    to_date_entry = tk.Entry(
        date_filter_frame,
        textvariable=to_date_var,
        width=13,
        font=("Arial", 9)
    )

    to_date_entry.pack(
        side="left",
        padx=(0, 15),
        ipady=3
    )

    # APPLY

    apply_date_button = add_button(
        date_filter_frame,
        "Apply",
        lambda: load_report_data(),
        10
    )

    apply_date_button.pack(
        side="left",
        padx=3
    )

    # CLEAR

    clear_date_button = add_button(
        date_filter_frame,
        "Clear",
        lambda: clear_date_filters(),
        10,
        True
    )

    clear_date_button.pack(
        side="left",
        padx=3
    )

    tk.Label(
        date_filter_frame,
        text="Format: YYYY-MM-DD",
        bg=WHITE,
        fg="#6076A4",
        font=("Arial", 8)
    ).pack(
        side="left",
        padx=(10, 0)
    )

    # -------------------------------------------------
    # SUMMARY CARDS
    # -------------------------------------------------

    summary_frame = tk.Frame(
        report_window,
        bg=BACKGROUND
    )
    summary_frame.pack(
        fill="x",
        padx=25,
        pady=(0, 10)
    )

    summary_vars = {
        "Total": tk.StringVar(value="0"),
        "OPEN": tk.StringVar(value="0"),
        "ASSIGNED": tk.StringVar(value="0"),
        "IN PROGRESS": tk.StringVar(value="0"),
        "RESOLVED": tk.StringVar(value="0"),
        "CLOSED": tk.StringVar(value="0"),
        "REOPENED": tk.StringVar(value="0")
    }

    summary_colors = {
        "Total": "#FFFFFF",
        "OPEN": "#FFF8D8",
        "ASSIGNED": "#EEF2FF",
        "IN PROGRESS": "#E8F4FF",
        "RESOLVED": "#E8F8EE",
        "CLOSED": "#E8F8EE",
        "REOPENED": "#FFE8E8"
    }

    for status, variable in summary_vars.items():

        card = tk.Frame(
            summary_frame,
            bg=summary_colors[status],
            highlightbackground="#D7E4FA",
            highlightthickness=1
        )

        card.pack(
            side="left",
            fill="x",
            expand=True,
            padx=4
        )

        tk.Label(
            card,
            text=status,
            bg=summary_colors[status],
            fg="#6076A4",
            font=("Arial", 9, "bold")
        ).pack(
            pady=(8, 2)
        )

        tk.Label(
            card,
            textvariable=variable,
            bg=summary_colors[status],
            fg=NAVY,
            font=("Arial", 18, "bold")
        ).pack(
            pady=(0, 8)
        )


    # -------------------------------------------------
    # CHART AREA
    # -------------------------------------------------

    chart_container = tk.Frame(
        report_window,
        bg=BACKGROUND
    )
    chart_container.pack(
        fill="both",
        expand=True,
        padx=25,
        pady=(0, 15)
    )

   # TOP ROW

    top_chart_frame = tk.Frame(
        chart_container,
        bg=BACKGROUND,
        height=230
    )

    top_chart_frame.pack(
        fill="x",
        pady=(0, 8)
    )

    top_chart_frame.pack_propagate(False)


    # BOTTOM ROW

    bottom_chart_frame = tk.Frame(
        chart_container,
        bg=BACKGROUND,
        height=230
    )

    bottom_chart_frame.pack(
        fill="x"
    )

    bottom_chart_frame.pack_propagate(False)

    # -------------------------------------------------
    # CHART 1 - STATUS
    # -------------------------------------------------

    status_card = tk.Frame(
        top_chart_frame,
        bg=WHITE,
        highlightbackground="#D7E4FA",
        highlightthickness=1
    )

    status_card.pack(
        side="left",
        fill="both",
        expand=True,
        padx=(0, 5)
    )

    tk.Label(
        status_card,
        text="Tickets by Status",
        bg=WHITE,
        fg=NAVY,
        font=("Arial", 11, "bold")
    ).pack(
        anchor="w",
        padx=12,
        pady=(10, 0)
    )

    status_canvas = tk.Canvas(
        status_card,
        bg=WHITE,
        highlightthickness=0
    )
    status_canvas.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=8
    )

    # -------------------------------------------------
    # CHART 2 - CATEGORY
    # -------------------------------------------------

    category_card = tk.Frame(
        top_chart_frame,
        bg=WHITE,
        highlightbackground="#D7E4FA",
        highlightthickness=1
    )

    category_card.pack(
        side="left",
        fill="both",
        expand=True,
        padx=(5, 0)
    )

    tk.Label(
        category_card,
        text="Tickets by Category",
        bg=WHITE,
        fg=NAVY,
        font=("Arial", 11, "bold")
    ).pack(
        anchor="w",
        padx=12,
        pady=(10, 0)
    )

    category_canvas = tk.Canvas(
        category_card,
        bg=WHITE,
        highlightthickness=0
    )
    category_canvas.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=8
    )

    # -------------------------------------------------
    # CHART 3 - PRIORITY
    # -------------------------------------------------

    priority_card = tk.Frame(
        bottom_chart_frame,
        bg=WHITE,
        highlightbackground="#D7E4FA",
        highlightthickness=1
    )

    priority_card.pack(
        side="left",
        fill="both",
        expand=True,
        padx=(0, 5)
    )

    tk.Label(
        priority_card,
        text="Tickets by Priority",
        bg=WHITE,
        fg=NAVY,
        font=("Arial", 11, "bold")
    ).pack(
        anchor="w",
        padx=12,
        pady=(10, 0)
    )

    priority_canvas = tk.Canvas(
        priority_card,
        bg=WHITE,
        highlightthickness=0
    )
    priority_canvas.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=8
    )

    # -------------------------------------------------
    # CHART 4 - EMPLOYEE
    # -------------------------------------------------

    employee_card = tk.Frame(
        bottom_chart_frame,
        bg=WHITE,
        highlightbackground="#D7E4FA",
        highlightthickness=1
    )

    employee_card.pack(
        side="left",
        fill="both",
        expand=True,
        padx=(5, 0)
    )

    tk.Label(
        employee_card,
        text="Employee-wise Tickets",
        bg=WHITE,
        fg=NAVY,
        font=("Arial", 11, "bold")
    ).pack(
        anchor="w",
        padx=12,
        pady=(10, 0)
    )

    employee_canvas = tk.Canvas(
        employee_card,
        bg=WHITE,
        highlightthickness=0
    )
    employee_canvas.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=8
    )

        # -------------------------------------------------
    # DRAW BAR CHART
    # -------------------------------------------------

    def draw_vertical_chart(canvas, labels, values):

        canvas.delete("all")

        width = canvas.winfo_width()
        height = canvas.winfo_height()

        if width < 100:
            width = 450

        if height < 100:
            height = 220

        if not labels:
            canvas.create_text(
                width / 2,
                height / 2,
                text="No data available",
                fill="#6076A4",
                font=("Arial", 11)
            )
            return

        max_value = max(values) if values else 1

        left = 45
        right = width - 20
        top = 20
        bottom = height - 40

        chart_width = right - left
        chart_height = bottom - top

        count = len(labels)

        bar_width = chart_width / count * 0.55

        for index, (label, value) in enumerate(
            zip(labels, values)
        ):

            x_center = (
                left
                + (index + 0.5)
                * (chart_width / count)
            )

            bar_height = (
                value / max_value
                * chart_height
                if max_value
                else 0
            )

            x1 = x_center - bar_width / 2
            x2 = x_center + bar_width / 2

            y1 = bottom - bar_height
            y2 = bottom

            canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill="#2F80ED",
                outline=""
            )

            canvas.create_text(
                x_center,
                y1 - 10,
                text=str(value),
                fill=NAVY,
                font=("Arial", 9, "bold")
            )

            canvas.create_text(
                x_center,
                bottom + 15,
                text=str(label),
                fill="#6076A4",
                font=("Arial", 8)
            )

        canvas.create_line(
            left,
            bottom,
            right,
            bottom,
            fill="#B8C7E0"
        )


    # -------------------------------------------------
    # DRAW HORIZONTAL CHART
    # -------------------------------------------------

    def draw_horizontal_chart(canvas, labels, values):

        canvas.delete("all")

        width = canvas.winfo_width()
        height = canvas.winfo_height()

        if width < 100:
            width = 450

        if height < 100:
            height = 220

        if not labels:
            canvas.create_text(
                width / 2,
                height / 2,
                text="No data available",
                fill="#6076A4",
                font=("Arial", 11)
            )
            return

        max_value = max(values) if values else 1

        left = 100
        right = width - 25
        top = 20
        bottom = height - 20

        chart_width = right - left
        chart_height = bottom - top

        count = len(labels)

        row_height = chart_height / count
        bar_height = row_height * 0.45

        for index, (label, value) in enumerate(
            zip(labels, values)
        ):

            y_center = (
                top
                + (index + 0.5)
                * row_height
            )

            bar_width = (
                value / max_value
                * chart_width
                if max_value
                else 0
            )

            x1 = left
            x2 = left + bar_width

            y1 = y_center - bar_height / 2
            y2 = y_center + bar_height / 2

            canvas.create_text(
                left - 8,
                y_center,
                text=str(label),
                fill="#6076A4",
                font=("Arial", 8),
                anchor="e"
            )

            canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill="#2F80ED",
                outline=""
            )

            canvas.create_text(
                x2 + 8,
                y_center,
                text=str(value),
                fill=NAVY,
                font=("Arial", 9, "bold"),
                anchor="w"
            )


    # -------------------------------------------------
    # LOAD REPORT DATA
    # -------------------------------------------------

    def clear_date_filters():
    
        month_var.set("All Months")
        from_date_var.set("")
        to_date_var.set("")

        load_report_data()
    
    def load_report_data(event=None):

        connection = get_connection()
        cursor = connection.cursor()

        conditions = []
        params = []

        # STATUS FILTER

        if status_var.get() != "All":

            conditions.append(
                "tickets.status = %s"
            )

            params.append(
                status_var.get()
            )

        # EMPLOYEE FILTER

        if employee_var.get() != "All Employees":

            conditions.append(
                "users.name = %s"
            )

            params.append(
                employee_var.get()
            )

        # CATEGORY FILTER

        if category_var.get() != "All Categories":

            conditions.append(
                "categories.category_name = %s"
            )

            params.append(
                category_var.get()
            )

        # PRIORITY FILTER

        if priority_var.get() != "All Priorities":

            conditions.append(
                "tickets.priority = %s"
            )

            params.append(
                priority_var.get()
            )

                # MONTH FILTER

        if month_var.get() != "All Months":

            month_number = [
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December"
            ].index(month_var.get()) + 1

            conditions.append(
                "MONTH(tickets.created_at) = %s"
            )

            params.append(
                month_number
            )

        # FROM DATE FILTER

        from_date = from_date_var.get().strip()

        if from_date:

            try:
                datetime.strptime(
                    from_date,
                    "%Y-%m-%d"
                )
            except ValueError:
                messagebox.showwarning(
                    "Invalid Date",
                    "From Date must be in YYYY-MM-DD format.",
                    parent=report_window
                )
                return

            conditions.append(
                "DATE(tickets.created_at) >= %s"
            )

            params.append(
                from_date
            )

        # TO DATE FILTER

        to_date = to_date_var.get().strip()

        if to_date:

            try:
                datetime.strptime(
                    to_date,
                    "%Y-%m-%d"
                )
            except ValueError:
                messagebox.showwarning(
                    "Invalid Date",
                    "To Date must be in YYYY-MM-DD format.",
                    parent=report_window
                )
                return

            conditions.append(
                "DATE(tickets.created_at) <= %s"
            )

            params.append(
                to_date
            )

        # DATE RANGE VALIDATION

        if from_date and to_date:

            if from_date > to_date:

                messagebox.showwarning(
                    "Invalid Date Range",
                    "From Date cannot be later than To Date.",
                    parent=report_window
                )

                return

        if conditions:

            where_clause = (
                "WHERE "
                + " AND ".join(conditions)
            )

        else:

            where_clause = ""

        # -------------------------------------------------
        # SUMMARY
        # -------------------------------------------------

        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM tickets
            LEFT JOIN users
                ON tickets.user_id = users.id
            LEFT JOIN categories
                ON tickets.category_id = categories.id
            {where_clause}
            """,
            tuple(params)
        )

        total = cursor.fetchone()[0]

        summary_vars["Total"].set(str(total))

        for status in (
            "OPEN",
            "ASSIGNED",
            "IN PROGRESS",
            "RESOLVED",
            "CLOSED",
            "REOPENED"
        ):

            status_conditions = list(conditions)
            status_params = list(params)

            status_conditions.append(
                "tickets.status = %s"
            )

            status_params.append(status)

            status_where = (
                "WHERE "
                + " AND ".join(status_conditions)
            )

            cursor.execute(
                f"""
                SELECT COUNT(*)
                FROM tickets
                LEFT JOIN users
                    ON tickets.user_id = users.id
                LEFT JOIN categories
                    ON tickets.category_id = categories.id
                {status_where}
                """,
                tuple(status_params)
            )

            count = cursor.fetchone()[0]

            summary_vars[status].set(str(count))

        # -------------------------------------------------
        # STATUS CHART
        # -------------------------------------------------

        cursor.execute(
            f"""
            SELECT tickets.status, COUNT(*)
            FROM tickets
            LEFT JOIN users
                ON tickets.user_id = users.id
            LEFT JOIN categories
                ON tickets.category_id = categories.id
            {where_clause}
            GROUP BY tickets.status
            """,
            tuple(params)
        )

        status_data = cursor.fetchall()

        status_order = [
            "OPEN",
            "ASSIGNED",
            "IN PROGRESS",
            "RESOLVED",
            "CLOSED",
            "REOPENED"
        ]

        status_dict = {
            status: 0
            for status in status_order
        }

        for status, count in status_data:

            if status in status_dict:
                status_dict[status] = count

        draw_vertical_chart(
            status_canvas,
            status_order,
            [
                status_dict[status]
                for status in status_order
            ]
        )

        # -------------------------------------------------
        # CATEGORY CHART
        # -------------------------------------------------

        cursor.execute(
            f"""
            SELECT categories.category_name, COUNT(*)
            FROM tickets
            LEFT JOIN users
                ON tickets.user_id = users.id
            LEFT JOIN categories
                ON tickets.category_id = categories.id
            {where_clause}
            GROUP BY categories.category_name
            """,
            tuple(params)
        )

        category_data = cursor.fetchall()

        category_labels = []
        category_values = []

        category_order = [
            "Hardware",
            "Software",
            "Network",
            "Access",
            "Email",
            "Other"
        ]

        category_dict = {
            category: 0
            for category in category_order
        }

        for category, count in category_data:

            if category in category_dict:
                category_dict[category] = count

        for category in category_order:

            if category_dict[category] > 0:

                category_labels.append(category)
                category_values.append(
                    category_dict[category]
                )

        draw_vertical_chart(
            category_canvas,
            category_labels,
            category_values
        )

        # -------------------------------------------------
        # PRIORITY CHART
        # -------------------------------------------------

        cursor.execute(
            f"""
            SELECT tickets.priority, COUNT(*)
            FROM tickets
            LEFT JOIN users
                ON tickets.user_id = users.id
            LEFT JOIN categories
                ON tickets.category_id = categories.id
            {where_clause}
            GROUP BY tickets.priority
            """,
            tuple(params)
        )

        priority_data = cursor.fetchall()

        priority_order = [
            "Critical",
            "High",
            "Medium",
            "Low"
        ]

        priority_dict = {
            priority: 0
            for priority in priority_order
        }

        for priority, count in priority_data:

            if priority in priority_dict:
                priority_dict[priority] = count

        priority_labels = []
        priority_values = []

        for priority in priority_order:

            if priority_dict[priority] > 0:

                priority_labels.append(priority)
                priority_values.append(
                    priority_dict[priority]
                )

        draw_horizontal_chart(
            priority_canvas,
            priority_labels,
            priority_values
        )

        # -------------------------------------------------
        # EMPLOYEE-WISE CHART
        # -------------------------------------------------

        cursor.execute(
            f"""
            SELECT users.name, COUNT(*)
            FROM tickets
            LEFT JOIN users
                ON tickets.user_id = users.id
            LEFT JOIN categories
                ON tickets.category_id = categories.id
            {where_clause}
            GROUP BY users.name
            ORDER BY COUNT(*) DESC
            """,
            tuple(params)
        )

        employee_data = cursor.fetchall()

        employee_labels = []
        employee_values = []

        for employee_name, count in employee_data:

            if employee_name:

                employee_labels.append(
                    employee_name
                )

                employee_values.append(count)

        draw_horizontal_chart(
            employee_canvas,
            employee_labels,
            employee_values
        )

        cursor.close()
        connection.close()


    # -------------------------------------------------
    # LOAD EMPLOYEES INTO FILTER
    # -------------------------------------------------

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT name
        FROM users
        WHERE role = 'Employee'
        ORDER BY name
        """
    )

    employee_values = [
        "All Employees"
    ]

    for (employee_name,) in cursor.fetchall():

        employee_values.append(
            employee_name
        )

    employee_filter["values"] = employee_values

    cursor.close()
    connection.close()


    # -------------------------------------------------
    # FILTER EVENTS
    # -------------------------------------------------

    status_filter.bind(
        "<<ComboboxSelected>>",
        load_report_data
    )

    employee_filter.bind(
        "<<ComboboxSelected>>",
        load_report_data
    )

    category_filter.bind(
        "<<ComboboxSelected>>",
        load_report_data
    )

    priority_filter.bind(
        "<<ComboboxSelected>>",
        load_report_data
    )


    # -------------------------------------------------
    # REDRAW CHARTS WHEN WINDOW SIZE CHANGES
    # -------------------------------------------------

    def redraw_charts(event=None):

        load_report_data()

    report_window.bind(
        "<Configure>",
        redraw_charts
    )


    # -------------------------------------------------
    # FIRST LOAD
    # -------------------------------------------------

    report_window.after(
        200,
        load_report_data
    )

def show_sla_reports():

    sla_window = tk.Toplevel(window)

    setup_window(
        sla_window,
        "SLA Reports & Analytics",
        "1100x750"
    )

    maximize_window(sla_window)

    add_header(
        sla_window,
        "SLA Reports & Analytics",
        "Detailed SLA performance and compliance analysis",
        closable=True
    )

    # -------------------------------------------------
    # SLA SUMMARY
    # -------------------------------------------------

    summary_frame = tk.Frame(
        sla_window,
        bg=BACKGROUND
    )

    summary_frame.pack(
        fill="x",
        padx=25,
        pady=20
    )

    sla_vars = {
        "SLA Met": tk.StringVar(value="0"),
        "Within SLA": tk.StringVar(value="0"),
        "Due Soon": tk.StringVar(value="0"),
        "SLA Breached": tk.StringVar(value="0"),
        "SLA Compliance": tk.StringVar(value="0%")
    }

    sla_colors = {
        "SLA Met": "#E8F8EE",
        "Within SLA": "#E8F4FF",
        "Due Soon": "#FFF4D6",
        "SLA Breached": "#FFE8E8",
        "SLA Compliance": "#EEF2FF"
    }

    for label, variable in sla_vars.items():

        card = tk.Frame(
            summary_frame,
            bg=sla_colors[label],
            highlightbackground="#D7E4FA",
            highlightthickness=1
        )

        card.pack(
            side="left",
            fill="x",
            expand=True,
            padx=4
        )

        tk.Label(
            card,
            text=label,
            bg=sla_colors[label],
            fg="#6076A4",
            font=("Arial", 9, "bold")
        ).pack(
            pady=(12, 3)
        )

        tk.Label(
            card,
            textvariable=variable,
            bg=sla_colors[label],
            fg=NAVY,
            font=("Arial", 18, "bold")
        ).pack(
            pady=(0, 12)
        )

    # -------------------------------------------------
    # DETAILED SLA REPORT
    # -------------------------------------------------

    table_card = tk.Frame(
        sla_window,
        bg=WHITE,
        highlightbackground="#D7E4FA",
        highlightthickness=1
    )
    table_card.pack(
        fill="both",
        expand=True,
        padx=30,
        pady=(15, 20)
    )

    tk.Label(
        table_card,
        text="Detailed SLA Report",
        bg=WHITE,
        fg=NAVY,
        font=("Arial", 12, "bold")
    ).pack(
        anchor="w",
        padx=18,
        pady=(12, 2)
    )

    tk.Label(
        table_card,
        text="Ticket-wise SLA performance and compliance status",
        bg=WHITE,
        fg="#6076A4",
        font=("Arial", 9)
    ).pack(
        anchor="w",
        padx=18,
        pady=(0, 10)
    )

    table_frame = tk.Frame(
        table_card,
        bg=WHITE
    )
    table_frame.pack(
        fill="both",
        expand=True,
        padx=15,
        pady=(0, 15)
    )

    columns = (
        "Ticket ID",
        "Employee",
        "Priority",
        "SLA Limit",
        "Created At",
        "Resolved At",
        "Elapsed Time",
        "SLA Status"
    )

    sla_tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings"
    )

    configure_tree(sla_tree)

    sla_tree.tag_configure("sla_met", background="#E8F8EE")
    sla_tree.tag_configure("within_sla", background="#E8F4FF")
    sla_tree.tag_configure("due_soon", background="#FFF4D6")
    sla_tree.tag_configure("sla_breached", background="#FFE8E8") 

    widths = (
        80,
        140,
        100,
        100,
        150,
        150,
        120,
        130
    )

    for column, width in zip(columns, widths):
        sla_tree.heading(
            column,
            text=column
        )

        sla_tree.column(
            column,
            width=width,
            anchor="center"
        )

    sla_tree.pack(
        side="left",
        fill="both",
        expand=True
    )

    scrollbar = ttk.Scrollbar(
        table_frame,
        orient="vertical",
        command=sla_tree.yview
    )

    scrollbar.pack(
        side="right",
        fill="y"
    )

    sla_tree.configure(
        yscrollcommand=scrollbar.set
    )

    # -------------------------------------------------
    # LOAD SLA DATA
    # -------------------------------------------------

    def load_sla_report_data():

        sla_tree.delete(
            *sla_tree.get_children()
        )

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                tickets.id,
                employee.name,
                tickets.priority,
                tickets.status,
                tickets.created_at,
                tickets.resolved_at,
                tickets.assigned_to 
            FROM tickets
            JOIN users AS employee
                ON tickets.user_id = employee.id
            ORDER BY tickets.id DESC
        """)

        tickets = cursor.fetchall()

        cursor.close()
        connection.close()

        # ---------------------------------------------
        # SLA LIMITS
        # ---------------------------------------------

        sla_limits = {
            "Critical": 4,
            "High": 8,
            "Medium": 24,
            "Low": 48
        }

        # ---------------------------------------------
        # SLA COUNTS
        # ---------------------------------------------

        counts = {
            "SLA Met": 0,
            "Within SLA": 0,
            "Due Soon": 0,
            "SLA Breached": 0
        }

        # ---------------------------------------------
        # PROCESS EACH TICKET
        # ---------------------------------------------

        for ticket in tickets:

            (
                ticket_id,
                employee_name,
                priority,
                status,
                created_at,
                resolved_at,
                assigned_to 
            ) = ticket

            sla_hours = sla_limits.get(
                priority,
                24
            )

            # Resolved ticket → use resolved time
            if (
                status == "RESOLVED"
                and resolved_at
            ):
                end_time = resolved_at

            # Active ticket → use current time
            else:
                end_time = datetime.now()

            elapsed_seconds = (
                end_time - created_at
            ).total_seconds()

            elapsed_hours = (
                elapsed_seconds / 3600
            )

            elapsed_minutes = int(
                elapsed_seconds / 60
            )

            hours = elapsed_minutes // 60
            minutes = elapsed_minutes % 60

            elapsed_display = (
                f"{hours}h {minutes}m"
            )

            # -----------------------------------------
            # DETERMINE SLA STATUS
            # -----------------------------------------

            if status == "RESOLVED":

                if elapsed_hours <= sla_hours:
                    sla_status = "SLA Met"

                else:
                    sla_status = "SLA Breached"

            else:

                if elapsed_hours > sla_hours:
                    sla_status = "SLA Breached"

                elif elapsed_hours >= (
                    sla_hours * 0.75
                ):
                    sla_status = "Due Soon"

                else:
                    sla_status = "Within SLA"

                # -----------------------------------------
                # SLA BREACH NOTIFICATION
                # -----------------------------------------

                if (
                    sla_status == "SLA Breached"
                    and status != "RESOLVED"
                ):
                    notify_sla_breach(
                        ticket_id,
                        assigned_to
                    )

                if sla_status == "SLA Met":
                    tag_name = "sla_met"

                elif sla_status == "Within SLA":
                    tag_name = "within_sla"

                elif sla_status == "Due Soon":
                    tag_name = "due_soon"

                else:
                    tag_name = "sla_breached"

            # -----------------------------------------
            # UPDATE COUNTS
            # -----------------------------------------

            counts[sla_status] += 1

            # -----------------------------------------
            # SLA STATUS COLOR
            # -----------------------------------------

            if sla_status == "SLA Met":
                tag_name = "sla_met"

            elif sla_status == "Within SLA":
                tag_name = "within_sla"

            elif sla_status == "Due Soon":
                tag_name = "due_soon"

            else:
                tag_name = "sla_breached"

           
            # -----------------------------------------
            # INSERT INTO TABLE
            # -----------------------------------------

            resolved_display = (
                resolved_at.strftime(
                    "%Y-%m-%d %H:%M"
                )
                if resolved_at
                else "—"
            )
            sla_tree.insert(
                "",
                tk.END,
                values=(
                    ticket_id,
                    employee_name,
                    priority,
                    f"{sla_hours} hrs",
                    created_at.strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                    resolved_display,
                    elapsed_display,
                    sla_status
                ),
                tags=(tag_name,)
            )

        # ---------------------------------------------
        # UPDATE SUMMARY CARDS
        # ---------------------------------------------

        sla_vars["SLA Met"].set(
            str(counts["SLA Met"])
        )

        sla_vars["Within SLA"].set(
            str(counts["Within SLA"])
        )

        sla_vars["Due Soon"].set(
            str(counts["Due Soon"])
        )

        sla_vars["SLA Breached"].set(
            str(counts["SLA Breached"])
        )

        # ---------------------------------------------
        # SLA COMPLIANCE
        # ---------------------------------------------

        completed_tickets = (
            counts["SLA Met"]
            + counts["SLA Breached"]
        )

        if completed_tickets > 0:

            compliance = (
                counts["SLA Met"]
                / completed_tickets
            ) * 100

        else:
            compliance = 0

        sla_vars["SLA Compliance"].set(
            f"{compliance:.0f}%"
        )

    load_sla_report_data()


                  


window = tk.Tk()
setup_window(window, "IT Support Management System", "1280x760")
window.minsize(1050, 650)

show_login_window()

window.mainloop()