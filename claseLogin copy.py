import tkinter as tk
from tkinter import messagebox
import sqlite3
import hashlib

def create_connection():
    """Create and return a connection to the SQLite database."""
    try:
        connection = sqlite3.connect('registros.db')
        return connection
    except sqlite3.Error as e:
        print(f"Error: {e}")
    return None

def check_credentials(usuario, contrasena):
    """Check if the given credentials are valid."""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            hashed_password = hashlib.sha256(contrasena.encode()).hexdigest()
            cursor.execute("SELECT contrasena FROM login WHERE usuario = ?", (usuario,))
            record = cursor.fetchone()
            return record and record[0] == hashed_password
        except sqlite3.Error as e:
            print(f"Error en check_credentials: {e}")
        finally:
            cursor.close()
            connection.close()
    return False

class Login:
    def __init__(self, master):
        self.master = master
        self.master.title("Login")
        self.master.geometry('300x150')

        self.username_label = tk.Label(master, text="Username:")
        self.username_label.pack(pady=5)
        
        self.username_entry = tk.Entry(master)
        self.username_entry.pack(pady=5)
        
        self.password_label = tk.Label(master, text="Password:")
        self.password_label.pack(pady=5)
        
        self.password_entry = tk.Entry(master, show="*")
        self.password_entry.pack(pady=5)
        
        self.login_button = tk.Button(master, text="Login", command=self.handle_login)
        self.login_button.pack(pady=10)
    
    def handle_login(self):
        user = self.username_entry.get()
        password = self.password_entry.get()
        
        if check_credentials(user, password):
            messagebox.showinfo("Login", "Login Successful")
            self.open_main_window()
        else:
            messagebox.showerror("Login", "Invalid Credentials")
    
    def open_main_window(self):
        # Cierra la ventana de login
        self.master.destroy()
        
        # Crear nueva ventana principal
        main_window = tk.Tk()
        main_window.title("Main Window")
        main_window.geometry('400x300')
        
        # Aquí agregarías tus paneles y widgets
        label = tk.Label(main_window, text="Welcome to the Main Window")
        label.pack(pady=20)

        # Ejecutar el mainloop de la nueva ventana principal
        main_window.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = Login(root)
    root.mainloop()
from tkinter import BOTH, END, LEFT, Button, Entry, Frame, Label, Tk, messagebox
from PIL import Image, ImageTk
import sqlite3
import hashlib
import os

def create_connection():
    try:
        connection = sqlite3.connect('registros.db')
        return connection
    except sqlite3.Error as e:
        print(f"Error: {e}")
    return None

def check_credentials(usuario, contrasena):
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            hashed_password = hashlib.sha256(contrasena.encode()).hexdigest()
            cursor.execute("SELECT contrasena FROM login WHERE usuario = ?", (usuario,))
            record = cursor.fetchone()
            return record and record[0] == hashed_password
        except sqlite3.Error as e:
            print(f"Error en check_credentials: {e}")
        finally:
            cursor.close()
            connection.close()
    return False

class Login:
    def __init__(self, master):
        self.master = master
        self.master.title("Analizador de la Calidad de la Energia")
        self.master.geometry('500x250')
        self.master.resizable(False, False)
        self.center_window(500, 250)

        main_frame = Frame(self.master, bg='white')
        main_frame.pack(fill=BOTH, expand=True)

        title_frame = Frame(main_frame, bg='#2c1d52', pady=10)
        title_frame.pack(fill='x')

        icon_path = os.path.join("C:/", "Users", "ASUS", "OneDrive", "Escritorio", "FenomenosV", "imgInterfaz", "electric.png")
        icon_image = Image.open(icon_path)
        icon_image = icon_image.resize((40, 40), Image.LANCZOS)
        icon_photo = ImageTk.PhotoImage(icon_image)
        icon_label = Label(title_frame, image=icon_photo, bg='#2c1d52')
        icon_label.image = icon_photo
        icon_label.pack(side=LEFT, padx=(20, 10))

        title_label = Label(title_frame, text='Analizador de la calidad de la Energia', font=('Arial', 18), fg='white', bg='#2c1d52')
        title_label.pack(side=LEFT)

        content_frame = Frame(main_frame, bg='white')
        content_frame.pack(pady=20)

        self.user_input = Entry(content_frame, font=('Arial', 12))
        self.user_input.pack(pady=10, padx=20)
        self.user_input.insert(0, 'Usuario')
        self.user_input.bind("<FocusIn>", lambda e: self.user_input.delete(0, END) if self.user_input.get() == 'Usuario' else None)

        self.pass_input = Entry(content_frame, font=('Arial', 12), show='*')
        self.pass_input.pack(pady=10, padx=20)
        self.pass_input.insert(0, 'Contraseña')
        self.pass_input.bind("<FocusIn>", lambda e: self.pass_input.delete(0, END) if self.pass_input.get() == 'Contraseña' else None)

        self.login_button = Button(content_frame, text='Iniciar sesión', font=('Arial', 12), bg='#4A3088', fg='white', command=self.handle_login)
        self.login_button.pack(pady=20)

        self.style_button(self.login_button)

    def center_window(self, width, height):
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.master.geometry(f'{width}x{height}+{x}+{y}')

    def style_button(self, button):
        button.configure(
            bg='#4A3088',
            fg='white',
            font=('Arial', 12),
            relief='flat'
        )
        button.bind("<Enter>", lambda e: button.configure(bg='#5A4098'))
        button.bind("<Leave>", lambda e: button.configure(bg='#4A3088'))

    def handle_login(self):
        try:
            usuario = self.user_input.get()
            contrasena = self.pass_input.get()
            if check_credentials(usuario, contrasena):
                self.open_main_window()
            else:
                self.show_error_message()
        except Exception as e:
            print(f"Error en handle_login: {e}")
            self.show_error_message()

    def show_error_message(self):
        messagebox.showerror('Error', 'Datos erroneos. Intente de nuevo.')
        self.user_input.delete(0, END)
        self.pass_input.delete(0, END)

    def open_main_window(self):
        self.master.destroy()
        main_window = Tk()
        main_window.title("Main Window")
        label = Label(main_window, text="Welcome to the Main Window")
        label.pack()
        main_window.mainloop()

if __name__ == "__main__":
    root = Tk()
    app = Login(root)
    root.mainloop()
