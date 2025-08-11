# Batch_stencilwizard.py

import json
from pywinauto import Application
import time
from pywinauto.findwindows import find_windows
from pywinauto.keyboard import send_keys
import pyperclip
import os
import sys

def load_settings(settings_path="settings.json"):
    if os.path.exists(settings_path):
        with open(settings_path, "r", encoding="utf-8") as f:
            return json.load(f)
        return
    raise FileNotFoundError(f"未找到设置文件: {settings_path}")

def process_one_file(folder, fname):
    fname_out = fname.partition('.')[0]
    main_win = app.window(title_re=".*StencilWizard.*")

    main_win.wait("visible")

    time.sleep(1) 
    # time.sleep(5)
    send_keys("%F")
    send_keys("{ENTER}")
    send_keys("{ENTER}")
    time.sleep(0.1)

    file_dlg = app.window(title_re="选择要打开的等温线库文件")

    file_dlg.wait('visible', timeout=10)
    file_dlg.set_focus()
    send_keys("%D")
    send_keys("{BACKSPACE}")
    time.sleep(0.1)

    path = folder
    pyperclip.copy(path)
    send_keys('^v'  )
    send_keys("{ENTER}")
    time.sleep(0.1)

    for edit in file_dlg.children(class_name="Edit"):
        if edit.is_visible() and edit.is_enabled():
            print("找到可见文本框，开始输入文件名…")
            edit.click_input()
            edit.set_edit_text(fname)
            edit.type_keys("{ENTER}") 
            print("输入完成并回车。")
            break
    else:
        print("未找到可输入的文本框！")

    time.sleep(0.1)

    shezhi_dlg = app.window(title_re="设置报告")
# 2. 获取 shezhi_dlg 的窗口句柄
    dlg_handle = shezhi_dlg.handle

# 3. 用 uia backend attach 到同一个窗口
    app_uia = Application(backend="uia").connect(handle=dlg_handle)
    dlg = app_uia.window(handle=dlg_handle)

# 4. 后续就可以用 uia 方式操作所有现代控件！
# 示例：遍历List，自动切换分组并批量设置
    list_box = dlg.child_window(control_type="List")
    list_items = list_box.children(control_type="ListItem")

    for item in list_items:
        item.select()  # 或 item.click_input()
        print("已选中：", item.window_text())

    # 设置节点符
    # for edit in dlg.children(control_type="Edit"):
    #     if edit.is_visible() and edit.is_enabled():
    #         edit.set_edit_text("10.0")
    #         break

    # 勾选所有CheckBox
        for cb in dlg.children(control_type="CheckBox"):
            if cb.is_visible() and cb.is_enabled() and not cb.get_toggle_state():
                cb.click()
        time.sleep(0.05)
# 点击确定
    ok_btn = dlg.child_window(title="确定", control_type="Button")
    ok_btn.click()
    time.sleep(1)

    send_keys("%F")
    send_keys('^s')
    time.sleep(0.1)
    save_dlg = app.window(title_re="输入一个文件名")
    save_dlg.wait('visible', timeout=10)
    save_dlg.set_focus()
#Enter the location of the folder of the files
    send_keys('%d')                # Alt+D，聚焦地址栏
    send_keys('^a{BACKSPACE}')     # 清空
    pyperclip.copy(folder)
    send_keys('^v')   # 你的文件夹路径
    send_keys('{ENTER}')           # 回车，跳转到目标文件夹
    time.sleep(0.1)


    for edit in save_dlg.children(class_name="Edit"):
        if edit.is_visible() and edit.is_enabled():
            print("找到可见文本框，开始输入文件名…")
            edit.click_input()
            edit.set_edit_text(fname_out)
            send_keys("{TAB}")
            send_keys("{DOWN}")
            send_keys("{DOWN}")
            send_keys("{ENTER}")
            send_keys("{ENTER}")
            print("输入完成并回车。")
            break
    else:
        print("未找到可输入的文本框！")

    main_win.child_window(title="保存当前文件", class_name="ExGraphControls").click()
    time.sleep(0.1)
    save_dlg = app.window(title_re="输入一个文件名")
    save_dlg.wait('visible', timeout=10)
    save_dlg.set_focus()
    time.sleep(0.1)

#Enter the location of the folder of the files
    send_keys('%d')                # Alt+D，聚焦地址栏
    time.sleep(0.1)
    send_keys('^a{BACKSPACE}')     # 清空
    pyperclip.copy(folder)
    send_keys('^v')   # 你的文件夹路径   # 你的文件夹路径
    send_keys('{ENTER}')           # 回车，跳转到目标文件夹
    time.sleep(1)

    for edit in save_dlg.children(class_name="Edit"):
        if edit.is_visible() and edit.is_enabled():
            print("找到可见文本框，开始输入文件名…")
            edit.click_input()
            edit.set_edit_text(fname_out)
            print(fname_out)
            send_keys("{TAB}")
            send_keys("{DOWN}")
            send_keys("{DOWN}")
            send_keys("{DOWN}")
            send_keys("{DOWN}")
            send_keys("{ENTER}")
            send_keys("{ENTER}") 
            print("输入完成并回车。")
            break
    else:
        print("未找到可输入的文本框！")
    time.sleep(0.1)
    close_btn = main_win.child_window(title_re="关闭.*", class_name="ExGraphControls")
    time.sleep(0.1)
    close_btn.click_input()
    print("已点击当前文件的关闭按钮。")
    time.sleep(0.1)
    send_keys('N')
    time.sleep(1)

def batch_process(filelist_path, app):
    with open(filelist_path, "r", encoding="utf-8") as f:
        file_paths = [line.strip() for line in f if line.strip()]
    print(file_paths)
    for _, path in enumerate(file_paths):
        folder = os.path.dirname(path)
        fname = os.path.basename(path)
        print(f"Processing {fname} in {folder}")
        try:
            process_one_file(folder, fname)
        except Exception as e:
            print(f"[ERROR] {fname}: {e}")
        time.sleep(0.2)
    time.sleep(1)
    print(f"全部文件处理完毕，共 {len(file_paths)} 个文件。")
    print("准备关闭 StencilWizard ...")
    app.kill()
    print("已调用 app.kill()，请观察任务管理器是否已无进程")


if __name__ == "__main__":
    # 参数1: 文件清单txt，参数2: 参数json
    if len(sys.argv) < 3:
        print("用法: python batch_stencilwizard_app.py <filelist.txt> <params.json>")
        sys.exit(1)
    filelist_txt = sys.argv[1]
    params_json = sys.argv[2]
    params = load_settings(params_json)
    stencil_exe = os.path.normpath(params.get("stencil_exe", ""))
    if not stencil_exe or not os.path.exists(stencil_exe):
        raise FileNotFoundError(f"指定的 StencilWizard 路径不存在: {stencil_exe}")
    print(f"启动 StencilWizard: {stencil_exe}")
    app = Application(backend="win32").start(stencil_exe)
    time.sleep(1)
    batch_process(filelist_txt, app)  # 你的自动化主循环



