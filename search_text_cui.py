import argparse
import os
from tkinter import filedialog
import traceback
import time

# ファイルにキーワードが含まれるか判定
def contains_keyword(file_path, keywords, mode: str):
    """ファイル内にいずれかのキーワードが含まれているかチェック"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # 検索モードを取得
        if mode.lower() == "or":
            return any(keyword in content for keyword in keywords)
        elif mode.lower() == "and":
            return all(keyword in content for keyword in keywords)
    except UnicodeDecodeError:
        pass
    except Exception as e:
        print(f"エラー: {file_path} - {e}")
        return False

# ファイルにキーワードが含まれる行番号と内容を返す
def find_keyword_lines(file_path, keywords, mode: str):
    """ファイル内でキーワードにヒットした行番号と内容を返す"""
    results = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                line_strip = line.rstrip('\n')
                if mode.lower() == "or":  # OR
                    if any(keyword in line_strip for keyword in keywords if keyword):
                        results.append((i, line_strip))
                elif mode.lower() == "and":  # AND
                    if all(keyword in line_strip for keyword in keywords if keyword):
                        results.append((i, line_strip))
    except UnicodeDecodeError:
        pass
    except Exception as e:
        print(f"エラー: {file_path} - {e}")
    return results

def walk_dir(target_dir, ignore_dirs, keywords, exts, mode="or"):
    if os.path.exists(target_dir) and os.path.isdir(target_dir):
        matching_files = list()
        for root, dirs, files in os.walk(target_dir):
            # 除外フォルダーならスキップ
            if any(ignore_dir in root for ignore_dir in ignore_dirs):
                continue
            for file in files:
                for ext in exts:
                    # endswithなら.txtでもtxtでも良い
                    if file.endswith(ext):
                        file_path = os.path.join(root, file)
                        hit_lines = find_keyword_lines(file_path, keywords, mode)
                        if hit_lines:
                            matching_files.append(file_path)
                            print(f"\n{'='*50}\n{file_path}")
                            for lineno, content in hit_lines:
                                print(f"{lineno}: {content}")


if __name__ == "__main__":
    st = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--target_dir", required=False)
    parser.add_argument("-i", "--ignore_dirs", required=False)
    parser.add_argument("-k", "--keywords", required=False)
    parser.add_argument("-e", "--exts", required=False)
    parser.add_argument("-m", "--mode", required=False)

    args = parser.parse_args()
    # 引数が何もない場合
    if all(x is None for x in (args.target_dir, args.ignore_dirs, args.keywords, args.exts)):
        target_dir = filedialog.askdirectory(title="検索を行うフォルダーを選択してください")
        print("ディレクトリ > " + target_dir)
        ignore_dirs = input("無視するフォルダー名（複数ある場合は,区切り）").split(",") + ["venv", ".pyenv", ".conda", "site-packages"]
        keywords = input("検索したい文字列（複数ある場合は,区切り） > ").split(",")
        filetypes = input("ファイルの拡張子（複数ある場合は,区切り） > ").split(",")

        try:
            walk_dir(target_dir, ignore_dirs, keywords, filetypes)
        except Exception as e:
            traceback.print_exception(e)
        
        input("続行するにはEnterを押してください... ")
    # 引数が指定されている場合
    else:
        if any(x is None for x in (args.target_dir, args.keywords, args.exts)):
            input(f"[Error] 引数が不足しています。")
        else:
            if all(type(x) is str for x in (args.target_dir, args.keywords, args.exts)):
                walk_dir(args.target_dir,
                        args.ignore_dirs.split(",") if not args.ignore_dirs is None else [] + ["venv", ".pyenv", ".conda", "site-packages"],
                        args.keywords.split(","),
                        args.exts.split(","))
    print("====" * 5 + f"\nTime: {time.time() - st:0.01f}s")