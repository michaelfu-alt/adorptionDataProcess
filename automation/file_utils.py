import os
import tempfile

def scan_iprd_files(root_dir, excluded_folders):
    result = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # 判断当前路径是否属于被排除的子文件夹
        rel_path = os.path.relpath(dirpath, root_dir)
        if any(rel_path.startswith(f) for f in excluded_folders):
            continue
        for f in filenames:
            if f.endswith(".iPrd"):
                result.append(os.path.normpath(os.path.join(dirpath, f)))
    return result

def convert_iprd_paths_to_txt_file(iprd_paths):
    txt_paths = [p.replace(".iPrd", ".txt") for p in iprd_paths]

    fd, tmp_path = tempfile.mkstemp(suffix=".txt", prefix="converted_soran_list_", text=True)
    os.close(fd)
    with open(tmp_path, "w", encoding="utf-8") as f:
        for path in txt_paths:
            f.write(path + "\n")
    return tmp_path

def write_filelist(path, lines):
    with open(path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")
