import os
import sys
import shutil
import hashlib
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import threading

# 设置主题颜色
BG_COLOR = "#f0f0f0"
BUTTON_COLOR = "#4CAF50"
TEXT_COLOR = "#333333"

# --- 文件处理函数 ---

def calculate_file_hash(file_path):
    """计算文件的SHA-256哈希值"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def process_files_recursive(source_folder, target_folder, file_extensions, operation="复制", progress_callback=None, log_callback=None):
    """
    递归遍历源文件夹，将指定类型的文件复制或移动到目标文件夹，并记录日志。
    """
    moved_files = []  # 移动或复制的文件
    skipped_files = []  # 跳过的文件

    # 确保目标文件夹存在
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    # 创建日志文件名，包含日期和时间
    log_filename = datetime.now().strftime("operation_log_%Y-%m-%d_%H-%M-%S.txt")
    log_path = os.path.join(target_folder, log_filename)  # 日志保存到目标文件夹

    # 获取需处理的总文件数
    all_files = [
        os.path.join(root, file)
        for root, _, files in os.walk(source_folder)
        for file in files if file.endswith(file_extensions)
    ]

    # 如果没有找到文件，直接返回
    if not all_files:
        start_button.config(state="normal")  # 重新启用按钮 (在多线程中无法直接操作 Tkinter 控件)
        messagebox.showinfo("提示", "源路径下没有找到指定类型的文件。")
        return

    # 写入日志
    with open(log_path, "w", encoding="utf-8") as log:
        # 写入总体信息
        log.write("=== 文件操作日志 ===\n")
        log.write(f"源路径：{source_folder}\n")
        log.write(f"目标路径：{target_folder}\n")
        log.write(f"操作类型：{operation}\n")
        log.write(f"总文件数：{len(all_files)} 个\n")
        log.write("\n=== 文件处理详情 ===\n")

    # 初始化进度条
    if progress_callback:
        progress_callback(0, len(all_files), "")

    # 缓存目标文件的哈希值
    target_file_hashes = {}

    for index, source_path in enumerate(all_files):
        filename = os.path.basename(source_path)
        target_path = os.path.join(target_folder, filename)

        if os.path.exists(target_path):
            if target_path not in target_file_hashes:
                target_file_hashes[target_path] = calculate_file_hash(target_path)
            source_hash = calculate_file_hash(source_path)
            if source_hash == target_file_hashes[target_path]:
                skipped_files.append(filename)
                # 写入日志
                with open(log_path, "a", encoding="utf-8") as log:
                    log.write(f"[跳过] 文件已存在且内容相同: {filename}\n")
                if log_callback:
                    log_callback(f"[跳过] 文件已存在且内容相同: {filename}\n")
            else:
                base, ext = os.path.splitext(filename)
                counter = 1
                new_target_path = os.path.join(target_folder, f"{base}_{counter}{ext}")
                while os.path.exists(new_target_path):
                    counter += 1
                    new_target_path = os.path.join(target_folder, f"{base}_{counter}{ext}")
                # 复制或移动文件
                if operation == "复制":
                    shutil.copy2(source_path, new_target_path)
                    moved_files.append(f"{filename} -> {os.path.basename(new_target_path)}")
                    # 写入日志
                    with open(log_path, "a", encoding="utf-8") as log:
                        log.write(f"[复制] {filename} 重命名为 {os.path.basename(new_target_path)}\n")
                    if log_callback:
                        log_callback(f"[复制] {filename} 重命名为 {os.path.basename(new_target_path)}\n")
                else:  # 移动
                    shutil.move(source_path, new_target_path)
                    moved_files.append(f"{filename} -> {os.path.basename(new_target_path)}")
                    # 写入日志
                    with open(log_path, "a", encoding="utf-8") as log:
                        log.write(f"[移动] {filename} 重命名为 {os.path.basename(new_target_path)}\n")
                    if log_callback:
                        log_callback(f"[移动] {filename} 重命名为 {os.path.basename(new_target_path)}\n")
        else:
            # 复制或移动文件
            if operation == "复制":
                shutil.copy2(source_path, target_path)
                moved_files.append(filename)
                # 写入日志
                with open(log_path, "a", encoding="utf-8") as log:
                    log.write(f"[复制] {filename}\n")
                if log_callback:
                    log_callback(f"[复制] {filename}\n")
            else:  # 移动
                shutil.move(source_path, target_path)
                moved_files.append(filename)
                # 写入日志
                with open(log_path, "a", encoding="utf-8") as log:
                    log.write(f"[移动] {filename}\n")
                if log_callback:
                    log_callback(f"[移动] {filename}\n")

        # 更新进度条
        if progress_callback:
            progress_callback(index + 1, len(all_files), filename)

    # 写入统计信息到日志文件
    with open(log_path, "a", encoding="utf-8") as log:
        log.write("\n=== 统计信息 ===\n")
        log.write(f"- 处理文件：{len(moved_files)} 个\n")
        log.write(f"- 跳过文件：{len(skipped_files)} 个\n")

    # 显示操作结果
    messagebox.showinfo("操作完成", f"文件操作已完成。\n日志文件已保存：\n  - {log_path}")

# --- GUI 部分 ---

# 配置
FILE_TYPES = [
    ".pdf", ".docx", ".xlsx", ".pptx", ".jpg", ".jpeg", ".png",
    ".gif", ".mp4", ".mp3", ".zip", ".rar", ".txt", ".csv",
    ".html", ".css", ".js", ".py", ".java", ".c", ".cpp",
    ".exe", ".dll", ".ini", ".log", ".json", ".xml", ".sql",
    ".ppt", ".xls", ".md"
]


def select_source_folder():
    folder = filedialog.askdirectory()
    if folder:
        source_folder_var.set(folder)

def select_target_folder():
    folder = filedialog.askdirectory()
    if folder:
        target_folder_var.set(folder)

def start_processing():
    source_folder = source_folder_var.get()
    target_folder = target_folder_var.get()
    custom_extensions = custom_extensions_var.get().strip()
    operation = operation_var.get()

    if not source_folder or not target_folder:
        messagebox.showerror("错误", "请选择源路径和目标路径")
        return

    # 禁用“开始处理”按钮
    start_button.config(state="disabled")
    status_bar.config(text="正在处理...")

    # 获取复选框选中的文件扩展名
    selected_extensions = [ext for ext, var in file_type_checkbox_vars.items() if var.get()]

    # 处理自定义文件扩展名
    if custom_extensions:
        custom_extensions_list = [ext.strip() for ext in custom_extensions.split(",") if ext.strip()]
        selected_extensions.extend(custom_extensions_list)

    if not selected_extensions:
        messagebox.showerror("错误", "请选择至少一个文件类型或输入自定义扩展名")
        start_button.config(state="normal")  # 重新启用按钮
        return

    file_extensions = tuple(selected_extensions)

    # 初始化进度条
    progress_bar["maximum"] = 100
    progress_bar["value"] = 0
    progress_label.config(text="等待开始...")
    log_text.delete(1.0, tk.END)  # 清空日志文本框

    # 使用多线程处理文件操作
    threading.Thread(target=process_files_recursive, args=(
        source_folder,
        target_folder,
        file_extensions,
        operation,
        lambda current, total, filename: update_progress(current, total, filename),
        lambda message: log_callback(message)
    )).start()

def update_progress(current, total, filename):
    """更新进度条和标签"""
    if total > 0:
        progress_bar["value"] = (current / total) * 100
    progress_label.config(text=f"处理中：{filename} ({current}/{total})")

def clear_log():
    log_text.delete(1.0, tk.END)

def open_log_folder():
    if os.path.exists(target_folder_var.get()):
        os.startfile(target_folder_var.get())
    else:
        messagebox.showerror("错误", "目标路径不存在")

def log_callback(message):
    log_text.insert(tk.END, message + "\n")
    log_text.see(tk.END)  # 自动滚动到底部

def show_about():
    about_message = """
    FileMover
    版本: 1.0.0
    作者: 沧浪之水
    邮箱: liucan01234@gmail.com
    GitHub: https://github.com/Liu8Can
    """
    messagebox.showinfo("关于", about_message)

def resource_path(relative_path):
    """获取打包后的资源文件的绝对路径"""
    try:
        base_path = sys._MEIPASS  # PyInstaller 打包后的临时文件夹
    except AttributeError:
        base_path = os.path.abspath(".")  # 开发环境中的当前文件夹
    return os.path.join(base_path, relative_path)

# 创建主窗口
root = tk.Tk()
root.title("FileMover v1.0")
root.geometry("800x680")  # 调整窗口大小
root.configure(bg=BG_COLOR)

# 设置窗口图标
icon_path = resource_path("icon.ico")  # 获取图标文件的路径
root.iconbitmap(icon_path)  # 设置窗口图标

# 设置窗口居中
window_width = 800
window_height = 680
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = (screen_width // 2) - (window_width // 2)
y = (screen_height // 2) - (window_height // 2)
root.geometry(f"{window_width}x{window_height}+{x}+{y}")

# 创建变量
source_folder_var = tk.StringVar()
target_folder_var = tk.StringVar()
custom_extensions_var = tk.StringVar()
operation_var = tk.StringVar(value="复制")
file_type_checkbox_vars = {ext: tk.BooleanVar() for ext in FILE_TYPES}

# 创建界面组件
top_frame = ttk.Frame(root)
top_frame.pack(padx=10, pady=10, fill="x")  # 使用 pack 布局

bottom_frame = ttk.Frame(root)
bottom_frame.pack(padx=10, pady=10, fill="both", expand=True)  # 填充并展开

# 顶部组件
ttk.Label(top_frame, text="源路径:", font=("", 10, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="e")
ttk.Entry(top_frame, textvariable=source_folder_var, width=60).grid(row=0, column=1, padx=5, pady=5)
ttk.Button(top_frame, text="浏览...", command=select_source_folder).grid(row=0, column=2, padx=5, pady=5)

ttk.Label(top_frame, text="目标路径:", font=("", 10, "bold")).grid(row=1, column=0, padx=5, pady=5, sticky="e")
ttk.Entry(top_frame, textvariable=target_folder_var, width=60).grid(row=1, column=1, padx=5, pady=5)
ttk.Button(top_frame, text="浏览...", command=select_target_folder).grid(row=1, column=2, padx=5, pady=5)

# 文件类型复选框
ttk.Label(top_frame, text="文件类型:", font=("", 10, "bold")).grid(row=2, column=0, padx=5, pady=5, sticky="ne")
file_types_frame = ttk.Frame(top_frame)
file_types_frame.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky="w")

# 将文件类型分成多列
for i, ext in enumerate(FILE_TYPES):
    row = i // 4
    col = i % 4
    ttk.Checkbutton(file_types_frame, text=ext, variable=file_type_checkbox_vars[ext]).grid(row=row, column=col, padx=5, pady=2, sticky="w")

# 自定义文件扩展名输入框
ttk.Label(top_frame, text="自定义文件扩展名（用逗号分隔）:", font=("", 10, "bold")).grid(row=3, column=0, padx=5, pady=5, sticky="e")
ttk.Entry(top_frame, textvariable=custom_extensions_var, width=60).grid(row=3, column=1, padx=5, pady=5)
ttk.Label(top_frame, text="例如：.jpg, .png, .mp4", font=("", 8)).grid(row=4, column=1, padx=5, pady=0, sticky="w")

# 操作类型下拉菜单
ttk.Label(top_frame, text="操作类型:", font=("", 10, "bold")).grid(row=5, column=0, padx=5, pady=5, sticky="e")
ttk.Combobox(top_frame, textvariable=operation_var, values=["复制", "移动"], state="readonly", width=17).grid(row=5, column=1, padx=5, pady=5, sticky="w")

# 进度条
progress_bar = ttk.Progressbar(top_frame, orient="horizontal", length=400, mode="determinate")
progress_bar.grid(row=6, column=1, padx=5, pady=10)

# 进度标签
progress_label = ttk.Label(top_frame, text="等待开始...", font=("", 9))
progress_label.grid(row=7, column=1, padx=5, pady=5)

# 按钮区域
button_frame = ttk.Frame(top_frame)
button_frame.grid(row=8, column=1, pady=10)

# 开始处理按钮
start_button = ttk.Button(button_frame, text="开始处理", command=start_processing)
start_button.pack(side="left", padx=5)

# 清除日志按钮
clear_button = ttk.Button(button_frame, text="清除日志", command=clear_log)
clear_button.pack(side="left", padx=5)

# 打开日志文件夹按钮
open_log_button = ttk.Button(button_frame, text="打开日志文件夹", command=open_log_folder)
open_log_button.pack(side="left", padx=5)

# 底部日志文本框
log_text = scrolledtext.ScrolledText(bottom_frame, wrap=tk.WORD, font=("Consolas", 10))
log_text.pack(fill="both", expand=True)

# 状态栏
status_bar = ttk.Label(root, text="就绪", relief="sunken", anchor="w", font=("", 9))
status_bar.pack(side="bottom", fill="x")

# 在界面中添加“关于”按钮
about_button = ttk.Button(button_frame, text="关于", command=show_about)
about_button.pack(side="left", padx=5)

# 运行主循环
root.mainloop()