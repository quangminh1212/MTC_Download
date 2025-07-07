import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ..core.downloader import download_chapter, download_multiple_chapters
from ..core.extractor import extract_story_content, extract_all_html_files


class MtcDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MTC Downloader")
        self.root.geometry("800x600")
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(root)
        
        # Create tabs
        self.download_tab = ttk.Frame(self.notebook)
        self.extract_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.download_tab, text="Tải truyện")
        self.notebook.add(self.extract_tab, text="Trích xuất")
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Setup download tab
        self._setup_download_tab()
        
        # Setup extract tab
        self._setup_extract_tab()
    
    def _setup_download_tab(self):
        # URL input frame
        url_frame = ttk.LabelFrame(self.download_tab, text="URL truyện")
        url_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(url_frame, text="URL:").grid(row=0, column=0, padx=5, pady=5)
        self.url_entry = ttk.Entry(url_frame, width=70)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Options frame
        options_frame = ttk.LabelFrame(self.download_tab, text="Tùy chọn")
        options_frame.pack(fill="x", padx=10, pady=5)
        
        # Download type
        ttk.Label(options_frame, text="Chế độ tải:").grid(row=0, column=0, padx=5, pady=5)
        self.download_type = tk.StringVar(value="single")
        ttk.Radiobutton(options_frame, text="Một chương", variable=self.download_type, 
                        value="single").grid(row=0, column=1, padx=5, pady=5)
        ttk.Radiobutton(options_frame, text="Nhiều chương", variable=self.download_type, 
                        value="multiple").grid(row=0, column=2, padx=5, pady=5)
        ttk.Radiobutton(options_frame, text="Tất cả chương", variable=self.download_type, 
                        value="all").grid(row=0, column=3, padx=5, pady=5)
        
        # Number of chapters
        ttk.Label(options_frame, text="Số chương:").grid(row=1, column=0, padx=5, pady=5)
        self.num_chapters = ttk.Spinbox(options_frame, from_=1, to=100, width=5)
        self.num_chapters.set(1)
        self.num_chapters.grid(row=1, column=1, padx=5, pady=5)
        
        # Combine option
        self.combine_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Kết hợp thành một file", 
                        variable=self.combine_var).grid(row=1, column=2, padx=5, pady=5, columnspan=2)
        
        # Output directory
        ttk.Label(options_frame, text="Thư mục lưu:").grid(row=2, column=0, padx=5, pady=5)
        self.output_dir = ttk.Entry(options_frame, width=50)
        self.output_dir.insert(0, os.path.join(os.getcwd(), "downloads"))
        self.output_dir.grid(row=2, column=1, padx=5, pady=5, columnspan=2)
        ttk.Button(options_frame, text="Chọn...", command=self._select_output_dir).grid(
            row=2, column=3, padx=5, pady=5)
        
        # Download button
        ttk.Button(self.download_tab, text="Tải truyện", 
                   command=self._download_story).pack(pady=20)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(self.download_tab, text="Tiến trình")
        progress_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.progress = ttk.Progressbar(progress_frame, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=10)
        
        self.status_text = tk.Text(progress_frame, height=10, wrap="word")
        self.status_text.pack(fill="both", expand=True, padx=10, pady=10)
        
    def _setup_extract_tab(self):
        # Input frame
        input_frame = ttk.LabelFrame(self.extract_tab, text="Input")
        input_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(input_frame, text="HTML File/Folder:").grid(row=0, column=0, padx=5, pady=5)
        self.input_path = ttk.Entry(input_frame, width=50)
        self.input_path.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(input_frame, text="Chọn...", 
                   command=self._select_input_path).grid(row=0, column=2, padx=5, pady=5)
        
        # Extract options
        options_frame = ttk.LabelFrame(self.extract_tab, text="Tùy chọn")
        options_frame.pack(fill="x", padx=10, pady=5)
        
        self.extract_combine_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Kết hợp thành một file", 
                        variable=self.extract_combine_var).pack(padx=5, pady=5)
        
        # Output directory
        ttk.Label(options_frame, text="Thư mục lưu:").pack(side="left", padx=5, pady=5)
        self.extract_output_dir = ttk.Entry(options_frame, width=40)
        self.extract_output_dir.insert(0, os.path.join(os.getcwd(), "extractions"))
        self.extract_output_dir.pack(side="left", padx=5, pady=5)
        ttk.Button(options_frame, text="Chọn...", 
                   command=self._select_extract_output_dir).pack(side="left", padx=5, pady=5)
        
        # Extract button
        ttk.Button(self.extract_tab, text="Trích xuất", 
                   command=self._extract_story).pack(pady=20)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(self.extract_tab, text="Tiến trình")
        progress_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.extract_progress = ttk.Progressbar(progress_frame, orient="horizontal", mode="determinate")
        self.extract_progress.pack(fill="x", padx=10, pady=10)
        
        self.extract_status_text = tk.Text(progress_frame, height=10, wrap="word")
        self.extract_status_text.pack(fill="both", expand=True, padx=10, pady=10)
    
    def _select_output_dir(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir.delete(0, tk.END)
            self.output_dir.insert(0, directory)
    
    def _select_extract_output_dir(self):
        directory = filedialog.askdirectory()
        if directory:
            self.extract_output_dir.delete(0, tk.END)
            self.extract_output_dir.insert(0, directory)
    
    def _select_input_path(self):
        path = filedialog.askopenfilename(filetypes=[("HTML files", "*.html"), ("All files", "*.*")])
        if not path:  # User canceled or no selection
            path = filedialog.askdirectory()
        
        if path:
            self.input_path.delete(0, tk.END)
            self.input_path.insert(0, path)
    
    def _log_message(self, message, text_widget):
        text_widget.insert(tk.END, f"{message}\n")
        text_widget.see(tk.END)
    
    def _download_story(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Lỗi", "Vui lòng nhập URL truyện")
            return
        
        output_dir = self.output_dir.get().strip()
        combine = self.combine_var.get()
        download_type = self.download_type.get()
        delay = 2  # Mặc định delay 2 giây
        
        self.status_text.delete(1.0, tk.END)
        self.progress["value"] = 0
        
        try:
            if download_type == "single":
                self._log_message(f"Đang tải chương từ {url}...", self.status_text)
                download_chapter(url, output_dir)
                self.progress["value"] = 100
                self._log_message("Tải thành công!", self.status_text)
                
            elif download_type == "multiple":
                num = int(self.num_chapters.get())
                self._log_message(f"Đang tải {num} chương từ {url}...", self.status_text)
                download_multiple_chapters(url, num, output_dir, delay, combine)
                self.progress["value"] = 100
                self._log_message("Tải thành công!", self.status_text)
                
            elif download_type == "all":
                self._log_message(f"Đang tải tất cả chương từ {url}...", self.status_text)
                # This would be implemented in the downloader module
                self._log_message("Tính năng này chưa được hỗ trợ", self.status_text)
                
            messagebox.showinfo("Thành công", "Đã tải truyện thành công!")
                
        except Exception as e:
            self._log_message(f"Lỗi: {str(e)}", self.status_text)
            messagebox.showerror("Lỗi", str(e))
    
    def _extract_story(self):
        input_path = self.input_path.get().strip()
        if not input_path:
            messagebox.showwarning("Lỗi", "Vui lòng chọn file HTML hoặc thư mục")
            return
        
        output_dir = self.extract_output_dir.get().strip()
        combine = self.extract_combine_var.get()
        
        self.extract_status_text.delete(1.0, tk.END)
        self.extract_progress["value"] = 0
        
        try:
            if os.path.isfile(input_path):
                self._log_message(f"Đang trích xuất từ {input_path}...", self.extract_status_text)
                extract_story_content(input_path, output_dir)
                self.extract_progress["value"] = 100
                self._log_message("Trích xuất thành công!", self.extract_status_text)
                
            elif os.path.isdir(input_path):
                self._log_message(f"Đang trích xuất từ thư mục {input_path}...", self.extract_status_text)
                extract_all_html_files(input_path, output_dir, combine)
                self.extract_progress["value"] = 100
                self._log_message("Trích xuất thành công!", self.extract_status_text)
                
            messagebox.showinfo("Thành công", "Đã trích xuất thành công!")
                
        except Exception as e:
            self._log_message(f"Lỗi: {str(e)}", self.extract_status_text)
            messagebox.showerror("Lỗi", str(e))


def run_gui():
    """Run the GUI application"""
    root = tk.Tk()
    app = MtcDownloaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui() 