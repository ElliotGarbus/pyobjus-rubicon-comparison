"""Write a KivyForge project for one version point.
Usage: make_project.py WORK LABEL

LABEL is "release" (pyobjus 1.2.4, Rubicon 0.5.7) or "main" (the default
branches). WORK/wheels/LABEL holds the iOS wheels from Section 2's
build_wheels.sh. Adapted from Section 4's make_project.py."""
import glob
import os
import shutil
import sys

work, label = sys.argv[1:]
here = os.path.dirname(os.path.abspath(__file__))
m1 = os.path.dirname(here)
root = os.path.join(work, "apps", label)
shutil.rmtree(os.path.join(root, "src"), ignore_errors=True)
os.makedirs(os.path.join(root, "src"))
os.makedirs(os.path.join(root, "wheels"), exist_ok=True)
for wheel in glob.glob(os.path.join(work, "wheels", label, "*.whl")):
    shutil.copy(wheel, os.path.join(root, "wheels"))
shutil.copy(os.path.join(here, "main.py"), os.path.join(root, "src"))
for name in ("common.py", "cases_pyobjus.py", "cases_rubicon.py", "cases_ios_pyobjus.py", "cases_ios_rubicon.py"):
    shutil.copy(os.path.join(m1, name), os.path.join(root, "src"))

rubicon = next((os.path.basename(w).split("-")[1] for w in glob.glob(os.path.join(root, "wheels", "rubicon*"))), "0.5.7")
open(os.path.join(root, "pyproject.toml"), "w").write(f'''[project]
name = "s8-{label}"
version = "0.1.0"
requires-python = ">=3.15"
dependencies = ["pyobjus==1.2.4", "rubicon-objc=={rubicon}"]

[tool.kivy]
display_name = "S8 {label}"
app_dir = "src"
entry_point = "main"
orientation = ["portrait"]

[tool.kivy.ios]
schema_version = 1
bundle_id = "org.comparison.s8-{label}"
build = 1
deployment_target = "16.0"
find_links = ["wheels"]

[tool.kivy.ios.python]
version = "3.15.0"

[tool.kivy.ios.signing]
team_id = ""
identity = "Apple Development"
auto_signing = true
''')
print(root)
