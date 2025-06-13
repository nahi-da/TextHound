import os
os.chdir(os.path.dirname(__file__))
try:
    from search_text_cui import walk_dir
except ImportError:
    from pathlib import Path
    import sys
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--rerun", action="store_true")
    args = parser.parse_args()

    os.chdir(os.path.dirname(__file__))
    # 仮想環境で実行されていない場合、仮想環境で再実行する
    if not args.rerun:
        def find_exec_dir(directory):
            for root, dirs, files in os.walk(directory):
                if "activate" in files:
                    return Path(os.path.abspath(root))
        exec_dir = find_exec_dir(os.path.dirname(__file__))
        if sys.platform == "win32":
            os.execl(exec_dir.joinpath("python.exe"), f"-u {__file__} --rerun")
        elif sys.platform == "linux":
            os.execl(exec_dir.joinpath("python3"), f"-u {__file__} --rerun")
except Exception as e:
    import traceback
    input("\n".join(traceback.TracebackException.from_exception(e).format()))
else:
    import sys

# from multiprocessing import Process
from threading import Thread
from tkinter import ttk, filedialog
import tkinter as tk
import time


WIN_TITLE = "文字列検索ツール"
ENTRY1_WIDTH = 60
ENTRY2_WIDTH = 45
FRAME_IGNORE_DIR_HEIGHT = 150
FRAME_KEYWORD_HEIGHT = 150
BUTTON1_WIDTH = 5
MODE_VALUES = ("OR", "AND")
IGNORE_DIR = ("venv", ".pyenv", ".conda", "site-packages")
STATUS_TEXT = ("準備完了", "検索中")
DEFAULT_FONT_NAME = "Noto Sans JP"


class SearchLine(object):
    def __init__(self):
        if sys.platform == "win32":
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        else:
            pass
        
        # 検索結果保存用
        self.matching_files = list()

        # entry保存用リスト
        self.entries_keywords = list()
        self.entries_ignore_dirs = list()

        self.root = tk.Tk()
        # テーマファイルがあるか確認
        if os.path.exists(f"{os.path.dirname(__file__)}/azure.tcl"):
            self.root.tk.call("source", "azure.tcl")
            self.root.tk.call("set_theme", "dark")

        # 背景をクリックしたら、Entryからフォーカスを外す
        self.root.bind("<Button-1>", self.focus_root)
        self.root.title(WIN_TITLE)
        
        # 一番上に「文字列検索ツール」と表示
        tk.Label(self.root, text=WIN_TITLE, font=(DEFAULT_FONT_NAME, 16, "bold")).pack()
        
        # 検索対象のディレクトリ入力欄
        frame_1 = tk.Frame(self.root)
        frame_1.pack(padx=10, pady=10)
        tk.Label(frame_1, text="検索対象のディレクトリ(ダブルクリックでダイアログを表示)", anchor=tk.W, font=(DEFAULT_FONT_NAME, 10, "normal")).pack(fill=tk.X)
        self.strvar_1_dir = tk.StringVar(frame_1)
        entry_1_dir = ttk.Entry(frame_1, textvariable=self.strvar_1_dir, width=ENTRY1_WIDTH, font=(DEFAULT_FONT_NAME, 10, "normal"))
        entry_1_dir.pack(fill=tk.X)
        entry_1_dir.bind("<Double-Button-1>", self.get_target_directory)
        

        # 拡張子入力欄
        frame_2 = tk.Frame(self.root)
        frame_2.pack(padx=10, pady=10)
        tk.Label(frame_2, text="検索対象のファイル拡張子(複数の場合は,区切り)", anchor=tk.W, font=(DEFAULT_FONT_NAME, 10, "normal")).pack(fill=tk.X)
        self.strvar_2_ext = tk.StringVar(self.root)
        entry_2_ext = ttk.Entry(frame_2, textvariable=self.strvar_2_ext, width=ENTRY1_WIDTH, font=(DEFAULT_FONT_NAME, 10, "normal"))
        entry_2_ext.pack(fill=tk.X)

        # 検索除外ディレクトリ入力欄
        tk.Label(self.root, text="\n検索から除外するフォルダ名", font=(DEFAULT_FONT_NAME, 10, "normal")).pack()
        button_1 = tk.Button(self.root, text="＋", width=BUTTON1_WIDTH, font=(DEFAULT_FONT_NAME, 10, "bold"))
        button_1.pack()
        frame_3 = tk.Frame(self.root)
        frame_3.pack(padx=10, pady=10, fill=tk.X)
        ## Canvasを使い、疑似的にFrameにスクロールバーをつけている
        canvas_1 = tk.Canvas(frame_3, highlightthickness=0, height=FRAME_IGNORE_DIR_HEIGHT)
        canvas_1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrbr_1 = ttk.Scrollbar(frame_3, orient=tk.VERTICAL, command=canvas_1.yview)
        scrbr_1.pack(side=tk.RIGHT, fill=tk.Y)
        canvas_1.configure(yscrollcommand=scrbr_1.set)
        self.frame_3_sub = tk.Frame(canvas_1)
        button_1.config(command=lambda : self.add_entry(self.frame_3_sub, self.entries_ignore_dirs))
        canvas_1.create_window((0, 0), window=self.frame_3_sub, anchor=tk.NW)
        ## frame_3_subのサイズ変更時にscrollregionを更新
        self.frame_3_sub.bind(
            "<Configure>",
            lambda e: canvas_1.configure(scrollregion=canvas_1.bbox(tk.ALL))
        )
        
        # OR/AND 検索モード切替
        tk.Label(self.root, text="\n検索モード (OR/AND)", font=(DEFAULT_FONT_NAME, 10, "normal")).pack()
        self.strvar_3_mode = tk.StringVar(self.root)
        combo_orand = ttk.Combobox(self.root, values=MODE_VALUES, width=10, textvariable=self.strvar_3_mode, font=(DEFAULT_FONT_NAME, 10, "normal"))
        combo_orand.pack()
        self.strvar_3_mode.set(MODE_VALUES[0])

        # 検索値入力欄
        tk.Label(self.root, text="\n検索値", font=(DEFAULT_FONT_NAME, 10, "normal")).pack()
        button_2 = tk.Button(self.root, text="＋", width=BUTTON1_WIDTH, font=(DEFAULT_FONT_NAME, 10, "bold"))
        button_2.pack()
        frame_4 = tk.Frame(self.root)
        frame_4.pack(padx=10, pady=10, fill=tk.X)
        ## Canvasを使い、疑似的にFrameにスクロールバーをつけている
        canvas_2 = tk.Canvas(frame_4, highlightthickness=0, height=FRAME_KEYWORD_HEIGHT)
        canvas_2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrbr_2 = ttk.Scrollbar(frame_4, orient=tk.VERTICAL, command=canvas_2.yview)
        scrbr_2.pack(side=tk.RIGHT, fill=tk.Y)
        canvas_2.configure(yscrollcommand=scrbr_2.set)
        self.frame_4_sub = tk.Frame(canvas_2)
        button_2.config(command=lambda : self.add_entry(self.frame_4_sub, self.entries_keywords))
        canvas_2.create_window((0, 0), window=self.frame_4_sub, anchor=tk.NW)
        ## frame_3_subのサイズ変更時にscrollregionを更新
        self.frame_4_sub.bind(
            "<Configure>",
            lambda e: canvas_2.configure(scrollregion=canvas_2.bbox(tk.ALL))
        )

        # スクロールイベント
        ## OSによりスクロールイベントが異なるためOS別に実装
        if sys.platform == "win32":
            # Windows用（既存のEnter/LeaveバインドでOK）
            canvas_1.bind('<Enter>', lambda e: canvas_1.bind_all('<MouseWheel>', lambda event: canvas_1.yview_scroll(int(-1 * (event.delta / abs(event.delta))), tk.UNITS)))
            canvas_1.bind('<Leave>', lambda e: canvas_1.unbind_all('<MouseWheel>'))
            canvas_2.bind('<Enter>', lambda e: canvas_2.bind_all('<MouseWheel>', lambda event: canvas_2.yview_scroll(int(-1 * (event.delta / abs(event.delta))), tk.UNITS)))
            canvas_2.bind('<Leave>', lambda e: canvas_2.unbind_all('<MouseWheel>'))
        elif sys.platform == "linux":
            # Linux用（Button-4/5をcanvasごとにbind/unbind）
            def linux_bind_canvas_scroll(canvas):
                def on_enter(event):
                    canvas.bind('<Button-4>', lambda e: canvas.yview_scroll(-1, tk.UNITS))
                    canvas.bind('<Button-5>', lambda e: canvas.yview_scroll(1, tk.UNITS))
                def on_leave(event):
                    canvas.unbind('<Button-4>')
                    canvas.unbind('<Button-5>')
                canvas.bind('<Enter>', on_enter)
                canvas.bind('<Leave>', on_leave)
            linux_bind_canvas_scroll(canvas_1)
            linux_bind_canvas_scroll(canvas_2)

        # 検索ボタン
        style_1 = ttk.Style(self.root)
        style_1.configure("TButton", font=(DEFAULT_FONT_NAME, 16))
        self.button_3_search = ttk.Button(self.root, text="検索", command=self.search_files, style="TButton")
        self.button_3_search.pack(padx=10, pady=10)

        # ステータステキスト
        self.strvar_4_status = tk.StringVar()
        tk.Label(self.root, textvariable=self.strvar_4_status, font=(DEFAULT_FONT_NAME, 10, "normal")).pack(pady=10)
    
    def focus_root(self, e: tk.Event):
        widget = e.widget
        if not isinstance(widget, (ttk.Entry, tk.Label)):
            self.root.focus_set()

    # フォルダー選択ダイアログ用
    def get_target_directory(self, e: tk.Event):
        # ダブルクリックをトリガーにして挿入した文字列は選択状態になり、
        # 且つselection系のメゾッドで選択状態を解除できない。
        # ただ、state=DISABLEDであれば選択状態にならないので、イベント検知後すぐに
        # DISABLEDにして、文字列の挿入が終わったらstateを戻している
        e.widget.configure(state=tk.DISABLED)
        res = filedialog.askdirectory(mustexist=True)
        self.strvar_1_dir.set(res)
        self.root.after(100, lambda :e.widget.config(state=tk.NORMAL))

    def add_entry(self, pframe, entries:list, dir_name=""):
        # 一行分の Frame（Label/Entry と 削除ボタンを並べる）
        row_frame = tk.Frame(pframe)
        row_frame.pack(fill=tk.X, pady=5, padx=5)
        # 初期値
        text_var = tk.StringVar()
        text_var.set(dir_name)
        # Label生成
        label = tk.Label(row_frame, textvariable=text_var, width=ENTRY2_WIDTH, anchor="w", relief="sunken", font=(DEFAULT_FONT_NAME, 10, "normal"))
        label.pack(side=tk.LEFT, padx=(0, 5))
        # LabelクリックでEntryに切り替え
        def to_entry(event=None):
            label.pack_forget()
            entry.pack(side=tk.LEFT, padx=(0, 5))
            entry.focus_set()
        # Entry生成
        entry = ttk.Entry(row_frame, textvariable=text_var, width=ENTRY2_WIDTH+4, font=(DEFAULT_FONT_NAME, 10, "normal"))
        # Entry編集終了でLabelに戻す
        def to_label(event=None):
            entry.pack_forget()
            label.pack(side=tk.LEFT, padx=(0, 5))
        label.bind("<Button-1>", to_entry)
        entry.bind("<Return>", to_label)
        entry.bind("<FocusOut>", to_label)
        # 削除ボタン
        del_btn = tk.Button(row_frame, text="－", width=BUTTON1_WIDTH, command=lambda: self.remove_entry(row_frame, entries), font=(DEFAULT_FONT_NAME, 10, "bold"))
        del_btn.pack(side=tk.RIGHT)
        entries.append((text_var, row_frame))

    def remove_entry(self, target_frame, entries:list):
        # entries リストから対象を削除して、ウィジェットを破棄
        for i, (text_var, frame) in enumerate(entries):
            if frame == target_frame:
                frame.destroy()
                entries.pop(i)
                break

    # ウィンドウを中央に表示する
    def centering_main_window(self):
        if sys.platform == "win32":
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            self.root.update_idletasks()
            window_width = self.root.winfo_width()
            window_height = self.root.winfo_height()
            x = screen_width / 2 - window_width / 2
            y = screen_height / 2 - window_height / 2
            self.root.geometry("+%d+%d" % (x, y))

    # 指定したディレクトリから特定の拡張子のファイルを検索し、キーワードが含まれるファイルを保存
    def search_files(self):
        """ディレクトリ内のテキストファイルを検索"""
        self.st = time.time()

        # ステータステキストを検索中に変える 検索ボタンは無効化
        self.strvar_4_status.set(STATUS_TEXT[1])
        self.button_3_search.config(state=tk.DISABLED)

        # 多分、tkinterウィジェットから値を読み取ると時間がかかるため、変数に代入していたほうが早い
        target_dir = self.strvar_1_dir.get()
        ignore_dirs = list(map(lambda x: x[0].get(), self.entries_ignore_dirs))
        keywords = list(map(lambda x: x[0].get(), self.entries_keywords))
        filetypes = self.strvar_2_ext.get().split(",")
        mode = self.strvar_3_mode.get().lower()

        # スレッドで高速化
        search_thread = Thread(target=walk_dir, args=(target_dir, ignore_dirs, keywords, filetypes, mode), daemon=True)
        search_thread.start()
        self.root.after(100, self.check_search_finish, search_thread)

        # 別プロセスで高速化
        # search_process = Process(target=walk_dir, args=(target_dir, ignore_dirs, keywords, filetypes, mode), daemon=True)
        # search_process.start()
        # self.root.after(100, self.check_process_finish, search_process)
    
    def check_search_finish(self, thread_or_process):
        if not thread_or_process.is_alive():
            # ステータステキストを戻す 検索ボタンを戻す
            self.strvar_4_status.set(STATUS_TEXT[0])
            self.button_3_search.config(state=tk.NORMAL)
            print("="*50 + f"\nTime: {time.time() - self.st:0.001f}s")
        else:
            self.root.after(100, self.check_search_finish, thread_or_process)


    def run(self):
        # 無視するフォルダ名の初期値を設定
        for dir_name in IGNORE_DIR:
            self.add_entry(self.frame_3_sub, self.entries_ignore_dirs, dir_name)
        self.centering_main_window()
        self.strvar_4_status.set(STATUS_TEXT[0])
        self.root.mainloop()


if __name__ == "__main__":
    SearchLine().run()