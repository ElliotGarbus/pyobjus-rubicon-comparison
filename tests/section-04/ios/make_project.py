"""Write a KivyForge project for one version point.
Usage: make_project.py WORK WHEELS LABEL

LABEL is "release" (pyobjus 1.2.4, Rubicon 0.5.7) or "main" (the default
branches). WHEELS holds Section 2's iOS wheels, one folder per label."""
import glob
import os
import shutil
import subprocess
import sys

work, wheels, label = sys.argv[1:]
here = os.path.dirname(os.path.abspath(__file__))
tests = os.path.dirname(here)
examples = os.path.join(tests, "..", "..", "examples", "section-04")
root = os.path.join(work, "apps", label)
os.makedirs(os.path.join(root, "src"), exist_ok=True)
os.makedirs(os.path.join(root, "wheels"), exist_ok=True)
for wheel in glob.glob(os.path.join(wheels, label, "*.whl")):
    shutil.copy(wheel, os.path.join(root, "wheels"))
subprocess.run(["ditto", "-c", "-k", "--keepParent", os.path.join(work, "S4Bridge.xcframework"),
                os.path.join(root, "S4Bridge.xcframework.zip")], check=True)
shutil.copy(os.path.join(here, "main.py"), os.path.join(root, "src"))
shutil.copy(os.path.join(tests, "harness.py"), os.path.join(root, "src"))
for path in glob.glob(os.path.join(examples, "e[234]_*.py")):
    shutil.copy(path, os.path.join(root, "src"))

# E4's Swift, both libraries' files in one local package.
sources = os.path.join(root, "swift-shims", "Sources", "S4Swift")
os.makedirs(sources, exist_ok=True)
for name in ("e4_async.swift", "e4_job.swift"):
    shutil.copy(os.path.join(examples, name), sources)
open(os.path.join(root, "swift-shims", "Package.swift"), "w").write('''// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "S4Swift",
    platforms: [.iOS(.v16)],
    products: [
        .library(name: "S4Swift", type: .dynamic, targets: ["S4Swift"]),
    ],
    targets: [
        .target(name: "S4Swift"),
    ]
)
''')

rubicon = next((os.path.basename(w).split("-")[1] for w in glob.glob(os.path.join(root, "wheels", "rubicon*"))), "0.5.7")
open(os.path.join(root, "pyproject.toml"), "w").write(f'''[project]
name = "s4-{label}"
version = "0.1.0"
requires-python = ">=3.15"
dependencies = ["pyobjus==1.2.4", "rubicon-objc=={rubicon}"]

[tool.kivy]
display_name = "S4 {label}"
app_dir = "src"
entry_point = "main"
orientation = ["portrait"]

[tool.kivy.ios]
schema_version = 1
bundle_id = "org.comparison.s4-{label}"
build = 1
deployment_target = "16.0"
find_links = ["wheels"]

[tool.kivy.ios.python]
version = "3.15.0"

[tool.kivy.ios.info_plist]
NSLocationWhenInUseUsageDescription = "The comparison's location example reads one location fix. It isn't stored or sent anywhere."
NSMotionUsageDescription = "The comparison's barometer example reads the air pressure. It isn't stored or sent anywhere."

[tool.kivy.ios.native.xcframeworks]
S4Bridge = {{ version = "1.0", source = "S4Bridge.xcframework.zip" }}

[tool.kivy.ios.native.swift_packages]
S4Swift = {{ path = "swift-shims", products = ["S4Swift"] }}

[tool.kivy.ios.signing]
team_id = ""
identity = "Apple Development"
auto_signing = true
''')
