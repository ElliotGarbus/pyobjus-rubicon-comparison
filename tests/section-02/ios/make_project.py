"""Write a KivyForge project for one version point.
Usage: make_project.py WORK LABEL
LABEL is "release" (pyobjus 1.2.4, Rubicon 0.5.7) or "main" (the default branches)."""
import glob
import os
import shutil
import subprocess
import sys

work, label = sys.argv[1:]
here = os.path.dirname(os.path.abspath(__file__))
tests = os.path.dirname(here)
root = os.path.join(work, "apps", label)
os.makedirs(os.path.join(root, "src"), exist_ok=True)
os.makedirs(os.path.join(root, "wheels"), exist_ok=True)
for wheel in glob.glob(os.path.join(work, "wheels", label, "*.whl")):
    shutil.copy(wheel, os.path.join(root, "wheels"))
subprocess.run(["ditto", "-c", "-k", "--keepParent", os.path.join(work, "S2Fixture.xcframework"),
                os.path.join(root, "S2Fixture.xcframework.zip")], check=True)
shutil.copy(os.path.join(here, "main.py"), os.path.join(root, "src"))
for name in ("adapters.py", "scenarios.py"):
    shutil.copy(os.path.join(tests, name), os.path.join(root, "src"))
rubicon = next((os.path.basename(w).split("-")[1] for w in glob.glob(os.path.join(root, "wheels", "rubicon*"))), "0.5.7")
open(os.path.join(root, "pyproject.toml"), "w").write(f'''[project]
name = "s2-{label}"
version = "0.1.0"
requires-python = ">=3.15"
dependencies = ["pyobjus==1.2.4", "rubicon-objc=={rubicon}"]

[tool.kivy]
display_name = "S2 {label}"
app_dir = "src"
entry_point = "main"
orientation = ["portrait"]

[tool.kivy.ios]
schema_version = 1
bundle_id = "org.comparison.s2-{label}"
build = 1
deployment_target = "16.0"
find_links = ["wheels"]

[tool.kivy.ios.python]
version = "3.15.0"

[tool.kivy.ios.native.xcframeworks]
S2Fixture = {{ version = "1.0", source = "S2Fixture.xcframework.zip" }}

[tool.kivy.ios.signing]
team_id = ""
identity = "Apple Development"
auto_signing = true
''')
