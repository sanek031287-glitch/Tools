import os
import sys
import ctypes
import json
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

VERSION = "v1.4"
AUTHOR = "Sarz_656"

# ---------- СКРЫТИЕ КОНСОЛИ ----------
def hide_console():
    try:
        kernel32 = ctypes.WinDLL('kernel32')
        user32 = ctypes.WinDLL('user32')
        hwnd = kernel32.GetConsoleWindow()
        if hwnd:
            user32.ShowWindow(hwnd, 0)
    except:
        pass

# ---------- ПРАВА АДМИНА ----------
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if not is_admin():
        pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        if not os.path.exists(pythonw):
            pythonw = sys.executable
        params = " ".join(f'"{a}"' for a in sys.argv)
        ctypes.windll.shell32.ShellExecuteW(None, "runas", pythonw, params, None, 0)
        sys.exit()

# ---------- КОНФИГ ----------
CONFIG_FILE = "config.json"

def load_config():
    default = {
        "version": VERSION,
        "author": AUTHOR,
        "show_splash": True,
        "splash_duration_ms": 1800,
        "last_folder": "",
        "last_size": 10,
        "last_border": 4,
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                default.update(cfg)
        except:
            pass
    else:
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(default, f, indent=2, ensure_ascii=False)
        except:
            pass
    return default

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except:
        pass

CONFIG = load_config()

# ---------- ГЕНЕРАЦИЯ QR ----------
def generate_qr(data, filepath, size=10, border=4):
    import qrcode
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filepath)

# ---------- ГЛАВНОЕ ОКНО ----------
class QRApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Генератор QR-кодов {VERSION} — by {AUTHOR}")
        self.root.geometry("620x620")
        self.root.resizable(False, False)

        # Тип данных
        tk.Label(root, text="Что закодировать:", anchor="w",
                 font=("Segoe UI", 10, "bold")).pack(fill="x", padx=15, pady=(15, 5))

        self.qr_type = tk.StringVar(value="Текст")
        type_frame = tk.Frame(root)
        type_frame.pack(fill="x", padx=15)
        for t in ["Текст", "Ссылка", "Wi-Fi", "Телефон", "Email"]:
            tk.Radiobutton(type_frame, text=t, variable=self.qr_type,
                           value=t, command=self.on_type_change).pack(side="left", padx=5)

        # Поле ввода
        tk.Label(root, text="Содержимое:", anchor="w",
                 font=("Segoe UI", 10, "bold")).pack(fill="x", padx=15, pady=(15, 5))

        self.text_input = tk.Text(root, height=6, font=("Consolas", 10))
        self.text_input.pack(fill="x", padx=15)

        # Кнопки под полем
        text_btns = tk.Frame(root)
        text_btns.pack(fill="x", padx=15, pady=(3, 0))
        tk.Button(text_btns, text="📋 Вставить", command=self.paste_clipboard,
                  width=14, bg="#2980b9", fg="white").pack(side="left")
        tk.Button(text_btns, text="🗑 Очистить", command=self.clear_text,
                  width=14).pack(side="left", padx=5)
        tk.Button(text_btns, text="Выделить всё", command=self.select_all_text,
                  width=14).pack(side="left", padx=5)

        # Привязки клавиш
        self.text_input.bind("<Control-v>", lambda e: self.paste_clipboard())
        self.text_input.bind("<Control-V>", lambda e: self.paste_clipboard())
        self.text_input.bind("<Control-a>", lambda e: self.select_all_text())
        self.text_input.bind("<Button-3>", self.show_context_menu)

        # Wi-Fi поля
        self.wifi_frame = tk.Frame(root)
        tk.Label(self.wifi_frame, text="SSID:").pack(side="left", padx=(0, 5))
        self.wifi_ssid = tk.Entry(self.wifi_frame, width=20)
        self.wifi_ssid.pack(side="left", padx=(0, 15))
        tk.Label(self.wifi_frame, text="Пароль:").pack(side="left", padx=(0, 5))
        self.wifi_pass = tk.Entry(self.wifi_frame, width=20, show="*")
        self.wifi_pass.pack(side="left")

        # Настройки
        settings = tk.Frame(root)
        settings.pack(fill="x", padx=15, pady=15)

        tk.Label(settings, text="Размер:").pack(side="left")
        self.size_var = tk.StringVar(value=str(CONFIG.get("last_size", 10)))
        ttk.Combobox(settings, textvariable=self.size_var, width=4,
                     values=["5", "8", "10", "15", "20"],
                     state="readonly").pack(side="left", padx=5)

        tk.Label(settings, text="Отступ:").pack(side="left", padx=(15, 0))
        self.border_var = tk.StringVar(value=str(CONFIG.get("last_border", 4)))
        ttk.Combobox(settings, textvariable=self.border_var, width=4,
                     values=["1", "2", "4", "6", "8"],
                     state="readonly").pack(side="left", padx=5)

        # Кнопки
        buttons = tk.Frame(root)
        buttons.pack(fill="x", padx=15, pady=5)

        tk.Button(buttons, text="💾 Сохранить QR", command=self.save_qr,
                  width=20, bg="#27ae60", fg="white",
                  font=("Segoe UI", 10, "bold")).pack(side="left")

        tk.Button(buttons, text="👁 Предпросмотр", command=self.preview_qr,
                  width=18).pack(side="left", padx=5)

        tk.Button(buttons, text="📂 Открыть папку", command=self.open_folder,
                  width=16).pack(side="left", padx=5)

        # Статус
        self.status = tk.Label(root, text=f"Готов. — {AUTHOR}", anchor="w", fg="#555")
        self.status.pack(fill="x", padx=15, pady=(10, 5))

        self.on_type_change()

    # ---------- РАБОТА С ТЕКСТОМ ----------
    def paste_clipboard(self):
        try:
            text = self.root.clipboard_get()
        except Exception:
            try:
                import win32clipboard
                win32clipboard.OpenClipboard()
                text = win32clipboard.GetClipboardData()
                win32clipboard.CloseClipboard()
            except Exception:
                self.status.config(text="Буфер обмена пуст или недоступен.", fg="#c0392b")
                return "break"

        if text:
            self.text_input.insert("insert", text)
            self.status.config(text="Вставлено из буфера.", fg="#27ae60")
        return "break"

    def clear_text(self):
        self.text_input.delete("1.0", "end")
        return "break"

    def select_all_text(self):
        self.text_input.tag_add("sel", "1.0", "end")
        self.text_input.mark_set("insert", "1.0")
        self.text_input.see("insert")
        return "break"

    def show_context_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Вырезать",
                         command=lambda: self.text_input.event_generate("<<Cut>>"))
        menu.add_command(label="Копировать",
                         command=lambda: self.text_input.event_generate("<<Copy>>"))
        menu.add_command(label="Вставить", command=self.paste_clipboard)
        menu.add_separator()
        menu.add_command(label="Выделить всё", command=self.select_all_text)
        menu.add_command(label="Очистить", command=self.clear_text)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
        return "break"

    # ---------- ЛОГИКА ----------
    def on_type_change(self):
        t = self.qr_type.get()
        if t == "Wi-Fi":
            self.wifi_frame.pack(fill="x", padx=15, pady=(5, 0))
            self.text_input.config(state="disabled", bg="#eee")
        else:
            self.wifi_frame.pack_forget()
            self.text_input.config(state="normal", bg="white")

    def build_data(self):
        t = self.qr_type.get()
        if t == "Wi-Fi":
            ssid = self.wifi_ssid.get().strip()
            pwd = self.wifi_pass.get().strip()
            if not ssid:
                messagebox.showerror("Ошибка", "Введи SSID сети.")
                return None
            return f"WIFI:T:WPA;S:{ssid};P:{pwd};;"
        else:
            text = self.text_input.get("1.0", "end").strip()
            if not text:
                messagebox.showerror("Ошибка", "Введи текст для QR-кода.")
                return None
            if t == "Ссылка" and not text.startswith(("http://", "https://")):
                text = "https://" + text
            return text

    def save_qr(self):
        data = self.build_data()
        if data is None:
            return

        last_folder = CONFIG.get("last_folder", "") or os.path.expanduser("~")
        filename = f"qr_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"
        filepath = filedialog.asksaveasfilename(
            initialdir=last_folder,
            initialfile=filename,
            defaultextension=".png",
            filetypes=[("PNG-картинка", "*.png")],
        )
        if not filepath:
            return

        try:
            size = int(self.size_var.get())
            border = int(self.border_var.get())
            generate_qr(data, filepath, size, border)

            CONFIG["last_folder"] = os.path.dirname(filepath)
            CONFIG["last_size"] = size
            CONFIG["last_border"] = border
            save_config(CONFIG)

            self.status.config(text=f"Сохранено: {filepath}", fg="#27ae60")
            messagebox.showinfo("Готово", f"QR-код сохранён:\n{filepath}")
        except Exception as e:
            self.status.config(text=f"Ошибка: {e}", fg="#c0392b")
            messagebox.showerror("Ошибка", str(e))

    def preview_qr(self):
        data = self.build_data()
        if data is None:
            return

        try:
            import qrcode
            from PIL import ImageTk

            size = int(self.size_var.get())
            border = int(self.border_var.get())

            qr = qrcode.QRCode(
                version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=size,
                border=border,
            )
            qr.add_data(data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            tk_img = ImageTk.PhotoImage(img)

            preview_win = tk.Toplevel(self.root)
            preview_win.title(f"Предпросмотр QR — by {AUTHOR}")
            preview_win.resizable(False, False)
            preview_win.transient(self.root)
            preview_win.grab_set()

            label = tk.Label(preview_win, image=tk_img)
            label.image = tk_img
            label.pack(padx=15, pady=15)

            tk.Label(preview_win, text=f"Данные: {data[:80]}",
                     font=("Consolas", 8), fg="#666").pack(padx=15)

            tk.Button(preview_win, text="Закрыть",
                      command=preview_win.destroy,
                      width=15).pack(pady=10)

            self.status.config(text="Предпросмотр открыт.", fg="#2980b9")
        except Exception as e:
            self.status.config(text=f"Ошибка: {e}", fg="#c0392b")
            messagebox.showerror("Ошибка", str(e))

    def open_folder(self):
        folder = CONFIG.get("last_folder", "") or os.path.expanduser("~")
        try:
            os.startfile(folder)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

# ---------- ЗАСТАВКА ----------
def show_splash(duration=1800):
    splash = tk.Tk()
    splash.overrideredirect(True)
    splash.configure(bg="#1e1e1e")
    w, h = 420, 220
    x = (splash.winfo_screenwidth() - w) // 2
    y = (splash.winfo_screenheight() - h) // 2
    splash.geometry(f"{w}x{h}+{x}+{y}")

    tk.Label(splash, text="Генератор QR-кодов",
             font=("Segoe UI", 16, "bold"),
             fg="white", bg="#1e1e1e").pack(pady=(40, 5))
    tk.Label(splash, text=VERSION,
             font=("Segoe UI", 11),
             fg="#aaaaaa", bg="#1e1e1e").pack()
    tk.Label(splash, text=f"by {AUTHOR}",
             font=("Segoe UI", 13, "italic"),
             fg="#4ea1ff", bg="#1e1e1e").pack(pady=(20, 0))

    splash.after(duration, splash.destroy)
    splash.mainloop()

# ---------- ЗАПУСК ----------
if __name__ == "__main__":
    if os.name == "nt":
        hide_console()
        run_as_admin()
    if CONFIG.get("show_splash", True):
        show_splash(CONFIG.get("splash_duration_ms", 1800))
    root = tk.Tk()
    app = QRApp(root)
    root.mainloop()