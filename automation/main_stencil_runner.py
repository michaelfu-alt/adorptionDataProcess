# automation/main_stencil_runner.py
import subprocess
import os
import sys
import json

def load_settings(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python main_stencil_runner.py <filelist.txt> <settings.json>")
        sys.exit(1)

    filelist = sys.argv[1]
    settings_file = sys.argv[2]

    settings = load_settings(settings_file)
    print(settings)
    stencil_exe = os.path.normpath(settings.get("stencil_exe", ""))
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "stencilwizard_runner.py"))

    print(f">>> 调用 stencilwizard_runner.py")
    subprocess.run([sys.executable, script_path, filelist, settings_file], check=True)
