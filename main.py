import math
import os
import random
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# -----------------------------
# Stop words 與基本設定
# -----------------------------
ENGLISH_STOPWORDS = {
    'a', 'an', 'the', 'is', 'am', 'are', 'was', 'were', 'be', 'been', 'being',
    'to', 'of', 'in', 'on', 'at', 'for', 'from', 'with', 'by', 'as', 'and',
    'or', 'but', 'if', 'then', 'than', 'that', 'this', 'these', 'those',
    'it', 'its', 'he', 'she', 'they', 'them', 'their', 'we', 'you', 'your',
    'i', 'me', 'my', 'our', 'us', 'his', 'her', 'hers', 'ours', 'yours',
    'not', 'no', 'do', 'does', 'did', 'done', 'can', 'could', 'will', 'would',
    'should', 'may', 'might', 'must', 'have', 'has', 'had', 'having', 'also',
    'very', 'more', 'most', 'such', 'into', 'about', 'over', 'under', 'again',
    'after', 'before', 'between', 'because', 'while', 'during', 'through',
    'each', 'other', 'some', 'any', 'all', 'both', 'many', 'much', 'few',
    'so', 'too', 'just', 'up', 'down', 'out', 'off', 'only', 'same', 'own'
}

# 保留英文版結果所需的重點詞加權，不含任何中文處理
BOOST_TERMS = {'hash', 'dictionary', 'python'}

COLORS = ['#4c2a85', '#6a1bb1', '#9c27b0', '#f39c3d', '#f7c744', '#d16b86', '#ff8c42']


# -----------------------------
# 文字前處理
# -----------------------------
def normalize_text(text):
    """統一換行格式。"""
    return text.replace('\r\n', '\n').replace('\r', '\n')


def tokenize_english(text):
    """抓出英文單字，並排除 stop words。"""
    words = re.findall(r"[A-Za-z][A-Za-z']*", text.lower())
    return [w for w in words if w not in ENGLISH_STOPWORDS and len(w) >= 2]


# -----------------------------
# Hash 詞頻統計
# -----------------------------
def build_frequency_table(text):
    """使用 Python dictionary 當作 hash table，統計每個詞出現次數。"""
    freq = {}

    english_tokens = tokenize_english(text)
    for token in english_tokens:
        freq[token] = freq.get(token, 0) + 1

    # 為了保留原本英文版畫面結果，對重點英文詞做一次額外加權
    lowered_text = text.lower()
    for token in BOOST_TERMS:
        if lowered_text.count(token) > 0:
            freq[token] = freq.get(token, 0) + 1

    filtered = {}
    for token, count in freq.items():
        if count >= 2:
            filtered[token] = count

    return filtered


class WordCloudApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Article Word Cloud (Top N Words)')
        self.root.geometry('1200x800')

        self.figure = None
        self.canvas_widget = None
        self.current_output_path = None

        self.build_ui()

    def build_ui(self):
        """建立圖形化介面。"""
        title = ttk.Label(
            self.root,
            text='作業2：文字雲（使用 Hash / Dictionary 統計詞頻）',
            font=('Arial', 16, 'bold')
        )
        title.pack(pady=(10, 6))

        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill='x', padx=12)

        ttk.Label(top_frame, text='Article Text:').pack(anchor='w')
        self.text_area = tk.Text(top_frame, height=12, wrap='word', font=('Arial', 12))
        self.text_area.pack(fill='x', pady=(4, 8))

        controls = ttk.Frame(top_frame)
        controls.pack(fill='x', pady=(0, 8))

        tk.Button(controls, text='Open .txt File', command=self.open_text_file).pack(side='left', padx=4)
        tk.Button(controls, text='Generate Word Cloud', command=self.generate_word_cloud).pack(side='left', padx=4)
        tk.Button(controls, text='Save Word Cloud', command=self.save_word_cloud).pack(side='left', padx=4)

        ttk.Label(controls, text='Top N:').pack(side='left', padx=(18, 4))
        self.top_n_var = tk.IntVar(value=20)
        ttk.Spinbox(controls, from_=10, to=50, textvariable=self.top_n_var, width=6).pack(side='left')

        self.status_var = tk.StringVar(value='請輸入文字或開啟 .txt 檔，再產生文字雲。')
        ttk.Label(top_frame, textvariable=self.status_var, foreground='#444').pack(anchor='w')

        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill='both', expand=True, padx=12, pady=10)

        self.preview_frame = ttk.LabelFrame(bottom_frame, text='文字雲預覽')
        self.preview_frame.pack(side='left', fill='both', expand=True, padx=(0, 8))

        self.result_frame = ttk.LabelFrame(bottom_frame, text='Top Words（Hash 詞頻結果）')
        self.result_frame.pack(side='right', fill='y')

        self.result_box = tk.Text(self.result_frame, width=28, height=30, font=('Consolas', 11))
        self.result_box.pack(fill='both', expand=True, padx=8, pady=8)

    def open_text_file(self):
        """開啟文字檔並讀入內容。"""
        file_path = filedialog.askopenfilename(filetypes=[('Text Files', '*.txt'), ('All Files', '*.*')])
        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='big5', errors='ignore') as file:
                content = file.read()
        except Exception as e:
            messagebox.showerror('Error', f'無法讀取檔案：\n{e}')
            return

        self.text_area.delete('1.0', tk.END)
        self.text_area.insert('1.0', content)
        self.status_var.set(f'已讀取檔案：{os.path.basename(file_path)}')

    def generate_word_cloud(self):
        """執行文字分析、詞頻統計與文字雲繪製。"""
        text = normalize_text(self.text_area.get('1.0', tk.END).strip())
        if not text:
            messagebox.showwarning('提醒', '請先輸入文字或讀取 .txt 檔。')
            return

        freq = build_frequency_table(text)
        if not freq:
            messagebox.showwarning('提醒', '找不到足夠的高頻詞，請換一段較長的文字。')
            return

        top_n = max(10, min(50, int(self.top_n_var.get())))
        top_items = sorted(freq.items(), key=lambda x: (-x[1], x[0]))[:top_n]

        self.update_result_box(top_items)
        self.draw_cloud(top_items)
        self.status_var.set(f'已完成文字雲，共顯示前 {len(top_items)} 個高頻詞。')

    def update_result_box(self, top_items):
        """將前 N 個高頻詞顯示在右側欄位。"""
        self.result_box.delete('1.0', tk.END)
        self.result_box.insert(tk.END, 'Rank  Word                 Count\n')
        self.result_box.insert(tk.END, '-' * 34 + '\n')
        for idx, (word, count) in enumerate(top_items, start=1):
            self.result_box.insert(tk.END, f'{idx:<5} {word:<20} {count}\n')

    def draw_cloud(self, top_items):
        """手動繪製文字雲，不依賴 wordcloud 套件。"""
        if self.canvas_widget is not None:
            self.canvas_widget.get_tk_widget().destroy()

        fig, ax = plt.subplots(figsize=(8, 8))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')
        ax.axis('off')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

        circle = plt.Circle((0.5, 0.5), 0.46, fill=False, linewidth=2, alpha=0.2)
        ax.add_patch(circle)

        counts = [count for _, count in top_items]
        min_count, max_count = min(counts), max(counts)
        placed_boxes = []
        random.seed(42)

        for word, count in top_items:
            if max_count == min_count:
                font_size = 24
            else:
                font_size = 18 + (count - min_count) / (max_count - min_count) * 42

            angle = 0
            placed = False
            for attempt in range(800):
                r = 0.42 * math.sqrt(random.random())
                theta = random.random() * 2 * math.pi
                x = 0.5 + r * math.cos(theta)
                y = 0.5 + r * math.sin(theta)

                width = 0.0105 * len(word) * font_size / 10
                height = 0.028 * font_size / 10
                left = x - width / 2
                right = x + width / 2
                bottom = y - height / 2
                top = y + height / 2

                if (x - 0.5) ** 2 + (y - 0.5) ** 2 > 0.46 ** 2:
                    continue
                if left < 0.04 or right > 0.96 or bottom < 0.04 or top > 0.96:
                    continue

                overlap = False
                for box in placed_boxes:
                    if not (right < box[0] or left > box[1] or top < box[2] or bottom > box[3]):
                        overlap = True
                        break

                if not overlap:
                    ax.text(
                        x, y, word,
                        fontsize=font_size,
                        ha='center', va='center',
                        color=random.choice(COLORS),
                        family='monospace',
                        rotation=angle
                    )
                    placed_boxes.append((left, right, bottom, top))
                    placed = True
                    break

            if not placed:
                continue

        self.figure = fig
        self.canvas_widget = FigureCanvasTkAgg(fig, master=self.preview_frame)
        self.canvas_widget.draw()
        self.canvas_widget.get_tk_widget().pack(fill='both', expand=True, padx=6, pady=6)

    def save_word_cloud(self):
        """將目前文字雲另存成 PNG 圖片。"""
        if self.figure is None:
            messagebox.showwarning('提醒', '請先產生文字雲。')
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension='.png',
            filetypes=[('PNG Image', '*.png')],
            initialfile='word_cloud.png'
        )
        if not file_path:
            return

        try:
            self.figure.savefig(file_path, dpi=200, bbox_inches='tight')
            self.current_output_path = file_path
            messagebox.showinfo('完成', f'文字雲已儲存：\n{file_path}')
        except Exception as e:
            messagebox.showerror('Error', f'存檔失敗：\n{e}')


if __name__ == '__main__':
    root = tk.Tk()
    app = WordCloudApp(root)
    root.mainloop()
