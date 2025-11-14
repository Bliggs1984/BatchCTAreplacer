import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import queue
import os # Added for dynamic discovery
from video_processor import process_videos, check_nvenc_availability, check_ffmpeg_installed

# Create the main window
root = tk.Tk()
root.withdraw()  # Hide the main window until the check is complete

# Check if ffmpeg is installed
if not check_ffmpeg_installed():
    messagebox.showerror("Error", "FFmpeg not found. Please install FFmpeg and add it to your system's PATH.")
    root.destroy()
    exit()

root.deiconify()  # Show the main window if the check passes
root.title("Video Processor")

class ProgressWindow(tk.Toplevel):
    def __init__(self, parent, queue):
        super().__init__(parent)
        self.title("Processing Videos")
        self.geometry("300x100")
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(pady=20, padx=20, fill=tk.X)
        self.label_var = tk.StringVar()
        self.label = tk.Label(self, textvariable=self.label_var)
        self.label.pack()
        self.queue = queue
        self.processed_videos = 0
        self.total_videos = 0
        self.check_queue()

    def check_queue(self):
        try:
            message = self.queue.get_nowait()
            if message == "done":
                self.destroy()
                messagebox.showinfo("Complete", "Video processing completed!")
                return
            elif isinstance(message, int):
                self.total_videos = message
            else:
                self.processed_videos += 1
                self.update_progress(self.processed_videos, self.total_videos)
        except queue.Empty:
            pass
        self.after(100, self.check_queue)

    def update_progress(self, value, total):
        if total > 0:
            progress_percentage = (value / total) * 100
            self.progress_var.set(progress_percentage)
            self.label_var.set(f"Processed {value} of {total} videos")
            self.update_idletasks()

def select_main_videos():
    files = filedialog.askopenfilenames(title="Select main videos", filetypes=[("MP4 files", "*.mp4")])
    if files:
        main_videos_entry.delete(0, tk.END)
        main_videos_entry.insert(0, ", ".join(files))

def select_cta_folder():
    folder = filedialog.askdirectory(title="Select CTA folder")
    if folder:
        cta_folder_entry.delete(0, tk.END)
        cta_folder_entry.insert(0, folder)

def select_output_folder():
    folder = filedialog.askdirectory(title="Select output folder")
    if folder:
        output_folder_entry.delete(0, tk.END)
        output_folder_entry.insert(0, folder)

def run_process():
    main_videos = main_videos_entry.get().split(", ")
    cta_folder = cta_folder_entry.get()
    output_folder = output_folder_entry.get()
    overlay_duration = float(overlay_duration_entry.get())

    if not main_videos or not cta_folder or not output_folder:
        messagebox.showerror("Error", "Please select all required folders and files.")
        return

    # Dynamically discover languages and CTAs
    languages = [d for d in os.listdir(cta_folder) if os.path.isdir(os.path.join(cta_folder, d))]
    total_ctas = 0
    for lang in languages:
        lang_path = os.path.join(cta_folder, lang)
        total_ctas += len([d for d in os.listdir(lang_path) if os.path.isdir(os.path.join(lang_path, d))])

    use_gpu = use_gpu_var.get() and check_nvenc_availability()

    progress_queue = queue.Queue()
    ProgressWindow(root, progress_queue)

    def process_thread():
        total_videos = len(main_videos) * total_ctas
        progress_queue.put(total_videos)

        def progress_callback():
            progress_queue.put("progress")

        process_videos(main_videos, cta_folder, output_folder, overlay_duration, use_gpu, progress_callback)
        progress_queue.put("done")

    threading.Thread(target=process_thread, daemon=True).start()

def validate_numeric_input(P):
    if P.isdigit() or P == "":
        return True
    return False

vcmd = (root.register(validate_numeric_input), '%P')

# Create and pack widgets
root.columnconfigure(1, weight=1)

tk.Label(root, text="Main Videos:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
main_videos_entry = tk.Entry(root, width=50)
main_videos_entry.grid(row=0, column=1, sticky="we", padx=5, pady=5)
tk.Button(root, text="Select Main Videos", command=select_main_videos).grid(row=0, column=2, padx=5, pady=5)

tk.Label(root, text="CTA Folder:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
cta_folder_entry = tk.Entry(root, width=50)
cta_folder_entry.grid(row=1, column=1, sticky="we", padx=5, pady=5)
tk.Button(root, text="Select CTA Folder", command=select_cta_folder).grid(row=1, column=2, padx=5, pady=5)

tk.Label(root, text="CTA Duration (seconds):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
overlay_duration_entry = tk.Entry(root, width=10, validate="key", validatecommand=vcmd)
overlay_duration_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)
overlay_duration_entry.insert(0, "4")  # Default value

tk.Label(root, text="Output Folder:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
output_folder_entry = tk.Entry(root, width=50)
output_folder_entry.grid(row=3, column=1, sticky="we", padx=5, pady=5)
tk.Button(root, text="Select Output Folder", command=select_output_folder).grid(row=3, column=2, padx=5, pady=5)

use_gpu_var = tk.BooleanVar()
use_gpu_checkbox = tk.Checkbutton(root, text="Use GPU Acceleration (if available)", variable=use_gpu_var)
use_gpu_checkbox.grid(row=4, column=1, sticky="w", padx=5, pady=5)

tk.Button(root, text="Process Videos", command=run_process).grid(row=5, column=1, pady=10)

# Start the GUI event loop
root.mainloop()
