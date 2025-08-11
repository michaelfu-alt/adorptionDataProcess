from pywinauto import Application, Desktop
from pywinauto.mouse import move, click
from pywinauto.keyboard import send_keys
import pyperclip
import time
import sys, os, json
import datetime

LOG_FILE = "soran_log.txt"

# ------------------ Logging Setup ------------------
class TeeLogger:
    def __init__(self, filepath):
        self.terminal = sys.__stdout__
        self.log = open(filepath, "w", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

# Redirect stdout to both console and file
sys.stdout = TeeLogger(LOG_FILE)

# ------------------ Main Logic ------------------

def fill_analyze_dlg_params(main_win, analyze_dlg, txt_path, params):
    """
    自动填写 Analyze Pore Size 窗口参数并导出 CSV。
    """
    # 1. Experiment Isotherm
    print(f"[DEBUG] 设置 Experiment Isotherm: {txt_path}")
    analyze_dlg.child_window(class_name="Edit", found_index=0).set_edit_text(str(txt_path))

    # 2. p/p0 ComboBox
    pp0_value = str(params.get("pp0", "p0"))
    print(f"[DEBUG] 选择 p/p0: {pp0_value}")
    cb_pp0 = analyze_dlg.child_window(title=pp0_value, class_name="ComboBox")
    print("  - 所有选项:", cb_pp0.item_texts())
    cb_pp0.select(pp0_value)

    # 3. 单位 ComboBox
    unit_value = str(params.get("unit", "cm3(STP)/g"))
    print(f"[DEBUG] 选择单位: {unit_value}")
    cb_unit = analyze_dlg.child_window(title=unit_value, class_name="ComboBox")
    print("  - 所有选项:", cb_unit.item_texts())
    cb_unit.select(unit_value)

    # 4. 模型 ComboBox
    model_index = int(params.get("model_index", 0))
    print(f"[DEBUG] 选择模型索引: {model_index}")
    analyze_dlg.child_window(title="N2 in Carbon Slit pore at 77K", class_name="ComboBox").select(model_index)
    time.sleep(1)

    # 5. Desorption CheckBox
    desorp_val = params.get("desorption", False)
    print(f"[DEBUG] 设置 Desorption: {desorp_val}")
    try:
        btn = analyze_dlg.child_window(title="Desorption", class_name="Button")
        if desorp_val:
            btn.check()
        else:
            btn.uncheck()
    except Exception as e:
        print("[WARN] Desorption按钮未找到或无法操作：", e)

    # 6. Min/Max Pressure
    min_p = str(params.get("min_pressure", "0.05"))
    max_p = str(params.get("max_pressure", "0.95"))
    print(f"[DEBUG] 设置 Min Pressure: {min_p}")
    analyze_dlg.child_window(class_name="Edit", found_index=1).set_edit_text(min_p)
    print(f"[DEBUG] 设置 Max Pressure: {max_p}")
    analyze_dlg.child_window(class_name="Edit", found_index=2).set_edit_text(max_p)

    # 7. Smooth Factor
    smooth_val = str(params.get("smooth_factor", "4"))
    print(f"[DEBUG] 设置 Smooth Factor: {smooth_val}")
    try:
        trackbar = analyze_dlg.child_window(class_name="msctls_trackbar32")
        edits = analyze_dlg.descendants(class_name="Edit")
        trackbar_rect = trackbar.rectangle()
        for edit in edits:
            rect = edit.rectangle()
            if rect.left > trackbar_rect.right and abs(rect.top - trackbar_rect.top) < 50:
                edit.set_edit_text(smooth_val)
                print("已设置 Smooth Factor")
                break
    except Exception as e:
        print("[WARN] Smooth Factor未找到或无法填写：", e)

    time.sleep(10)
    print("Wait 3s for data importing")
    send_keys("{ENTER}")
    time.sleep(1)

    # 8. Export CSV File
    csv_offset_x = 1357 - 1098
    csv_offset_y = 177 - 109
    csv_width_analysis = 1385 - 1357
    csv_height_analysis = 173 - 149
    win_rect = main_win.rectangle()
    win_left, win_top = win_rect.left, win_rect.top
    csv_center_x = win_left + csv_offset_x + csv_width_analysis // 2
    csv_center_y = win_top + csv_offset_y + csv_height_analysis // 2
    click(coords=(csv_center_x, csv_center_y))
    print("窗口隐藏后文件存储")
    time.sleep(1)
    send_keys("%D")

    folder = os.path.normpath(txt_path)
    pyperclip.copy(os.path.dirname(folder))
    send_keys("^v")
    time.sleep(0.5)
    send_keys("%S")
    time.sleep(1)

    # 9. Check output CSV exists
    expected_dir = os.path.dirname(txt_path)
    expected_file = os.path.join(expected_dir, "DFT Result.csv")
    for _ in range(10):
        if os.path.exists(expected_file):
            print(f"[OK] 结果文件已生成: {expected_file}")
            break
        time.sleep(0.5)
    else:
        print(f"[WARN] 未检测到输出文件: {expected_file}")

    print(f"[DONE] 文件处理完成: {txt_path}")


def process_one_file_dft(txt_path, app, params):
    main_win = app.window(title_re=".*Soran.*")
    main_win.wait('visible', timeout=15)
    main_win.set_focus()

    # 点击 Analysis 菜单
    win_rect = main_win.rectangle()
    win_left, win_top = win_rect.left, win_rect.top
    offset_x = 1299 - 1098
    offset_y = 149 - 109
    width_analysis = 1363 - 1299
    height_analysis = 173 - 149
    center_x = win_left + offset_x + width_analysis // 2
    center_y = win_top + offset_y + height_analysis // 2

    move(coords=(center_x, center_y))
    time.sleep(0.5)
    click(coords=(center_x, center_y))
    print(f"Clicked Analysis at ({center_x},{center_y})")
    send_keys('{DOWN}')
    time.sleep(0.2)
    send_keys('{ENTER}')
    print("Pressed Enter to activate the menu item.")

    # 等待弹窗
    analyze_dlg = None
    try:
        analyze_dlg = Desktop(backend="win32").window(title_re=".*Analyze Pore Size.*")
        analyze_dlg.wait("exists ready", timeout=10)
    except Exception:
        raise Exception("未找到 Analyze Pore Size 窗口")

    print("Find Window:", analyze_dlg.window_text())
    fill_analyze_dlg_params(main_win, analyze_dlg, txt_path, params)
    time.sleep(1)


def batch_process(filelist_txt, params):
    """
    批量处理文件
    """
    soran_exe = params["soran_exe"]
    print(f"[启动 Soran 应用]: {soran_exe}")
    app = Application(backend="win32").start(soran_exe)

    with open(filelist_txt, "r", encoding="utf-8") as f:
        file_paths = [line.strip() for line in f if line.strip()]

    print(f"[DFT] 共收到 {len(file_paths)} 个文件待处理。")
    for txt_path in file_paths:
        txt_path = os.path.normpath(txt_path)
        print(f"\n==== 处理文件: {txt_path} ====")
        try:
            process_one_file_dft(txt_path, app, params)
        except Exception as e:
            print(f"[DFT ERROR] {txt_path}: {e}")
        time.sleep(1)

    print("[DFT] 全部文件处理完毕。")
    app.kill()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python main_soran_runner.py <文件清单.txt> <设置.json>")
        sys.exit(1)

    filelist_txt = sys.argv[1]
    params_json = sys.argv[2]

    with open(params_json, "r", encoding="utf-8") as f:
        params = json.load(f)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n====== Soran DFT 批处理启动时间: {now} ======")
    print("参数内容如下：")
    for k, v in params.items():
        print(f"{k}: {v}")
    print("参数读取正常，开始处理…")

    batch_process(filelist_txt, params)
