"""T2: which of Section 3's feature rows each project's own suite tests.

Usage: features_tested.py CLONES OUT.json OUT.md

The judgments below were made by reading each suite at the pinned refs. This
script checks that every cited test exists at each ref, finds its line, and
writes the table with links.

Statuses:
- tested: a test calls the feature
- setup: the feature is called only to set up other tests, such as loading
  the test library
- partial: the test covers part of the feature, as the note says
- untested: the library supports the feature and no test calls it
- unsupported: Section 3 found the library doesn't support it, so there is
  nothing to test
"""
import ast
import json
import subprocess
import sys

REFS = {"pyobjus-1.2.4": ("pyobjus", "v1.2.4", "kivy/pyobjus"),
        "pyobjus-master": ("pyobjus", "0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81", "kivy/pyobjus"),
        "rubicon-0.5.7": ("rubicon-objc", "v0.5.7", "beeware/rubicon-objc"),
        "rubicon-main": ("rubicon-objc", "6bf06390f720226da3d51477f38de3ff1e680eaf", "beeware/rubicon-objc")}

# row: {version: (status, "file::test" or None, note)}
P, R = "pyobjus", "rubicon"
ROWS = {
    "F1.1 Classes and methods": {
        P: ("tested", "test_nsobject.py::test_description", ""),
        R: ("tested", "test_ObjCClass.py::test_by_name", "")},
    "F1.2 Properties": {
        P: ("tested", "test_properties.py::test_basic_properties", ""),
        R: ("tested", "test_NSArray.py::test_property", "")},
    "F1.3 Variadic methods": {
        P: ("tested", "test_nsarray.py::test_objc_arr_behaviour", "`arrayWithObjects:` with objects"),
        R: ("tested", "test_send_message.py::test_method_varargs_send", "")},
    "F1.4 Global constants": {
        P: ("unsupported", None, ""),
        R: ("tested", "test_const.py::test_objc_const", "")},
    "F1.5 C functions": {
        P: ("unsupported", None, ""),
        R: ("partial", "test_ObjCClass.py::test_by_pointer", "Calls runtime functions through Rubicon's own `libobjc` bindings. No test calls a framework function")},
    "F1.6 Loading code": {
        "pyobjus-1.2.4": ("setup", "test_properties.py::test_basic_properties", "`load_dylib` loads the test library in `setUp`"),
        "pyobjus-master": ("tested", "test_load_framework.py::test_loads_system_framework", ""),
        R: ("setup", None, "`load_library` loads the test library when the test package is imported")},
    "F1.7 Introspection": {
        P: ("untested", None, ""),
        R: ("unsupported", None, "")},
    "F2.1 Structs": {
        P: ("tested", "test_nsstring.py::test_substringWithRange", ""),
        R: ("tested", "test_ObjCProtocol.py::test_interface_return_struct", "")},
    "F2.2 Unions and bit fields": {
        "pyobjus-1.2.4": ("tested", "test_union.py::test_returning_values", "Returned unions"),
        "pyobjus-master": ("tested", "test_union.py::test_returning_values", "Returned unions, and a clear error for bit fields"),
        R: ("partial", "test_types.py::test_ctype_for_encoding_union", "Type-encoding conversion only. No test passes a union or bit field to a method")},
    "F2.3 C arrays": {
        P: ("tested", "test_carray.py::test_carray_int", ""),
        R: ("partial", "test_types.py::test_compound_value_for_sequence_array", "Conversion only. No test passes an array to a method")},
    "F2.4 Out parameters": {
        P: ("tested", "test_carray.py::test_carray_int", "A count written back through `unsigned int *`"),
        R: ("partial", "test_partial_method.py::test_lots_of_args", "Passes pointers that `getBytes:maxLength:usedLength:encoding:options:range:remainingRange:` writes into, and checks the bytes written to the buffer, not the values written through the scalar pointers. No `NSError **`")},
    "F2.5 Collections": {
        P: ("tested", "test_nsarray.py::test_objc_arr_behaviour", "Explicit conversion with `objc_arr`"),
        R: ("tested", "test_NSString.py::test_str_nsstring_conversion", "")},
    "F2.6 Python behavior on Objective-C objects": {
        P: ("unsupported", None, ""),
        R: ("tested", "test_NSArray.py::test_len", "")},
    "F2.7 Enums and constants": {
        "pyobjus-1.2.4": ("untested", None, ""),
        "pyobjus-master": ("tested", "test_downstream_call_shapes.py::test_enum_values_as_nsuinteger_arguments", ""),
        R: ("tested", "test_method.py::test_enum_argument", "")},
    "F3.1 New class": {
        P: ("unsupported", None, ""),
        R: ("tested", "test_ObjCClass.py::test_auto_rename_global", "")},
    "F3.2 Subclass an Apple class": {
        P: ("unsupported", None, ""),
        R: ("tested", "test_super.py::test_send", "")},
    "F3.3 Instance state": {
        P: ("unsupported", None, ""),
        R: ("tested", "test_ObjCClass.py::test_ivars", "")},
    "F3.4 Apple protocol": {
        P: ("tested", "test_delegate.py::test_existing_delegate", "`NSURLConnectionDelegate`"),
        R: ("untested", None, "Apple's protocols are checked with `isinstance` and `issubclass`, but no test implements one and receives a call. Protocols the test library declares are implemented (F3.5)")},
    "F3.5 Protocol not known in advance": {
        P: ("tested", "test_delegate.py::test_user_registration_delegate", "Registers a protocol and creates the delegate. No delegate call is received"),
        R: ("tested", "test_ObjCProtocol.py::test_interface_return_struct", "")},
    "F3.6 Selector targets": {
        P: ("partial", "test_delegate.py::test_user_registration_delegate", "Registers `NSNotificationCenter` observers. No notification is posted"),
        R: ("untested", None, "")},
    "F3.7 Delegate values": {
        "pyobjus-1.2.4": ("partial", "test_delegate.py::test_existing_delegate", "Object arguments only"),
        "pyobjus-master": ("tested", "test_delegate_returns.py::test_msgsend_double_return", ""),
        R: ("tested", "test_ObjCProtocol.py::test_interface_return_struct", "")},
    "F3.8 Removing a delegate": {
        P: ("unsupported", None, "No API"),
        R: ("unsupported", None, "Automatic, so there is no API to test")},
    "F4.1 Completion handlers": {
        P: ("unsupported", None, ""),
        R: ("tested", "test_blocks.py::test_block_receiver", "")},
    "F4.2 Received blocks": {
        P: ("unsupported", None, ""),
        R: ("tested", "test_blocks.py::test_block_round_trip", "")},
    "F4.3 GCD": {
        P: ("unsupported", None, ""),
        R: ("untested", None, "")},
    "F4.4 Function pointers": {
        P: ("unsupported", None, ""),
        R: ("partial", "test_ctypes_patch.py::test_patch_structure", "Makes Python functions into C function pointers with `ctypes` and calls them, to test Rubicon's patch for returning structs. None is passed to a C or Objective-C function")},
    "F5.1 Memory management": {
        "pyobjus-1.2.4": ("untested", None, ""),
        "pyobjus-master": ("tested", "test_object_lifecycle.py::test_returned_object", "See T5"),
        R: ("tested", "test_ObjCInstance.py::test_returned_lifecycle", "See T5")},
    "F5.2 Objective-C exceptions": {
        P: ("unsupported", None, ""),
        R: ("unsupported", None, "")},
    "F5.3 Event loops": {
        P: ("unsupported", None, ""),
        R: ("tested", "test_async.py::test_run_until_complete", "")},
    "F5.4 Main thread": {
        P: ("unsupported", None, "No API"),
        R: ("unsupported", None, "No API")},
    "F7.1 Finding Swift classes": {P: ("untested", None, ""), R: ("untested", None, "")},
    "F7.2 Swift values": {P: ("untested", None, ""), R: ("untested", None, "")},
    "F7.3 Throwing methods": {P: ("untested", None, "Partly supported"), R: ("untested", None, "")},
    "F7.4 `async` methods": {P: ("unsupported", None, ""), R: ("untested", None, "")},
    "F7.5 Swift protocols in Python": {P: ("untested", None, ""), R: ("untested", None, "")},
    "F7.6 Swift-only APIs": {P: ("unsupported", None, ""), R: ("unsupported", None, "")},
}


def entry(row, version):
    cells = ROWS[row]
    return cells.get(version) or cells[version.split("-")[0]]


def find(clones, version, cite):
    repo, ref, _ = REFS[version]
    path, name = cite.split("::")
    src = subprocess.run(["git", "-C", f"{clones}/{repo}", "show", f"{ref}:tests/{path}"],
                         capture_output=True, text=True).stdout
    if not src:
        return None
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node.lineno
    return None


def main():
    clones, out_json, out_md = sys.argv[1:4]
    data, missing = {}, []
    for row in ROWS:
        data[row] = {}
        for version in REFS:
            status, cite, note = entry(row, version)
            line = find(clones, version, cite) if cite else None
            if cite and line is None:
                missing.append((row, version, cite))
            repo, ref, slug = REFS[version]
            url = f"https://github.com/{slug}/blob/{ref}/tests/{cite.split('::')[0]}#L{line}" if line else None
            data[row][version] = {"status": status, "test": cite, "line": line, "url": url, "note": note}
    if missing:
        print("MISSING", missing)
        sys.exit(1)
    json.dump(data, open(out_json, "w"), indent=1)
    labels = {"tested": "Tested", "setup": "Setup only", "partial": "Partly", "untested": "Not tested",
              "unsupported": "Not supported"}
    with open(out_md, "w") as f:
        f.write("| Row | pyobjus 1.2.4 | pyobjus `master` | Rubicon 0.5.7 | Rubicon `main` |\n|---|---|---|---|---|\n")
        for row in ROWS:
            cells = []
            for version in REFS:
                c = data[row][version]
                text = labels[c["status"]]
                if c["url"]:
                    text += f": [`{c['test'].split('::')[1]}`]({c['url']})"
                if c["note"]:
                    text += f". {c['note']}"
                cells.append(text)
            f.write(f"| {row} | " + " | ".join(cells) + " |\n")
    counts = {v: {} for v in REFS}
    for row in ROWS:
        for v in REFS:
            s = data[row][v]["status"]
            counts[v][s] = counts[v].get(s, 0) + 1
    print(json.dumps(counts, indent=1))


if __name__ == "__main__":
    main()
