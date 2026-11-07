"""Write a KivyForge project for one version point.
Usage: make_project.py WORK WHEELS LABEL

LABEL is "release" (pyobjus 1.2.4, Rubicon 0.5.7) or "main" (the default
branches). WHEELS holds Section 2's iOS wheels, built from the same pinned
commits, in one folder per label."""
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
for name in ("S3Fixture", "S3Extra"):
    subprocess.run(["ditto", "-c", "-k", "--keepParent", os.path.join(work, f"{name}.xcframework"),
                    os.path.join(root, f"{name}.xcframework.zip")], check=True)
shutil.copy(os.path.join(here, "main.py"), os.path.join(root, "src"))
for name in ("cases.py", "cases_pyobjus.py", "cases_rubicon.py"):
    shutil.copy(os.path.join(tests, name), os.path.join(root, "src"))

# F7's Swift library, as a local package, the way an app ships its shim.
sources = os.path.join(root, "swift-shims", "Sources", "S3Swift")
os.makedirs(sources, exist_ok=True)
shutil.copy(os.path.join(tests, "S3Swift.swift"), sources)
open(os.path.join(root, "swift-shims", "Package.swift"), "w").write('''// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "S3Swift",
    platforms: [.iOS(.v16)],
    products: [
        .library(name: "S3Swift", type: .dynamic, targets: ["S3Swift"]),
    ],
    targets: [
        .target(name: "S3Swift"),
    ]
)
''')

rubicon = next((os.path.basename(w).split("-")[1] for w in glob.glob(os.path.join(root, "wheels", "rubicon*"))), "0.5.7")
open(os.path.join(root, "pyproject.toml"), "w").write(f'''[project]
name = "s3-{label}"
version = "0.1.0"
requires-python = ">=3.15"
dependencies = ["pyobjus==1.2.4", "rubicon-objc=={rubicon}"]

[tool.kivy]
display_name = "S3 {label}"
app_dir = "src"
entry_point = "main"
orientation = ["portrait"]

[tool.kivy.ios]
schema_version = 1
bundle_id = "org.comparison.s3-{label}"
build = 1
deployment_target = "16.0"
find_links = ["wheels"]

[tool.kivy.ios.python]
version = "3.15.0"

[tool.kivy.ios.native.xcframeworks]
S3Fixture = {{ version = "1.0", source = "S3Fixture.xcframework.zip" }}
# Embedded but not linked, so it isn't loaded until F1.6 loads it.
S3Extra = {{ version = "1.0", source = "S3Extra.xcframework.zip", link = false }}

[tool.kivy.ios.native.swift_packages]
S3Swift = {{ path = "swift-shims", products = ["S3Swift"] }}

[tool.kivy.ios.signing]
team_id = ""
identity = "Apple Development"
auto_signing = true
''')
