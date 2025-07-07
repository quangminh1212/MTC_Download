#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from extract_story import extract_story_content
from extract_story_batch import extract_all_html_files

class StoryExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Công Cụ Trích Xuất Nội Dung Truyện")
        self.root.geometry("700x500")
        self.root.resizable(True, True)
        
        # Thiết lập style
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, relief="flat", font=('Helvetica', 10))
        self.style.configure("TLabel", font=('Helvetica', 10))
        
        self.setup_ui()
    
    def setup_ui(self):
        # Frame chính
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Tab Control
        tab_control = ttk.Notebook(main_frame)
        
        # Tab 1: Trích xuất một file
        tab1 = ttk.Frame(tab_control)
        tab_control.add(tab1, text='Trích xuất một file')
        self.setup_tab1(tab1)
        
        # Tab 2: Trích xuất nhiều file
        tab2 = ttk.Frame(tab_control)
        tab_control.add(tab2, text='Trích xuất nhiều file')
        self.setup_tab2(tab2)
        
        # Tab 3: Xem file đã trích xuất
        tab3 = ttk.Frame(tab_control)
        tab_control.add(tab3, text='Xem file đã trích xuất')
        self.setup_tab3(tab3)
        
        tab_control.pack(expand=1, fill="both")
        
        # Thanh trạng thái
        self.status_var = tk.StringVar()
        self.status_var.set("Sẵn sàng")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_tab1(self, parent):
        # Frame chứa các thành phần
        frame = ttk.Frame(parent, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Mô tả
        desc_label = ttk.Label(frame, text="Trích xuất nội dung từ một file HTML và lưu thành file text", wraplength=600)
        desc_label.pack(pady=(0, 10), anchor="w")
        
        # Khung nhập file nguồn
        source_frame = ttk.LabelFrame(frame, text="File nguồn", padding="10")
        source_frame.pack(fill=tk.X, pady=5)
        
        self.source_var = tk.StringVar()
        source_entry = ttk.Entry(source_frame, textvariable=self.source_var, width=50)
        source_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        source_button = ttk.Button(source_frame, text="Chọn file", command=self.browse_source_file)
        source_button.pack(side=tk.RIGHT)
        
        # Khung nhập file đích
        target_frame = ttk.LabelFrame(frame, text="File đích (để trống để tạo tự động)", padding="10")
        target_frame.pack(fill=tk.X, pady=5)
        
        self.target_var = tk.StringVar()
        target_entry = ttk.Entry(target_frame, textvariable=self.target_var, width=50)
        target_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        target_button = ttk.Button(target_frame, text="Chọn file", command=self.browse_target_file)
        target_button.pack(side=tk.RIGHT)
        
        # Nút trích xuất
        extract_button = ttk.Button(frame, text="Trích xuất nội dung", command=self.extract_single_file)
        extract_button.pack(pady=10)
        
        # Kết quả
        result_frame = ttk.LabelFrame(frame, text="Kết quả", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.result_text = tk.Text(result_frame, wrap=tk.WORD, height=10)
        self.result_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=self.result_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.config(yscrollcommand=scrollbar.set)
    
    def setup_tab2(self, parent):
        # Frame chứa các thành phần
        frame = ttk.Frame(parent, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Mô tả
        desc_label = ttk.Label(frame, text="Trích xuất nội dung từ nhiều file HTML trong một thư mục", wraplength=600)
        desc_label.pack(pady=(0, 10), anchor="w")
        
        # Khung nhập thư mục nguồn
        source_frame = ttk.LabelFrame(frame, text="Thư mục nguồn", padding="10")
        source_frame.pack(fill=tk.X, pady=5)
        
        self.source_dir_var = tk.StringVar()
        source_dir_entry = ttk.Entry(source_frame, textvariable=self.source_dir_var, width=50)
        source_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        source_dir_button = ttk.Button(source_frame, text="Chọn thư mục", command=self.browse_source_dir)
        source_dir_button.pack(side=tk.RIGHT)
        
        # Khung nhập thư mục đích
        target_frame = ttk.LabelFrame(frame, text="Thư mục đích (để trống để sử dụng thư mục nguồn)", padding="10")
        target_frame.pack(fill=tk.X, pady=5)
        
        self.target_dir_var = tk.StringVar()
        target_dir_entry = ttk.Entry(target_frame, textvariable=self.target_dir_var, width=50)
        target_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        target_dir_button = ttk.Button(target_frame, text="Chọn thư mục", command=self.browse_target_dir)
        target_dir_button.pack(side=tk.RIGHT)
        
        # Tùy chọn kết hợp các file
        options_frame = ttk.Frame(frame)
        options_frame.pack(fill=tk.X, pady=5)
        
        self.combine_var = tk.BooleanVar(value=False)
        combine_check = ttk.Checkbutton(options_frame, text="Kết hợp tất cả file thành một file duy nhất", variable=self.combine_var)
        combine_check.pack(anchor="w")
        
        # Nút trích xuất
        extract_button = ttk.Button(frame, text="Trích xuất nội dung", command=self.extract_multiple_files)
        extract_button.pack(pady=10)
        
        # Kết quả
        result_frame = ttk.LabelFrame(frame, text="Kết quả", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.result_text2 = tk.Text(result_frame, wrap=tk.WORD, height=10)
        self.result_text2.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar2 = ttk.Scrollbar(result_frame, orient="vertical", command=self.result_text2.yview)
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text2.config(yscrollcommand=scrollbar2.set)
    
    def setup_tab3(self, parent):
        # Frame chứa các thành phần
        frame = ttk.Frame(parent, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Mô tả
        desc_label = ttk.Label(frame, text="Xem các file text đã trích xuất", wraplength=600)
        desc_label.pack(pady=(0, 10), anchor="w")
        
        # Khung chọn thư mục
        dir_frame = ttk.Frame(frame)
        dir_frame.pack(fill=tk.X, pady=5)
        
        dir_label = ttk.Label(dir_frame, text="Thư mục:")
        dir_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.view_dir_var = tk.StringVar(value=os.getcwd())
        dir_entry = ttk.Entry(dir_frame, textvariable=self.view_dir_var, width=50)
        dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        dir_button = ttk.Button(dir_frame, text="Chọn thư mục", command=self.browse_view_dir)
        dir_button.pack(side=tk.RIGHT)
        
        refresh_button = ttk.Button(dir_frame, text="Làm mới", command=self.refresh_file_list)
        refresh_button.pack(side=tk.RIGHT, padx=5)
        
        # Danh sách file và nội dung
        list_content_frame = ttk.Frame(frame)
        list_content_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Danh sách file
        list_frame = ttk.LabelFrame(list_content_frame, text="Danh sách file")
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))
        
        self.file_listbox = tk.Listbox(list_frame, width=30)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)
        
        list_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_listbox.yview)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=list_scrollbar.set)
        
        # Nội dung file
        content_frame = ttk.LabelFrame(list_content_frame, text="Nội dung")
        content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.content_text = tk.Text(content_frame, wrap=tk.WORD)
        self.content_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        content_scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=self.content_text.yview)
        content_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.content_text.config(yscrollcommand=content_scrollbar.set)
        
        # Làm mới danh sách file ban đầu
        self.refresh_file_list()
    
    def browse_source_file(self):
        file_path = filedialog.askopenfilename(
            title="Chọn file HTML",
            filetypes=(("HTML files", "*.html"), ("All files", "*.*"))
        )
        if file_path:
            self.source_var.set(file_path)
            # Tự động đề xuất tên file đầu ra
            output_file = os.path.splitext(file_path)[0] + ".txt"
            self.target_var.set(output_file)
    
    def browse_target_file(self):
        file_path = filedialog.asksaveasfilename(
            title="Chọn vị trí lưu file",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*")),
            defaultextension=".txt"
        )
        if file_path:
            self.target_var.set(file_path)
    
    def browse_source_dir(self):
        dir_path = filedialog.askdirectory(title="Chọn thư mục chứa file HTML")
        if dir_path:
            self.source_dir_var.set(dir_path)
    
    def browse_target_dir(self):
        dir_path = filedialog.askdirectory(title="Chọn thư mục lưu file kết quả")
        if dir_path:
            self.target_dir_var.set(dir_path)
    
    def browse_view_dir(self):
        dir_path = filedialog.askdirectory(title="Chọn thư mục chứa file text")
        if dir_path:
            self.view_dir_var.set(dir_path)
            self.refresh_file_list()
    
    def extract_single_file(self):
        source_file = self.source_var.get()
        target_file = self.target_var.get() or None
        
        if not source_file:
            messagebox.showerror("Lỗi", "Vui lòng chọn file HTML nguồn!")
            return
        
        self.status_var.set("Đang xử lý...")
        self.root.update_idletasks()
        
        # Sử dụng thread để tránh giao diện bị đóng băng
        def process():
            try:
                result = extract_story_content(source_file, target_file)
                if result:
                    self.result_text.delete(1.0, tk.END)
                    self.result_text.insert(tk.END, f"Đã trích xuất thành công và lưu vào: {result}\n")
                    self.status_var.set("Đã hoàn thành")
                else:
                    self.result_text.delete(1.0, tk.END)
                    self.result_text.insert(tk.END, "Trích xuất thất bại!\n")
                    self.status_var.set("Có lỗi xảy ra")
            except Exception as e:
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(tk.END, f"Lỗi: {str(e)}\n")
                self.status_var.set("Có lỗi xảy ra")
        
        threading.Thread(target=process).start()
    
    def extract_multiple_files(self):
        source_dir = self.source_dir_var.get()
        target_dir = self.target_dir_var.get() or None
        combine = self.combine_var.get()
        
        if not source_dir:
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục chứa file HTML!")
            return
        
        self.status_var.set("Đang xử lý...")
        self.root.update_idletasks()
        
        # Sử dụng thread để tránh giao diện bị đóng băng
        def process():
            try:
                self.result_text2.delete(1.0, tk.END)
                self.result_text2.insert(tk.END, f"Đang xử lý các file trong thư mục: {source_dir}\n")
                
                successful = extract_all_html_files(source_dir, target_dir, combine)
                
                self.result_text2.insert(tk.END, f"Đã trích xuất thành công {successful} file.\n")
                if successful > 0:
                    output_dir = target_dir or source_dir
                    self.result_text2.insert(tk.END, f"Các file đã được lưu vào: {output_dir}\n")
                    if combine:
                        combined_file = os.path.join(output_dir, "combined_story.txt")
                        self.result_text2.insert(tk.END, f"Đã kết hợp thành file: {combined_file}\n")
                
                self.status_var.set("Đã hoàn thành")
            except Exception as e:
                self.result_text2.insert(tk.END, f"Lỗi: {str(e)}\n")
                self.status_var.set("Có lỗi xảy ra")
        
        threading.Thread(target=process).start()
    
    def refresh_file_list(self):
        directory = self.view_dir_var.get()
        
        if not os.path.isdir(directory):
            messagebox.showerror("Lỗi", f"Thư mục '{directory}' không tồn tại!")
            return
        
        self.file_listbox.delete(0, tk.END)
        
        # Liệt kê tất cả các file .txt trong thư mục
        txt_files = [f for f in os.listdir(directory) if f.endswith('.txt')]
        txt_files.sort()
        
        for txt_file in txt_files:
            self.file_listbox.insert(tk.END, txt_file)
        
        self.content_text.delete(1.0, tk.END)
        self.content_text.insert(tk.END, f"Đã tìm thấy {len(txt_files)} file .txt trong thư mục này.\nChọn một file để xem nội dung.")
    
    def on_file_select(self, event):
        selection = self.file_listbox.curselection()
        if not selection:
            return
        
        file_name = self.file_listbox.get(selection[0])
        file_path = os.path.join(self.view_dir_var.get(), file_name)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.content_text.delete(1.0, tk.END)
            self.content_text.insert(tk.END, content)
        except Exception as e:
            self.content_text.delete(1.0, tk.END)
            self.content_text.insert(tk.END, f"Lỗi khi đọc file: {str(e)}")

def main():
    root = tk.Tk()
    app = StoryExtractorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 