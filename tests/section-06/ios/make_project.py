"""Write a KivyForge project for one version point, as Section 2's does.
Usage: make_project.py WORK WHEELS LABEL

LABEL is "release" (pyobjus 1.2.4, Rubicon 0.5.7) or "main" (the default
branches). WHEELS holds Section 2's iOS wheels, in folders named by LABEL.
WORK must hold S6Fixture.xcframework, from build_fixture.sh."""
import glob
import os
import shutil
import subprocess
import sys

work, wheels, label = sys.argv[1:]
here = os.path.dirname(os.path.abspath(__file__))
tests = os.path.dirname(here)
root = os.path.join(work, "apps", label)
os.makedirs(os.path.join(root, "src"), exist_ok=True)
os.makedirs(os.path.join(root, "wheels"), exist_ok=True)
for wheel in glob.glob(os.path.join(wheels, label, "*.whl")):
    shutil.copy(wheel, os.path.join(root, "wheels"))
subprocess.run(["ditto", "-c", "-k", "--keepParent", os.path.join(work, "S6Fixture.xcframework"),
                os.path.join(root, "S6Fixture.xcframework.zip")], check=True)
shutil.copy(os.path.join(here, "main.py"), os.path.join(root, "src"))
shutil.copy(os.path.join(tests, "bench.py"), os.path.join(root, "src"))
rubicon = next((os.path.basename(w).split("-")[1] for w in glob.glob(os.path.join(root, "wheels", "rubicon*"))), "0.5.7")
open(os.path.join(root, "pyproject.toml"), "w").write(f'''[project]
name = "s6-{label}"
version = "0.1.0"
requires-python = ">=3.15"
dependencies = ["pyobjus==1.2.4", "rubicon-objc=={rubicon}"]

[tool.kivy]
display_name = "S6 {label}"
app_dir = "src"
entry_point = "main"
orientation = ["portrait"]

[tool.kivy.ios]
schema_version = 1
bundle_id = "org.comparison.s6-{label}"
build = 1
deployment_target = "16.0"
find_links = ["wheels"]

[tool.kivy.ios.python]
version = "3.15.0"

[tool.kivy.ios.native.xcframeworks]
S6Fixture = {{ version = "1.0", source = "S6Fixture.xcframework.zip" }}

[tool.kivy.ios.signing]
team_id = ""
identity = "Apple Development"
auto_signing = true
''')
