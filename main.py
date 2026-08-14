import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

from scanner import Scanner
from duplicate_engine import DuplicateEngine
from ui_components import DuplicateGroupCard

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("DupeX - Duplicate File Finder")
        self.geometry("900x600")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.selected_paths = set()
        self.engine = DuplicateEngine()

        self._setup_ui()

    def _setup_ui(self):
        # Left Panel (Sidebar)
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="DupeX", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.add_folder_btn = ctk.CTkButton(self.sidebar_frame, text="Add Folder", command=self.add_folder)
        self.add_folder_btn.grid(row=1, column=0, padx=20, pady=10)

        self.paths_listbox = tk.Listbox(self.sidebar_frame, bg=self.sidebar_frame._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"]), fg="white", highlightthickness=0, borderwidth=0)
        self.paths_listbox.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        
        self.clear_paths_btn = ctk.CTkButton(self.sidebar_frame, text="Clear Folders", command=self.clear_folders, fg_color="transparent", border_width=1, text_color=("gray10", "#DCE4EE"))
        self.clear_paths_btn.grid(row=3, column=0, padx=20, pady=10)

        # Min Size Option
        self.min_size_label = ctk.CTkLabel(self.sidebar_frame, text="Min File Size:")
        self.min_size_label.grid(row=4, column=0, padx=20, pady=(20, 0), sticky="w")
        
        self.min_size_var = ctk.StringVar(value="1 MB")
        self.min_size_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=["0 B", "1 KB", "100 KB", "1 MB", "10 MB", "100 MB"], variable=self.min_size_var)
        self.min_size_menu.grid(row=5, column=0, padx=20, pady=5, sticky="n")

        # Main View
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Top Bar (Filters)
        self.topbar = ctk.CTkFrame(self.main_frame, height=50)
        self.topbar.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        self.filter_vars = {}
        filters = ["Images", "Videos", "Audio", "Documents", "All Files"]
        for i, f in enumerate(filters):
            var = ctk.StringVar(value="on" if f == "All Files" else "off")
            self.filter_vars[f] = var
            cb = ctk.CTkCheckBox(self.topbar, text=f, variable=var, onvalue="on", offvalue="off", command=lambda f=f: self.on_filter_change(f))
            cb.pack(side="left", padx=10, pady=10)

        # Controls & Progress
        self.controls_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.controls_frame.grid(row=1, column=0, sticky="ew", padx=10)
        
        self.scan_btn = ctk.CTkButton(self.controls_frame, text="Start Scan", command=self.start_scan)
        self.scan_btn.pack(side="left", padx=10)
        
        self.progress_bar = ctk.CTkProgressBar(self.controls_frame, width=300)
        self.progress_bar.pack(side="left", padx=10, fill="x", expand=True)
        self.progress_bar.set(0)
        
        self.status_label = ctk.CTkLabel(self.controls_frame, text="Ready")
        self.status_label.pack(side="left", padx=10)

        # Results Area (Scrollable)
        self.results_scroll = ctk.CTkScrollableFrame(self.main_frame)
        self.results_scroll.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        
        self.result_cards = []

    def on_filter_change(self, changed_filter):
        if changed_filter == "All Files" and self.filter_vars["All Files"].get() == "on":
            for f, var in self.filter_vars.items():
                if f != "All Files":
                    var.set("off")
        elif changed_filter != "All Files" and self.filter_vars[changed_filter].get() == "on":
            self.filter_vars["All Files"].set("off")

    def add_folder(self):
        folder = filedialog.askdirectory()
        if folder and folder not in self.selected_paths:
            self.selected_paths.add(folder)
            self.paths_listbox.insert(tk.END, folder)

    def clear_folders(self):
        self.selected_paths.clear()
        self.paths_listbox.delete(0, tk.END)

    def _get_min_size_bytes(self):
        val = self.min_size_var.get()
        if "KB" in val: return int(val.replace(" KB", "")) * 1024
        if "MB" in val: return int(val.replace(" MB", "")) * 1024 * 1024
        return 0

    def start_scan(self):
        if not self.selected_paths:
            messagebox.showwarning("No Paths", "Please add at least one folder to scan.")
            return

        active_filters = [f for f, var in self.filter_vars.items() if var.get() == "on"]
        if not active_filters:
            messagebox.showwarning("No Filters", "Please select at least one file type to scan.")
            return

        self.scan_btn.configure(state="disabled")
        for card in self.result_cards:
            card.destroy()
        self.result_cards.clear()
        
        self.engine = DuplicateEngine()
        
        thread = threading.Thread(target=self._run_scan_thread, args=(active_filters,))
        thread.daemon = True
        thread.start()

    def update_progress_ui(self, message, progress=None):
        self.status_label.configure(text=message)
        if progress is not None:
            self.progress_bar.set(progress)
        self.update_idletasks()

    def _run_scan_thread(self, filters):
        min_size = self._get_min_size_bytes()
        scanner = Scanner(min_size_bytes=min_size)
        
        def ui_callback(msg):
            self.after(0, self.update_progress_ui, msg, 0) # Just indeterminate progress for now

        # Scan phase
        files_by_size, image_files = scanner.scan_directories(self.selected_paths, filters, ui_callback)
        
        # Exact duplicate phase
        def exact_prog(processed, total, msg):
            self.after(0, self.update_progress_ui, msg, processed / total if total else 0)
            
        exact_dupes = self.engine.find_exact_duplicates(files_by_size, exact_prog)
        
        self.after(0, self._show_results, exact_dupes)

    def _show_results(self, duplicates):
        self.update_progress_ui("Scan complete.", 1)
        self.scan_btn.configure(state="normal")
        
        if not duplicates:
            ctk.CTkLabel(self.results_scroll, text="No duplicates found!").pack(pady=20)
            return
            
        for group in duplicates:
            card = DuplicateGroupCard(self.results_scroll, group, self.handle_delete)
            card.pack(fill="x", pady=5)
            self.result_cards.append(card)

    def handle_delete(self, paths, card_widget):
        total_size = sum(os.path.getsize(p) for p in paths)
        size_str = DuplicateGroupCard.format_size(total_size)
        
        if messagebox.askyesno("Confirm Delete", f"Send {len(paths)} files ({size_str}) to the Recycle Bin?"):
            deleted = self.engine.delete_files(paths)
            messagebox.showinfo("Deleted", f"Successfully moved {deleted} files to the Recycle Bin.")
            card_widget.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()
