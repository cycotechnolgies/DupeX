import os
import datetime
import customtkinter as ctk
from PIL import Image

class DuplicateGroupCard(ctk.CTkFrame):
    def __init__(self, master, duplicate_group, on_delete_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.duplicate_group = duplicate_group # List of file paths
        self.on_delete_callback = on_delete_callback
        self.checkboxes = []
        self.thumbnails = []
        
        self._setup_ui()

    def _setup_ui(self):
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(10, 0))
        
        group_size = os.path.getsize(self.duplicate_group[0]) if self.duplicate_group else 0
        size_str = self.format_size(group_size)
        
        title_label = ctk.CTkLabel(header_frame, text=f"Identical Files ({size_str} each)", font=ctk.CTkFont(weight="bold"))
        title_label.pack(side="left")
        
        auto_select_btn = ctk.CTkButton(header_frame, text="Select All but Newest", width=120, height=24, command=self.auto_select)
        auto_select_btn.pack(side="right", padx=5)
        
        delete_btn = ctk.CTkButton(header_frame, text="Delete Selected", width=100, height=24, fg_color="#D32F2F", hover_color="#B71C1C", command=self.on_delete)
        delete_btn.pack(side="right", padx=5)
        
        keep_btn = ctk.CTkButton(header_frame, text="Keep Both", width=80, height=24, fg_color="transparent", border_width=1, command=self.destroy)
        keep_btn.pack(side="right", padx=5)

        # Files List
        self.files_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.files_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        for path in self.duplicate_group:
            self._add_file_row(path)

    def _add_file_row(self, path):
        row = ctk.CTkFrame(self.files_frame, fg_color="transparent")
        row.pack(fill="x", pady=2)
        
        var = ctk.StringVar(value="off")
        cb = ctk.CTkCheckBox(row, text="", variable=var, onvalue="on", offvalue="off", width=24)
        cb.pack(side="left")
        self.checkboxes.append((cb, var, path))
        
        # Try to load thumbnail if image
        ext = os.path.splitext(path)[1].lower()
        if ext in {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}:
            try:
                img = Image.open(path)
                img.thumbnail((40, 40))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(40, 40))
                self.thumbnails.append(ctk_img) # keep reference
                img_label = ctk.CTkLabel(row, image=ctk_img, text="")
                img_label.pack(side="left", padx=5)
            except Exception:
                pass
        
        info_frame = ctk.CTkFrame(row, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, padx=5)
        
        name_label = ctk.CTkLabel(info_frame, text=os.path.basename(path), anchor="w")
        name_label.pack(fill="x")
        
        try:
            mtime = os.path.getmtime(path)
            date_str = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        except OSError:
            date_str = "Unknown date"
            
        path_label = ctk.CTkLabel(info_frame, text=f"{os.path.dirname(path)} | {date_str}", font=ctk.CTkFont(size=10), text_color="gray", anchor="w")
        path_label.pack(fill="x")

    def auto_select(self):
        """Selects all files except the most recently modified one."""
        if not self.duplicate_group:
            return
            
        # Sort paths by modification time descending (newest first)
        def get_mtime(p):
            try: return os.path.getmtime(p)
            except OSError: return 0
            
        sorted_paths = sorted(self.duplicate_group, key=get_mtime, reverse=True)
        newest_path = sorted_paths[0] if sorted_paths else None
        
        for cb, var, path in self.checkboxes:
            if path != newest_path:
                cb.select()
            else:
                cb.deselect()

    def on_delete(self):
        selected_paths = [path for cb, var, path in self.checkboxes if var.get() == "on"]
        if selected_paths:
            self.on_delete_callback(selected_paths, self)

    @staticmethod
    def format_size(size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
