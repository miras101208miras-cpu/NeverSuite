import os
import subprocess
import tempfile

def make_desktop_shortcut():
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    shortcut_path = os.path.join(desktop, "Never Hub.lnk")
    pythonw = os.path.join(os.path.dirname(os.sys.executable), "pythonw.exe")
    if not os.path.exists(pythonw):
        pythonw = os.sys.executable

    hub_dir = r"C:\Users\school57-60\.gemini\antigravity\scratch\Never_Hub"
    hub_script = os.path.join(hub_dir, "main.py")
    icon_path = os.path.join(hub_dir, "assets", "never_hub.ico")

    vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
strDesktop = WshShell.SpecialFolders("Desktop")
Set oShortcut = WshShell.CreateShortcut(strDesktop & "\\Never Hub.lnk")
oShortcut.TargetPath = "{pythonw}"
oShortcut.Arguments = """{hub_script}"""
oShortcut.WorkingDirectory = "{hub_dir}"
oShortcut.WindowStyle = 1
oShortcut.IconLocation = "{icon_path}, 0"
oShortcut.Description = "Never Hub - Central Tray & Theme Launcher for Never Suite"
oShortcut.Save
'''
    vbs_path = os.path.join(tempfile.gettempdir(), "create_never_hub_lnk.vbs")
    with open(vbs_path, "w", encoding="utf-8") as f:
        f.write(vbs_content)

    subprocess.run(["cscript.exe", "//Nologo", vbs_path], check=True)
    if os.path.exists(vbs_path):
        os.remove(vbs_path)
    print("Created desktop shortcut:", shortcut_path)
    return shortcut_path

if __name__ == "__main__":
    make_desktop_shortcut()
