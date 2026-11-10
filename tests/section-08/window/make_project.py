"""Write the KivyForge project for the window test, for one version point.
Usage: make_project.py WORK LABEL

LABEL is "release" (pyobjus 1.2.4, Rubicon 0.5.7) or "main" (the default
branches), with the same iOS wheels as M1, from WORK/wheels/LABEL. The app also
needs Kivy, for a window, and Plyer 2.1.0 from PyPI. Kivy's iOS wheel and its
pins are KivyForge's hello-kivy example's, from the kivy-mobile-wheels index
(the comparison author's)."""
import glob
import os
import shutil
import sys

work, label = sys.argv[1:]
here = os.path.dirname(os.path.abspath(__file__))
root = os.path.join(work, "window-apps", label)
shutil.rmtree(os.path.join(root, "src"), ignore_errors=True)
os.makedirs(os.path.join(root, "src"))
os.makedirs(os.path.join(root, "wheels"), exist_ok=True)
for wheel in glob.glob(os.path.join(work, "wheels", label, "*.whl")):
    shutil.copy(wheel, os.path.join(root, "wheels"))
shutil.copy(os.path.join(here, "main.py"), os.path.join(root, "src"))

rubicon = next((os.path.basename(w).split("-")[1] for w in glob.glob(os.path.join(root, "wheels", "rubicon*"))), "0.5.7")
open(os.path.join(root, "pyproject.toml"), "w").write(f'''[project]
name = "s8-window-{label}"
version = "0.1.0"
requires-python = ">=3.15"
dependencies = [
    "kivy==3.0.0.dev202610251128",
    "filetype==1.2.0",
    "plyer==2.1.0",
    "pyobjus==1.2.4",
    "rubicon-objc=={rubicon}",
]

[tool.kivy]
display_name = "S8 window {label}"
app_dir = "src"
entry_point = "main"
orientation = ["portrait"]

[tool.kivy.ios]
schema_version = 1
bundle_id = "org.comparison.s8-window-{label}"
build = 1
deployment_target = "16.0"
find_links = ["wheels"]
extra_index_urls = ["https://elliotgarbus.github.io/kivy-mobile-wheels/simple/"]
exclude = ["kivy-garden", "requests", "certifi", "charset-normalizer", "idna", "urllib3", "docutils", "pygments"]

[tool.kivy.ios.python]
version = "3.15.0"

[tool.kivy.ios.signing]
team_id = ""
identity = "Apple Development"
auto_signing = true
''')
print(root)
