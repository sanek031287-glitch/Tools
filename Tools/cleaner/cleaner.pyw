import os
import sys
import ctypes
import shutil
import threading
import json
import traceback
import subprocess
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

VERSION = "v6.0"
AUTHOR = "Sarz_656"

def log_error(e):
    with open("error_log.txt", "a", encoding="utf-8") as f:
        f.write(f"\n=== {datetime.now()} ===\n")
        f.write(traceback.format_exc() + "\n")

CONFIG_FILE = "config.json"

def load_config():
    default = {
        "version": VERSION,
        "author": AUTHOR,
        "empty_recycle_bin": True,
        "show_splash": True,
        "splash_duration_ms": 2000,
        "disk_cleanup": True,
        "disk_cleanup_profile": 1,
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                default.update(cfg)
        except:
            pass
    else:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2, ensure_ascii=False)
    return default

CONFIG = load_config()

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

# ---------- СПИСОК ПАПОК ДЛЯ ОЧИСТКИ ----------
def get_clean_targets():
    user = os.environ.get("USERPROFILE", "")
    local = os.environ.get("LOCALAPPDATA", "")
    roaming = os.environ.get("APPDATA", "")
    windir = os.environ.get("WINDIR", "C:\\Windows")
    progdata = os.environ.get("PROGRAMDATA", "C:\\ProgramData")

    targets = {
        "Temp (пользователь)": os.path.join(local, "Temp"),
        "Temp (Windows)": os.path.join(windir, "Temp"),
        "Chrome Cache": os.path.join(local, "Google", "Chrome", "User Data", "Default", "Cache"),
        "Chrome Code Cache": os.path.join(local, "Google", "Chrome", "User Data", "Default", "Code Cache"),
        "Chrome GPUCache": os.path.join(local, "Google", "Chrome", "User Data", "Default", "GPUCache"),
        "Edge Cache": os.path.join(local, "Microsoft", "Edge", "User Data", "Default", "Cache"),
        "Edge Code Cache": os.path.join(local, "Microsoft", "Edge", "User Data", "Default", "Code Cache"),
        "Edge GPUCache": os.path.join(local, "Microsoft", "Edge", "User Data", "Default", "GPUCache"),
        "Firefox Cache": os.path.join(local, "Mozilla", "Firefox", "Profiles"),
        "Opera Cache": os.path.join(roaming, "Opera Software", "Opera Stable", "Cache"),
        "Brave Cache": os.path.join(local, "BraveSoftware", "Brave-Browser", "User Data", "Default", "Cache"),
        "Yandex Cache": os.path.join(local, "Yandex", "YandexBrowser", "User Data", "Default", "Cache"),
        "Telegram Cache": os.path.join(roaming, "Telegram Desktop", "tdata", "user_data", "cache"),
        "Discord Cache": os.path.join(roaming, "discord", "Cache"),
        "Discord Code Cache": os.path.join(roaming, "discord", "Code Cache"),
        "Discord GPUCache": os.path.join(roaming, "discord", "GPUCache"),
        "Skype Cache": os.path.join(local, "Packages", "Microsoft.SkypeApp_kzf8qxf38zg5c", "LocalCache"),
        "Spotify Cache": os.path.join(local, "Spotify", "Storage"),
        "VLC Cache": os.path.join(roaming, "vlc", "cache"),
        "Windows Update Cache": os.path.join(windir, "SoftwareDistribution", "Download"),
        "Windows Logs": os.path.join(windir, "Logs"),
        "Windows Error Reporting": os.path.join(local, "Microsoft", "Windows", "WER"),
        "Windows Error Reporting (ProgramData)": os.path.join(progdata, "Microsoft", "Windows", "WER"),
        "Windows Prefetch": os.path.join(windir, "Prefetch"),
        "INetCache": os.path.join(local, "Microsoft", "Windows", "INetCache"),
        "Explorer Thumbnails": os.path.join(local, "Microsoft", "Windows", "Explorer"),
        "Recent Files": os.path.join(roaming, "Microsoft", "Windows", "Recent"),
        "Microsoft Store Cache": os.path.join(local, "Packages", "Microsoft.WindowsStore_8wekyb3d8bbwe", "LocalCache"),
        "D3DSCache": os.path.join(local, "D3DSCache"),
        "NVIDIA Cache": os.path.join(local, "NVIDIA", "DXCache"),
        "AMD Cache": os.path.join(local, "AMD", "DxCache"),
        "CrashDumps": os.path.join(local, "CrashDumps"),
        "Font Cache": os.path.join(local, "FontCache"),
    }

    return {name: path for name, path in targets.items() if os.path.exists(path)}

# ---------- ФУНКЦИИ ----------
def human_size(num):
    for unit in ["Б", "КБ", "МБ", "ГБ"]:
        if num < 1024:
            return f"{num:.1f} {unit}"
        num /= 1024
    return f"{num:.1f} ТБ"

def get_folder_size(folder):
    total = 0
    try:
        for root, dirs, files in os.walk(folder):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except:
                    pass
    except:
        pass
    return total

def clean_folder_contents(folder):
    deleted = 0
    errors = 0
    freed = 0
    try:
        for name in os.listdir(folder):
            full = os.path.join(folder, name)
            try:
                if os.path.isfile(full) or os.path.islink(full):
                    size = os.path.getsize(full)
                    os.remove(full)
                    deleted += 1
                    freed += size
                elif os.path.isdir(full):
                    size = get_folder_size(full)
                    shutil.rmtree(full, ignore_errors=False)
                    deleted += 1
                    freed += size
            except Exception:
                errors += 1
    except Exception:
        errors += 1
    return deleted, errors, freed

def empty_recycle_bin():
    try:
        flags = 0x00000001 | 0x00000002 | 0x00000004
        result = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, flags)
        if result == 0:
            return True, "OK"
        return False, f"Код {result}"
    except Exception as e:
        return False, str(e)

def parse_size(text):
    try:
        parts = text.split()
        if len(parts) != 2:
            return 0
        num = float(parts[0])
        unit = parts[1]
        multipliers = {"Б": 1, "КБ": 1024, "МБ": 1024**2, "ГБ": 1024**3, "ТБ": 1024**4}
        return int(num * multipliers.get(unit, 1))
    except:
        return 0

# ---------- ГЛАВНОЕ ОКНО ----------
class CleanerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Чистильщик мусора PRO {VERSION} — by {AUTHOR}")
        self.root.geometry("1050x700")

        self.targets = get_clean_targets()
        self.scanning = False
        self.stop_flag = False
        self.check_vars = {}

        # Данные для вкладки больших файлов
        self.big_files = []
        self.big_scanning = False
        self.big_stop_flag = [False]

        # Верхняя панель
        top = tk.Frame(root)
        top.pack(fill="x", padx=10, pady=8)

        self.scan_btn = tk.Button(top, text="🔍 Анализ", command=self.start_scan, width=14)
        self.scan_btn.pack(side="left")

        self.stop_btn = tk.Button(top, text="⏹ Стоп", command=self.stop_scan, width=10, state="disabled")
        self.stop_btn.pack(side="left", padx=5)

        self.clean_btn = tk.Button(top, text="🧹 Очистить выбранное", command=self.clean_selected,
                                   width=22, bg="#c0392b", fg="white", state="disabled")
        self.clean_btn.pack(side="left", padx=10)

        self.status = tk.Label(root, text=f"Готов. Нажми «Анализ». — {AUTHOR}", anchor="w")
        self.status.pack(fill="x", padx=10)

        # Вкладки
        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # Вкладка 1: очистка мусора
        tab1 = tk.Frame(notebook)
        notebook.add(tab1, text="Очистка мусора")
        self.build_clean_tab(tab1)

        # Вкладка 2: большие файлы
        tab2 = tk.Frame(notebook)
        notebook.add(tab2, text="Большие файлы")
        self.build_big_files_tab(tab2)

        # Нижняя панель
        bottom = tk.Frame(root)
        bottom.pack(fill="x", padx=10, pady=5)
        tk.Button(bottom, text="Выделить всё", command=lambda: self.toggle_all(True)).pack(side="left")
        tk.Button(bottom, text="Снять всё", command=lambda: self.toggle_all(False)).pack(side="left", padx=5)

        self.total_label = tk.Label(bottom, text="", anchor="e")
        self.total_label.pack(side="right")

        self.recycle_var = tk.BooleanVar(value=CONFIG.get("empty_recycle_bin", True))
        tk.Checkbutton(bottom, text="Очистить корзину", variable=self.recycle_var).pack(side="left", padx=20)

        self.diskclean_var = tk.BooleanVar(value=CONFIG.get("disk_cleanup", True))
        tk.Checkbutton(bottom, text="Очистка диска Windows", variable=self.diskclean_var).pack(side="left", padx=10)

        self.build_category_list()

    # ---------- ВКЛАДКА ОЧИСТКИ ----------
    def build_clean_tab(self, parent):
        frame = tk.Frame(parent)
        frame.pack(fill="both", expand=True, padx=5, pady=5)

        canvas = tk.Canvas(frame)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        self.inner = tk.Frame(canvas)
        self.inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def build_category_list(self):
        for name in self.targets.keys():
            row = tk.Frame(self.inner)
            row.pack(fill="x", pady=1)
            var = tk.BooleanVar(value=True)
            cb = tk.Checkbutton(row, variable=var, text=name, anchor="w", width=35,
                                command=self.update_total)
            cb.pack(side="left")
            size_label = tk.Label(row, text="—", width=15, anchor="w", fg="#666")
            size_label.pack(side="left")
            path_label = tk.Label(row, text=self.targets[name], anchor="w", fg="#888",
                                  font=("Consolas", 8))
            path_label.pack(side="left")
            self.check_vars[name] = (var, size_label)

    # ---------- ВКЛАДКА БОЛЬШИХ ФАЙЛОВ ----------
    def build_big_files_tab(self, parent):
        top = tk.Frame(parent)
        top.pack(fill="x", padx=5, pady=5)

        tk.Label(top, text="Диск:").pack(side="left")
        self.drive_var = tk.StringVar(value="ВСЕ")
        drives = ["ВСЕ"] + self.get_drives()
        ttk.Combobox(top, textvariable=self.drive_var, values=drives,
                     width=10, state="readonly").pack(side="left", padx=5)

        tk.Label(top, text="Топ:").pack(side="left", padx=(15, 5))
        self.top_var = tk.StringVar(value="500")
        ttk.Combobox(top, textvariable=self.top_var,
                     values=["100", "500", "1000", "2000"],
                     width=6, state="readonly").pack(side="left")

        tk.Label(top, text="Искать:").pack(side="left", padx=(15, 5))
        self.mode_var = tk.StringVar(value="Файлы")
        ttk.Combobox(top, textvariable=self.mode_var,
                     values=["Файлы", "Папки"],
                     width=8, state="readonly").pack(side="left")

        self.big_scan_btn = tk.Button(top, text="🔍 Найти", command=self.start_big_scan, width=10)
        self.big_scan_btn.pack(side="left", padx=10)

        self.big_stop_btn = tk.Button(top, text="⏹ Стоп", command=self.stop_big_scan,
                                      width=10, state="disabled")
        self.big_stop_btn.pack(side="left", padx=5)

        tk.Button(top, text="🗑 Удалить выбранное", command=self.delete_big_selected,
                  width=20, bg="#c0392b", fg="white").pack(side="left", padx=10)

        tk.Button(top, text="📂 Открыть папку", command=self.open_big_folder).pack(side="left", padx=5)

        self.big_status = tk.Label(parent, text="Выбери диск и нажми «Найти».", anchor="w")
        self.big_status.pack(fill="x", padx=5)

        frame = tk.Frame(parent)
        frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.big_list = tk.Listbox(frame, selectmode="extended", font=("Consolas", 9))
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=self.big_list.yview)
        self.big_list.configure(yscrollcommand=scrollbar.set)
        self.big_list.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.big_total_label = tk.Label(parent, text="", anchor="e")
        self.big_total_label.pack(fill="x", padx=5)

    def get_drives(self):
        drives = []
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            path = f"{letter}:\\"
            if os.path.exists(path):
                drives.append(path)
        return drives

    def start_big_scan(self):
        if self.big_scanning:
            return
        self.big_scanning = True
        self.big_stop_flag[0] = False
        self.big_files.clear()
        self.big_list.delete(0, "end")
        self.big_scan_btn.config(state="disabled")
        self.big_stop_btn.config(state="normal")
        self.big_status.config(text="Сканирование...")
        threading.Thread(target=self.scan_big, daemon=True).start()

    def stop_big_scan(self):
        self.big_stop_flag[0] = True
        self.big_status.config(text="Остановка...")

    def scan_big(self):
        try:
            drive = self.drive_var.get()
            top_n = int(self.top_var.get())
            mode = self.mode_var.get()

            if drive == "ВСЕ":
                drives_to_scan = self.get_drives()
            else:
                drives_to_scan = [drive]

            all_items = []

            if mode == "Файлы":
                for d in drives_to_scan:
                    for root, dirs, files in os.walk(d):
                        if self.big_stop_flag[0]:
                            break
                        self.root.after(0, lambda r=root: self.big_status.config(text=f"Смотрю: {r[:80]}..."))
                        for name in files:
                            if self.big_stop_flag[0]:
                                break
                            full = os.path.join(root, name)
                            try:
                                size = os.path.getsize(full)
                                all_items.append((size, full))
                            except:
                                continue
            else:
                for d in drives_to_scan:
                    for root, dirs, files in os.walk(d):
                        if self.big_stop_flag[0]:
                            break
                        self.root.after(0, lambda r=root: self.big_status.config(text=f"Смотрю: {r[:80]}..."))
                        for sub in dirs:
                            if self.big_stop_flag[0]:
                                break
                            sub_path = os.path.join(root, sub)
                            try:
                                size = get_folder_size(sub_path)
                                if size > 100 * 1024 * 1024:
                                    all_items.append((size, sub_path))
                            except:
                                continue

            all_items.sort(reverse=True)
            self.big_files = all_items[:top_n]

            self.root.after(0, self.show_big_results)
        except Exception as e:
            log_error(e)
            self.root.after(0, lambda: self.big_status.config(text=f"ОШИБКА: {e}"))

    def show_big_results(self):
        self.big_scanning = False
        self.big_scan_btn.config(state="normal")
        self.big_stop_btn.config(state="disabled")

        if not self.big_files:
            self.big_status.config(text="Ничего не найдено.")
            return

        total = 0
        for size, path in self.big_files:
            total += size
            try:
                mtime = os.path.getmtime(path)
                date = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
            except:
                date = "—"
            self.big_list.insert("end", f"{human_size(size):>10}  {date}  {path}")

        self.big_status.config(text=f"Найдено: {len(self.big_files)} объектов")
        self.big_total_label.config(text=f"Всего: {human_size(total)}")

    def open_big_folder(self):
        sel = self.big_list.curselection()
        if not sel:
            messagebox.showinfo("Инфо", "Выбери файл.")
            return
        _, path = self.big_files[sel[0]]
        os.startfile(os.path.dirname(path))

    def delete_big_selected(self):
        sel = self.big_list.curselection()
        if not sel:
            messagebox.showinfo("Инфо", "Ничего не выбрано.")
            return

        to_delete = [self.big_files[i] for i in sel]
        total = sum(s for s, _ in to_delete)

        if not messagebox.askyesno("Подтверждение",
                                   f"Удалить {len(to_delete)} объектов?\n"
                                   f"Освободится: {human_size(total)}\n\n"
                                   f"ВНИМАНИЕ: удаляй только то, в чём уверен!"):
            return

        deleted = 0
        freed = 0
        errors = 0
        log_lines = []

        for size, path in to_delete:
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=False)
                    deleted += 1
                    freed += size
                    log_lines.append(f"OK (папка) {path}")
                else:
                    os.remove(path)
                    deleted += 1
                    freed += size
                    log_lines.append(f"OK (файл)  {path}")
            except Exception as e:
                errors += 1
                log_lines.append(f"ERR {path} :: {e}")

        with open("cleaner_log.txt", "a", encoding="utf-8") as log:
            log.write(f"\n=== {datetime.now()} | Большие файлы | by {AUTHOR} ===\n")
            log.write("\n".join(log_lines) + "\n")

        messagebox.showinfo("Готово",
                            f"Удалено: {deleted}\n"
                            f"Ошибок: {errors}\n"
                            f"Освобождено: {human_size(freed)}")
        self.start_big_scan()

    # ---------- СТАРЫЕ МЕТОДЫ ОЧИСТКИ ----------
    def start_scan(self):
        if self.scanning:
            return
        self.scanning = True
        self.stop_flag = False
        self.scan_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.clean_btn.config(state="disabled")
        self.status.config(text="Анализ...")
        threading.Thread(target=self.scan, daemon=True).start()

    def stop_scan(self):
        self.stop_flag = True
        self.status.config(text="Остановка...")

    def scan(self):
        for name, path in self.targets.items():
            if self.stop_flag:
                break
            self.root.after(0, lambda n=name: self.status.config(text=f"Смотрю: {n}"))
            size = get_folder_size(path)
            self.root.after(0, lambda n=name, s=size: self.update_size(n, s))
        self.root.after(0, self.scan_done)

    def update_size(self, name, size):
        if name in self.check_vars:
            _, label = self.check_vars[name]
            label.config(text=human_size(size) if size > 0 else "0 Б")

    def scan_done(self):
        self.scanning = False
        self.scan_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.clean_btn.config(state="normal")
        self.status.config(text=f"Анализ завершён. Отметь, что чистить. — {AUTHOR}")
        self.update_total()

    def update_total(self):
        total = 0
        for name, (var, label) in self.check_vars.items():
            if var.get():
                total += parse_size(label.cget("text"))
        self.total_label.config(text=f"Итого выбрано: {human_size(total)}")

    def toggle_all(self, value):
        for var, _ in self.check_vars.values():
            var.set(value)
        self.update_total()

    def clean_selected(self):
        selected = [(n, self.targets[n]) for n, (v, _) in self.check_vars.items() if v.get()]

        if not selected and not self.recycle_var.get() and not self.diskclean_var.get():
            messagebox.showinfo("Инфо", "Ничего не выбрано.")
            return

        total_files = 0
        total_freed = 0
        total_errors = 0
        log_lines = []

        for name, path in selected:
            deleted, errors, freed = clean_folder_contents(path)
            total_files += deleted
            total_errors += errors
            total_freed += freed
            log_lines.append(f"{name}: удалено {deleted}, ошибок {errors}, освобождено {human_size(freed)}")

        if self.recycle_var.get():
            ok, msg = empty_recycle_bin()
            if ok:
                log_lines.append("Корзина: очищена")
            else:
                log_lines.append(f"Корзина: ошибка ({msg})")

        # Автоматическая очистка диска Windows через cleanmgr
        if self.diskclean_var.get():
            self.status.config(text="Запускаю очистку дисков C: и D:...")
            self.root.update()
            profile = CONFIG.get("disk_cleanup_profile", 1)
            try:
                for drive in ["C:", "D:"]:
                    if os.path.exists(drive + "\\"):
                        subprocess.run(
                            ["cleanmgr", "/d", drive, f"/sagerun:{profile}"],
                            shell=True,
                            timeout=1800,
                            creationflags=0x08000000,
                        )
                        log_lines.append(f"Windows Disk Cleanup ({drive}): выполнен")
            except Exception as e:
                log_lines.append(f"Windows Disk Cleanup: ошибка ({e})")

        with open("cleaner_log.txt", "a", encoding="utf-8") as log:
            log.write(f"\n=== {datetime.now()} | by {AUTHOR} ===\n")
            log.write("\n".join(log_lines) + "\n")

        messagebox.showinfo("Готово",
                            f"Удалено объектов: {total_files}\n"
                            f"Ошибок: {total_errors}\n"
                            f"Освобождено: {human_size(total_freed)}\n\n"
                            f"Лог: cleaner_log.txt\n\n"
                            f"— {AUTHOR}")

        self.start_scan()

# ---------- ЗАСТАВКА ----------
def show_splash():
    splash = tk.Tk()
    splash.overrideredirect(True)
    splash.configure(bg="#1e1e1e")

    w, h = 400, 220
    screen_w = splash.winfo_screenwidth()
    screen_h = splash.winfo_screenheight()
    x = (screen_w - w) // 2
    y = (screen_h - h) // 2
    splash.geometry(f"{w}x{h}+{x}+{y}")

    tk.Label(splash, text="Чистильщик мусора PRO",
             font=("Segoe UI", 16, "bold"),
             fg="white", bg="#1e1e1e").pack(pady=(40, 5))

    tk.Label(splash, text=VERSION,
             font=("Segoe UI", 11),
             fg="#aaaaaa", bg="#1e1e1e").pack()

    tk.Label(splash, text=f"by {AUTHOR}",
             font=("Segoe UI", 13, "italic"),
             fg="#4ea1ff", bg="#1e1e1e").pack(pady=(20, 0))

    splash.after(2000, splash.destroy)
    splash.mainloop()

# ---------- ЗАПУСК ----------
if __name__ == "__main__":
    if os.name == "nt":
        hide_console()
        run_as_admin()
    show_splash()
    root = tk.Tk()
    app = CleanerApp(root)
    root.mainloop()