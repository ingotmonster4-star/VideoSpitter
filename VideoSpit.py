import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import os
import threading
import time
import sys
import traceback
import subprocess

# --- Auto-Installer Logic ---
def install_dependencies():
    print("🛠️  Checking dependencies...")
    try:
        import cv2
        print("✅ OpenCV found.")
    except ImportError:
        print("⚠️  OpenCV missing! Attempting auto-install...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "opencv-python"])
            print("✅ Successfully installed opencv-python!")
            import cv2
        except Exception as e:
            print(f"❌ Auto-install failed: {e}")
            print("👉 Please manually run: pip install opencv-python")
            input("Press Enter to exit...")
            sys.exit()

install_dependencies()
import cv2 # Final import after potential install

class FrameReaperStudio:
    def __init__(self, root):
        self.root = root
        self.root.title("Frame Reaper // STUDIO EDITION v2")
        self.root.geometry("900x650")
        self.root.configure(bg="#121212")
        self.root.resizable(True, True)

        # Style Configuration for a premium look
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except:
            pass # Fallback if system doesn't support clam
        
        # Custom colors
        self.colors = {
            "bg": "#121212",
            "panel": "#1e1e1e",
            "input": "#2d2d2d",
            "text": "#e0e0e0",
            "accent": "#00ff99",
            "accent_hover": "#00cc7a",
            "warn": "#ffbb00",
            "err": "#ff4444"
        }

        self.style.configure("TProgressbar", thickness=15, troughcolor=self.colors['input'], background=self.colors['accent'])
        self.style.configure("TFrame", background=self.colors['bg'])
        self.style.configure("Dark.TLabel", background=self.colors['panel'], foreground=self.colors['text'])
        
        # State Variables
        self.queue_items = []
        
        # FIX: Use Desktop as the default path to avoid System32 permission errors
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "Reaper_Output")
        self.output_base_path = tk.StringVar(value=desktop_path)
        
        self.processing = False
        self.stop_signal = False
        
        # Settings Variables
        self.skip_val = tk.IntVar(value=1)
        self.format_val = tk.StringVar(value="png")
        self.quality_val = tk.IntVar(value=95)
        self.resize_enable = tk.BooleanVar(value=False)
        self.resize_width = tk.IntVar(value=1920)
        self.resize_height = tk.IntVar(value=1080)
        self.auto_folder = tk.BooleanVar(value=True)

        self._build_ui()

    def _build_ui(self):
        # --- Main Layout ---
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        header = tk.Frame(main_container, bg=self.colors['bg'])
        header.pack(fill="x", pady=(0, 20))
        tk.Label(header, text="FRAME REAPER", font=("Impact", 24), fg=self.colors['accent'], bg=self.colors['bg']).pack(side="left")
        tk.Label(header, text="// STUDIO EDITION", font=("Consolas", 12), fg="#666", bg=self.colors['bg']).pack(side="left", padx=10, pady=(12,0))

        # Content Split (Left: Queue, Right: Settings/Log)
        content_split = tk.Frame(main_container, bg=self.colors['bg'])
        content_split.pack(fill="both", expand=True)

        # --- LEFT PANEL: QUEUE ---
        left_panel = tk.Frame(content_split, bg=self.colors['panel'], width=400)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        left_panel.pack_propagate(False)

        # Queue Header
        q_header = tk.Frame(left_panel, bg=self.colors['panel'])
        q_header.pack(fill="x", padx=10, pady=10)
        tk.Label(q_header, text="JOB QUEUE", font=("Arial", 10, "bold"), fg="#fff", bg=self.colors['panel']).pack(side="left")
        
        # Queue Buttons
        btn_frame = tk.Frame(left_panel, bg=self.colors['panel'])
        btn_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        self._make_btn(btn_frame, "+ Add Files", self.add_files).pack(side="left", fill="x", expand=True, padx=(0,2))
        self._make_btn(btn_frame, "+ Add Folder", self.add_folder).pack(side="left", fill="x", expand=True, padx=2)
        self._make_btn(btn_frame, "Clear", self.clear_queue, bg="#444").pack(side="left", fill="x", expand=True, padx=(2,0))

        # Queue Listbox
        self.queue_list = tk.Listbox(left_panel, bg=self.colors['input'], fg="white", selectbackground=self.colors['accent'], selectforeground="black", relief="flat", font=("Consolas", 9))
        self.queue_list.pack(fill="both", expand=True, padx=10, pady=5)

        # Output Path Config
        out_frame = tk.Frame(left_panel, bg=self.colors['panel'])
        out_frame.pack(fill="x", padx=10, pady=10)
        tk.Label(out_frame, text="Base Output Folder:", fg="#aaa", bg=self.colors['panel'], font=("Arial", 8)).pack(anchor="w")
        
        out_box = tk.Frame(out_frame, bg=self.colors['panel'])
        out_box.pack(fill="x", pady=2)
        tk.Entry(out_box, textvariable=self.output_base_path, bg=self.colors['input'], fg="white", relief="flat").pack(side="left", fill="x", expand=True)
        tk.Button(out_box, text="...", command=self.browse_output, bg="#444", fg="white", relief="flat", width=3).pack(side="right", padx=(5,0))
        
        tk.Checkbutton(out_frame, text="Create subfolder per video", variable=self.auto_folder, bg=self.colors['panel'], fg="#ccc", selectcolor=self.colors['panel'], activebackground=self.colors['panel']).pack(anchor="w")

        # --- RIGHT PANEL: SETTINGS & LOGS ---
        right_panel = tk.Frame(content_split, bg=self.colors['bg'], width=350)
        right_panel.pack(side="right", fill="both", padx=(10, 0))
        
        # Settings Group
        settings_frame = tk.LabelFrame(right_panel, text="CONFIGURATION", bg=self.colors['panel'], fg="#aaa", font=("Arial", 9, "bold"), relief="flat")
        settings_frame.pack(fill="x", ipadx=10, ipady=10)

        # 1. Extraction Settings
        tk.Label(settings_frame, text="Frame Skip (Every Nth):", bg=self.colors['panel'], fg="white").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        tk.Spinbox(settings_frame, from_=1, to=1000, textvariable=self.skip_val, width=5, bg=self.colors['input'], fg="white", buttonbackground="#444").grid(row=0, column=1, sticky="w")

        # 2. Format Settings
        tk.Label(settings_frame, text="Output Format:", bg=self.colors['panel'], fg="white").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        fmt_box = tk.Frame(settings_frame, bg=self.colors['panel'])
        fmt_box.grid(row=1, column=1, sticky="w")
        ttk.Radiobutton(fmt_box, text="PNG", variable=self.format_val, value="png").pack(side="left", padx=(0,10))
        ttk.Radiobutton(fmt_box, text="JPG", variable=self.format_val, value="jpg").pack(side="left")

        # 3. Quality
        tk.Label(settings_frame, text="Quality (JPG only):", bg=self.colors['panel'], fg="white").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        tk.Scale(settings_frame, from_=10, to=100, variable=self.quality_val, orient="horizontal", bg=self.colors['panel'], fg="white", highlightthickness=0, length=120).grid(row=2, column=1, sticky="w")

        # 4. Resize Settings
        tk.Checkbutton(settings_frame, text="Force Resize", variable=self.resize_enable, bg=self.colors['panel'], fg="white", selectcolor=self.colors['panel'], activebackground=self.colors['panel']).grid(row=3, column=0, sticky="w", padx=10, pady=5)
        res_box = tk.Frame(settings_frame, bg=self.colors['panel'])
        res_box.grid(row=3, column=1, sticky="w")
        tk.Entry(res_box, textvariable=self.resize_width, width=5, bg=self.colors['input'], fg="white", relief="flat").pack(side="left")
        tk.Label(res_box, text="x", bg=self.colors['panel'], fg="#aaa").pack(side="left", padx=2)
        tk.Entry(res_box, textvariable=self.resize_height, width=5, bg=self.colors['input'], fg="white", relief="flat").pack(side="left")

        # Console Log
        log_label = tk.Label(right_panel, text="SYSTEM LOG", font=("Arial", 9, "bold"), fg="#aaa", bg=self.colors['bg'])
        log_label.pack(anchor="w", pady=(15, 5))
        
        self.log_text = scrolledtext.ScrolledText(right_panel, height=10, bg=self.colors['input'], fg="#00ff00", font=("Consolas", 8), state="disabled", relief="flat")
        self.log_text.pack(fill="both", expand=True)

        # --- BOTTOM ACTION BAR ---
        action_bar = tk.Frame(self.root, bg=self.colors['panel'], height=80)
        action_bar.pack(side="bottom", fill="x")
        
        # Progress Bars
        prog_frame = tk.Frame(action_bar, bg=self.colors['panel'])
        prog_frame.pack(fill="x", padx=20, pady=(10, 0))
        
        self.lbl_current = tk.Label(prog_frame, text="Idle", bg=self.colors['panel'], fg="white", font=("Arial", 9))
        self.lbl_current.pack(anchor="w")
        
        self.prog_bar = ttk.Progressbar(prog_frame, orient="horizontal", mode="determinate", style="TProgressbar")
        self.prog_bar.pack(fill="x", pady=2)
        
        self.lbl_overall = tk.Label(prog_frame, text="Batch Progress: 0/0", bg=self.colors['panel'], fg="#888", font=("Arial", 8))
        self.lbl_overall.pack(anchor="e")

        # Big Buttons
        btn_box = tk.Frame(action_bar, bg=self.colors['panel'])
        btn_box.pack(fill="x", padx=20, pady=10)
        
        self.btn_start = tk.Button(btn_box, text="START BATCH", command=self.start_processing, bg=self.colors['accent'], fg="#121212", font=("Arial", 11, "bold"), relief="flat")
        self.btn_start.pack(side="right", ipadx=20, ipady=5)
        
        self.btn_stop = tk.Button(btn_box, text="ABORT", command=self.stop_processing, bg=self.colors['err'], fg="white", font=("Arial", 11, "bold"), relief="flat", state="disabled")
        self.btn_stop.pack(side="right", padx=10, ipadx=10, ipady=5)

    def _make_btn(self, parent, text, cmd, bg=None):
        color = bg if bg else "#333"
        return tk.Button(parent, text=text, command=cmd, bg=color, fg="white", relief="flat", font=("Arial", 9), activebackground="#555")

    # --- Thread Safe Logging ---
    def log(self, msg, level="info"):
        # Schedule the UI update on the main thread
        # Also print to terminal for the homie who likes CMD
        print(f"[{level.upper()}] {msg}")
        self.root.after(0, lambda: self._log_internal(msg, level))

    def _log_internal(self, msg, level):
        self.log_text.config(state="normal")
        tag = "INFO"
        color = "#00ff00"
        
        if level == "warn": 
            tag = "WARN"
            color = self.colors['warn']
        elif level == "error": 
            tag = "ERR"
            color = self.colors['err']
            
        timestamp = time.strftime("[%H:%M:%S]")
        self.log_text.insert("end", f"{timestamp} {tag}: {msg}\n")
        
        # Colorize the last line
        end_index = self.log_text.index("end-1c")
        start_index = self.log_text.index(f"{end_index} linestart")
        
        self.log_text.tag_add(level, start_index, end_index)
        self.log_text.tag_config(level, foreground=color)
        
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    # --- File Operations ---
    def add_files(self):
        files = filedialog.askopenfilenames(filetypes=[("Video Files", "*.mp4 *.avi *.mov *.mkv *.flv")])
        for f in files:
            if f not in self.queue_items:
                self.queue_items.append(f)
                self.queue_list.insert("end", os.path.basename(f))
        self.log(f"Added {len(files)} files to queue.")

    def add_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            count = 0
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.flv')):
                        full_path = os.path.join(root, file)
                        if full_path not in self.queue_items:
                            self.queue_items.append(full_path)
                            self.queue_list.insert("end", file)
                            count += 1
            self.log(f"Scanned folder. Added {count} videos.")

    def clear_queue(self):
        self.queue_items = []
        self.queue_list.delete(0, "end")
        self.log("Queue cleared.", "warn")

    def browse_output(self):
        d = filedialog.askdirectory()
        if d: self.output_base_path.set(d)

    # --- Core Logic ---
    def start_processing(self):
        if not self.queue_items:
            messagebox.showwarning("Empty Queue", "Feed me some files first.")
            return
        
        if self.processing: return

        self.processing = True
        self.stop_signal = False
        self.btn_start.config(state="disabled", bg="#444")
        self.btn_stop.config(state="normal")
        
        threading.Thread(target=self.process_queue, daemon=True).start()

    def stop_processing(self):
        if self.processing:
            self.stop_signal = True
            self.log("Stopping after current file...", "warn")

    def process_queue(self):
        total_files = len(self.queue_items)
        base_out = self.output_base_path.get()
        
        try:
            skip = self.skip_val.get()
            fmt = self.format_val.get()
            quality = self.quality_val.get()
            do_resize = self.resize_enable.get()
            r_w = self.resize_width.get()
            r_h = self.resize_height.get()
            use_subfolder = self.auto_folder.get()
        except Exception as e:
            self.log(f"Config Error: {e}", "error")
            self.root.after(0, self.finish_batch)
            return

        if not os.path.exists(base_out):
            try:
                os.makedirs(base_out)
            except Exception as e:
                self.log(f"Critical: Cannot create output dir: {e}", "error")
                self.root.after(0, self.finish_batch)
                return

        for idx, video_path in enumerate(self.queue_items):
            if self.stop_signal:
                self.log("Batch aborted by user.", "warn")
                break

            filename = os.path.basename(video_path)
            self.root.after(0, lambda t=f"Processing: {filename}": self.lbl_current.config(text=t))
            self.root.after(0, lambda i=idx+1, t=total_files: self.lbl_overall.config(text=f"Batch Progress: {i}/{t}"))
            
            if use_subfolder:
                safe_name = os.path.splitext(filename)[0]
                video_out_dir = os.path.join(base_out, safe_name)
            else:
                video_out_dir = base_out

            if not os.path.exists(video_out_dir):
                os.makedirs(video_out_dir, exist_ok=True)

            self.log(f"Starting: {filename}")
            
            try:
                cap = cv2.VideoCapture(video_path)
                if not cap.isOpened():
                    self.log(f"Failed to open {filename}. Skipping.", "error")
                    continue

                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                if total_frames <= 0: total_frames = 1
                
                count = 0
                saved = 0
                
                while True:
                    if self.stop_signal: break
                    
                    success, frame = cap.read()
                    if not success:
                        break
                    
                    if count % skip == 0:
                        if do_resize:
                            try:
                                frame = cv2.resize(frame, (r_w, r_h), interpolation=cv2.INTER_AREA)
                            except Exception as e:
                                self.log(f"Resize failed on frame {count}: {e}", "error")
                        
                        out_name = os.path.join(video_out_dir, f"frame_{count:08d}.{fmt}")
                        if fmt == "jpg":
                            cv2.imwrite(out_name, frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
                        else:
                            cv2.imwrite(out_name, frame, [int(cv2.IMWRITE_PNG_COMPRESSION), 3])
                        saved += 1
                        
                    count += 1
                    if count % 20 == 0:
                        progress = (count / total_frames) * 100
                        self.root.after(0, lambda v=progress: self.prog_bar.config(value=v))

                cap.release()
                self.log(f"Finished {filename}: {saved} frames extracted.", "info")
                
            except Exception as e:
                self.log(f"Crash on {filename}: {e}", "error")

        self.root.after(0, self.finish_batch)

    def finish_batch(self):
        self.processing = False
        self.btn_start.config(state="normal", bg=self.colors['accent'])
        self.btn_stop.config(state="disabled")
        self.lbl_current.config(text="Idle")
        self.prog_bar.config(value=0)
        messagebox.showinfo("Studio Report", "Batch processing complete.")

if __name__ == "__main__":
    # --- Fail-Safe Startup ---
    try:
        root = tk.Tk()
        app = FrameReaperStudio(root)
        root.mainloop()
    except Exception:
        print("\n\n🔥 FATAL ERROR DURING EXECUTION 🔥")
        traceback.print_exc()
        print("\n👉 Press Enter to exit the program...")
        input()