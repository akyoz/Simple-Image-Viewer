import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import os
import sys # 追加
import threading

class ImageViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tkinter Image Viewer")
        self.root.geometry("1200x800")

        # --- Style ---
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TFrame', background='#2e2e2e')
        self.style.configure('TButton', padding=6, relief='flat', background='#4a4a4a', foreground='white')
        self.style.map('TButton', background=[('active', '#6a6a6a')])
        self.style.configure('TLabel', background='#2e2e2e', foreground='white')
        self.style.configure('Treeview', rowheight=60, fieldbackground='#3c3c3c', background='#3c3c3c', foreground='white')
        self.style.configure('Treeview.Heading', background='#4a4a4a', foreground='white', relief='flat')
        self.style.map('Treeview.Heading', background=[('active', '#6a6a6a')])
        self.style.configure("Horizontal.TProgressbar", background='#6a6a6a', troughcolor='#2e2e2e')

        # --- Data ---
        self.image_info = []
        self.thumbnails = []

        # --- Layout ---
        self.main_frame = ttk.Frame(self.root, style='TFrame')
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.top_frame = ttk.Frame(self.main_frame, style='TFrame')
        self.top_frame.pack(fill=tk.X, padx=10, pady=5)

        self.content_frame = ttk.Frame(self.main_frame, style='TFrame')
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # --- Widgets ---
        self.select_button = ttk.Button(self.top_frame, text="フォルダを選択", command=self.select_folder_dialog)
        self.select_button.pack(side=tk.LEFT)

        self.status_label = ttk.Label(self.top_frame, text="フォルダを選択してください。", style='TLabel')
        self.status_label.pack(side=tk.LEFT, padx=10)

        self.progressbar = ttk.Progressbar(self.top_frame, orient='horizontal', mode='determinate', style="Horizontal.TProgressbar")

        # Treeview for table display
        self.tree_frame = ttk.Frame(self.content_frame)
        self.tree_frame.grid(row=0, column=0, sticky='nswe', padx=(0, 5))
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            self.tree_frame, 
            columns=('num', 'name', 'folder', 'size'),
            show='headings'
        )
        self.tree.grid(row=0, column=0, sticky='nswe')

        self.tree.heading('num', text='番号')
        self.tree.heading('name', text='ファイル名')
        self.tree.heading('folder', text='フォルダ')
        self.tree.heading('size', text='サイズ')

        self.tree.column('num', width=50, anchor='center')
        self.tree.column('name', width=250)
        self.tree.column('folder', width=150)
        self.tree.column('size', width=100, anchor='e')

        self.scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.scrollbar.grid(row=0, column=1, sticky='ns')
        self.tree.config(yscrollcommand=self.scrollbar.set)

        # Image Preview Label
        self.preview_label = ttk.Label(self.content_frame, text="画像プレビュー", style='TLabel', anchor=tk.CENTER)
        self.preview_label.grid(row=0, column=1, sticky='nswe', padx=(5, 0))

        # --- Bindings ---
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        self.tree.bind('<Double-1>', self.show_full_size_image)
        self.tree.bind('<Return>', self.show_full_size_image)

    def select_folder_dialog(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.load_folder(folder_path)

    def load_folder(self, folder_path):
        self.clear_tree()
        self.progressbar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.status_label.config(text="ファイル数を計算中...")
        self.root.update_idletasks() # Ensure UI updates before starting thread
        threading.Thread(target=self.load_images_thread, args=(folder_path,), daemon=True).start()

    def format_size(self, size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.1f} KB"
        else:
            return f"{size_bytes/1024**2:.1f} MB"

    def load_images_thread(self, folder_path):
        supported = (".png", ".jpg", ".jpeg", ".gif", ".bmp")
        thumb_size = (50, 50)

        paths_to_process = []
        for root, _, files in os.walk(folder_path):
            for f in files:
                if f.lower().endswith(supported):
                    paths_to_process.append(os.path.join(root, f))
        
        total_files = len(paths_to_process)
        if total_files == 0:
            self.root.after(0, self.populate_tree, [])
            return

        self.root.after(0, self.progressbar.config, {'maximum': total_files, 'value': 0})

        image_info_list = []
        for i, path in enumerate(paths_to_process):
            try:
                img = Image.open(path)
                img.thumbnail(thumb_size, Image.Resampling.LANCZOS)
                info = {
                    'num': i + 1,
                    'path': path,
                    'name': os.path.basename(path),
                    'folder': os.path.basename(os.path.dirname(path)),
                    'size': self.format_size(os.path.getsize(path)),
                    'thumb': img
                }
                image_info_list.append(info)

                if (i + 1) % 10 == 0 or (i + 1) == total_files:
                    self.root.after(0, self.update_progress, i + 1, total_files)
            except Exception as e:
                print(f"Error processing {path}: {e}")
        
        self.root.after(0, self.populate_tree, image_info_list)

    def clear_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.image_info = []
        self.thumbnails = []

    def update_progress(self, value, total):
        self.progressbar['value'] = value
        self.status_label.config(text=f"読み込み中... {value} / {total}")

    def populate_tree(self, image_info_list):
        self.clear_tree()
        self.progressbar.pack_forget()
        self.image_info = image_info_list
        self.thumbnails = [ImageTk.PhotoImage(info['thumb']) for info in self.image_info]

        for i, info in enumerate(self.image_info):
            self.tree.insert(
                '', 
                'end', 
                iid=i, 
                image=self.thumbnails[i],
                values=(info['num'], info['name'], info['folder'], info['size'])
            )
        
        if self.image_info:
            self.status_label.config(text=f"{len(self.image_info)} 個の画像が見つかりました。")
            self.tree.selection_set('0')
            self.tree.focus_set()
            self.tree.focus('0')
        else:
            self.status_label.config(text="選択されたフォルダに画像は見つかりませんでした。")

    def on_tree_select(self, event=None):
        selection = self.tree.selection()
        if not selection:
            return
        
        selected_index = int(selection[0])
        image_path = self.image_info[selected_index]['path']

        try:
            image = Image.open(image_path)
            w, h = image.size
            max_w = self.preview_label.winfo_width()
            max_h = self.preview_label.winfo_height()
            if max_w < 50 or max_h < 50: max_w, max_h = 800, 600

            ratio = min(max_w/w, max_h/h)
            new_w, new_h = int(w * ratio), int(h * ratio)

            resized_image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
            photo_image = ImageTk.PhotoImage(resized_image)
            
            self.preview_label.config(image=photo_image, text="")
            self.preview_label.image = photo_image
        except Exception as e:
            self.preview_label.config(image=None, text=f"プレビューの読み込みエラー:\n{e}")

    def show_full_size_image(self, event=None):
        selection = self.tree.selection()
        if not selection:
            return
        
        initial_index = int(selection[0])

        top = tk.Toplevel(self.root)
        top.configure(bg='black')
        top.attributes('-fullscreen', True)
        top.focus_set()

        self.current_fullscreen_index = initial_index
        self.fullscreen_photo_ref = None
        self.hide_overlay_timer = None

        img_label = tk.Label(top, bg='black')
        img_label.pack(expand=True)

        top_overlay = tk.Frame(top, bg='#000000', bd=0)
        bottom_overlay = tk.Frame(top, bg='#000000', bd=0)

        filename_label = tk.Label(top_overlay, text="", bg="#000000", fg="white", font=("Segoe UI", 12))
        filename_label.pack(side=tk.LEFT, padx=10, pady=5)
        count_label = tk.Label(top_overlay, text="", bg="#000000", fg="white", font=("Segoe UI", 12))
        count_label.pack(side=tk.RIGHT, padx=10, pady=5)

        sequence_scale = ttk.Scale(bottom_overlay, from_=0, to=len(self.image_info)-1, orient='horizontal')
        sequence_scale.pack(fill=tk.X, expand=True, padx=10, pady=5)

        prev_button = tk.Button(top, text="<", bg="#202020", fg="white", font=("Segoe UI", 16, 'bold'), bd=0, relief='flat', activebackground='#404040')
        next_button = tk.Button(top, text=">", bg="#202020", fg="white", font=("Segoe UI", 16, 'bold'), bd=0, relief='flat', activebackground='#404040')

        def update_fullscreen_image(update_scale=True):
            image_path = self.image_info[self.current_fullscreen_index]['path']
            filename = os.path.basename(image_path)
            top.title(filename)
            try:
                img = Image.open(image_path)
                screen_w, screen_h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
                w, h = img.size
                ratio = min(screen_w / w, screen_h / h)
                new_w, new_h = int(w * ratio), int(h * ratio)
                
                resized_image = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                self.fullscreen_photo_ref = ImageTk.PhotoImage(resized_image)
                img_label.config(image=self.fullscreen_photo_ref)

                filename_label.config(text=filename)
                count_label.config(text=f"{self.current_fullscreen_index + 1} / {len(self.image_info)}")
                if update_scale:
                    sequence_scale.set(self.current_fullscreen_index)

            except Exception as e:
                top.destroy()
                from tkinter import messagebox
                messagebox.showerror("画像エラー", f"画像の読み込み中にエラーが発生しました:\n{e}")

        def next_image(e=None):
            if self.current_fullscreen_index < len(self.image_info) - 1:
                self.current_fullscreen_index += 1
                update_fullscreen_image()

        def prev_image(e=None):
            if self.current_fullscreen_index > 0:
                self.current_fullscreen_index -= 1
                update_fullscreen_image()

        def seek_image(value):
            index = int(float(value))
            if self.current_fullscreen_index != index:
                self.current_fullscreen_index = index
                update_fullscreen_image(update_scale=False)

        def close_fullscreen(e=None):
            if self.hide_overlay_timer:
                top.after_cancel(self.hide_overlay_timer)
            top.destroy()

        def show_overlay(e=None):
            top_overlay.place(relx=0, rely=0, relwidth=1, height=40)
            bottom_overlay.place(relx=0, rely=1, anchor='sw', relwidth=1, height=40)
            prev_button.place(relx=0, rely=0.5, anchor='w', width=50, height=100)
            next_button.place(relx=1, rely=0.5, anchor='e', width=50, height=100)
            
            if self.hide_overlay_timer:
                top.after_cancel(self.hide_overlay_timer)
            self.hide_overlay_timer = top.after(2500, hide_overlay)

        def hide_overlay():
            top_overlay.place_forget()
            bottom_overlay.place_forget()
            prev_button.place_forget()
            next_button.place_forget()

        def on_mouse_wheel(event):
            if event.num == 5 or event.delta < 0: next_image()
            elif event.num == 4 or event.delta > 0: prev_image()

        sequence_scale.config(command=seek_image)
        prev_button.config(command=prev_image)
        next_button.config(command=next_image)

        top.bind('<Motion>', show_overlay)
        top.bind('<Escape>', close_fullscreen)
        top.bind('<space>', close_fullscreen)
        top.bind('<Return>', close_fullscreen)
        img_label.bind('<Button-1>', close_fullscreen)

        top.bind('<Right>', next_image)
        top.bind('<Down>', next_image)
        top.bind('<Left>', prev_image)
        top.bind('<Up>', prev_image)
        
        top.bind('<MouseWheel>', on_mouse_wheel)
        top.bind('<Button-4>', on_mouse_wheel)
        top.bind('<Button-5>', on_mouse_wheel)

        update_fullscreen_image()
        show_overlay()

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageViewerApp(root)

    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
        if os.path.isdir(folder_path):
            root.after(100, lambda: app.load_folder(folder_path))
        else:
            print(f"エラー: 指定されたパスは有効なディレクトリではありません: {folder_path}")

    root.mainloop()
