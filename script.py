import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import os
from pathlib import Path                
from gif_parser import GifParser        

class GifViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("GIF Viewer")
        
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(padx=10, pady=10)
        
        self.controls_frame = tk.Frame(self.main_frame)
        self.controls_frame.pack(pady=5)
        
        self.select_button = tk.Button(self.controls_frame, text="Select GIF", command=self.select_file)
        self.select_button.pack(side=tk.LEFT, padx=5)
        
        self.pause_button = tk.Button(self.controls_frame, text="Pause", command=self.pause_gif)
        self.pause_button.pack(side=tk.LEFT, padx=5)
        self.play_button = tk.Button(self.controls_frame, text="Play", command=self.play_gif)
        self.play_button.pack(side=tk.LEFT, padx=5)
        
        self.size_frame = tk.Frame(self.controls_frame)
        self.size_frame.pack(side=tk.LEFT, padx=5)
        
        tk.Label(self.size_frame, text="Width:").pack(side=tk.LEFT)
        self.width_var = tk.StringVar()
        self.width_entry = tk.Entry(self.size_frame, textvariable=self.width_var, width=5)
        self.width_entry.pack(side=tk.LEFT, padx=2)
        
        tk.Label(self.size_frame, text="Height:").pack(side=tk.LEFT)
        self.height_var = tk.StringVar()
        self.height_entry = tk.Entry(self.size_frame, textvariable=self.height_var, width=5)
        self.height_entry.pack(side=tk.LEFT, padx=2)
        
        self.increase_button = tk.Button(self.controls_frame, text="+s", command=self.increase_size)
        self.increase_button.pack(side=tk.LEFT, padx=5)
        self.decrease_button = tk.Button(self.controls_frame, text="-s", command=self.decrease_size)
        self.decrease_button.pack(side=tk.LEFT, padx=5)
        
        self.label = tk.Label(self.main_frame)
        self.label.pack()
        
        self.info_text = tk.Text(self.main_frame, wrap=tk.NONE, height=20, width=80)
        self.info_text.pack(pady=5)
        
        self.current_gif = None
        self.frames = []
        self.current_frame = 0
        self.original_gif = None
        self.paused = False
        self.delays = []

    def select_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("GIF files", "*.gif")]
        )
        if file_path:
            self.file_path = file_path
            self.original_gif = Image.open(file_path)
            self.width_var.set(str(self.original_gif.width))
            self.height_var.set(str(self.original_gif.height))
            self.load_gif(self.original_gif)

    def load_gif(self, gif, size=None, start_frame=0):
        if size is None:
            orig_w, orig_h = self.original_gif.width, self.original_gif.height
            new_w, new_h = orig_w, orig_h
            if orig_w < 200 or orig_h < 200:
                new_w = max(orig_w, 200)
                new_h = max(orig_h, 200)
            if orig_w > 1000 or orig_h > 1000:
                new_w = min(orig_w, 1000)
                new_h = min(orig_h, 1000)
            size = (new_w, new_h)
            self.width_var.set(str(new_w))
            self.height_var.set(str(new_h))
        if self.current_gif:
            self.label.after_cancel(self.current_gif)
        
        self.frames = []
        self.delays = []
        
        try:
            while True:
                frame = gif.copy()
                if size:
                    frame = frame.resize(size, Image.Resampling.NEAREST)
                photo = ImageTk.PhotoImage(frame)
                self.frames.append(photo)
                delay = gif.info.get("duration", 100)
                self.delays.append(delay)
                gif.seek(len(self.frames))
        except EOFError:
            pass

        self.current_frame = start_frame % len(self.frames)
        self.animate_gif()
        self.update_info()

    def animate_gif(self):
        if self.frames:
            self.label.configure(image=self.frames[self.current_frame])
            
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            
            if not self.paused:
                self.current_gif = self.label.after(100, self.animate_gif)

    def pause_gif(self):
        if not self.paused:
            self.paused = True
            if self.current_gif:
                self.label.after_cancel(self.current_gif)
                self.current_gif = None

    def play_gif(self):
        if self.paused:
            self.paused = False
            self.animate_gif()

    def update_info(self):
        try:
            parser = GifParser(Path(self.file_path))
            parsed_info = parser.parse_file()
            info_text = "=== Parsed GIF Information ===\n"
            for section, entries in parsed_info.get("headers", {}).items():
                info_text += f"\n{section}:\n"
                for key, (value, desc) in entries.items():
                    info_text += f"  {key}: {value} ({desc})\n"
            frames = parsed_info.get("frames", [])
            info_text += "\n=== Frames Information ===\n"
            for idx, frame in enumerate(frames):
                info_text += f"Frame {idx+1}:\n"
                for key, value in frame.items():
                    info_text += f"  {key}: {value}\n"
        except Exception as e:
            info_text = f"Error parsing GIF info: {str(e)}"
            
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert(tk.END, info_text)

    def increase_size(self):
        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            new_width = int(width * 1.1)
            new_height = int(height * 1.1)
            self.width_var.set(str(new_width))
            self.height_var.set(str(new_height))
            self.load_gif(self.original_gif, size=(new_width, new_height))
        except ValueError:
            pass

    def decrease_size(self):
        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            new_width = max(1, int(width * 0.9))
            new_height = max(1, int(height * 0.9))
            self.width_var.set(str(new_width))
            self.height_var.set(str(new_height))
            self.load_gif(self.original_gif, size=(new_width, new_height))
        except ValueError:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = GifViewer(root)
    root.mainloop()
