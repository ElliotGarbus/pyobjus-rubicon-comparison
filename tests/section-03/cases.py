"""The Section 3 cases: each one's F row, what it checks and its expected value.

Each library's file (`cases_pyobjus.py`, `cases_rubicon.py`, `cases_pyobjc.py`)
implements the cases with that library's public API. A case ID ending in
`__ctypes` or `__helper` is the workaround for the case without the suffix,
written only where the library can't do the case itself. It has the same
expected value.

Comparison is strict about `bool`: `False` doesn't match `0`.
"""


class NotExpressible(Exception):
    """The library has no public way to write this case."""


class NotApplicable(Exception):
    """The case tests something this library doesn't have to do."""


class Check:
    """An observed value with an expected value known only at run time."""

    def __init__(self, observed, expected):
        self.observed = observed
        self.expected = expected


RUNTIME = object()  # the case returns a Check

# F1.6 needs a framework the process hasn't loaded yet. iOS loads CoreLocation
# at launch, so the first framework on this list that isn't loaded is used.
FRAMEWORKS = [("CoreLocation", "CLLocation"), ("Contacts", "CNContact"), ("EventKit", "EKEvent"),
              ("HealthKit", "HKHealthStore"), ("HomeKit", "HMHome")]

CASES = {
    # F1. Calling Objective-C and C
    "f1_1_class_method": ("F1.1", "NSURL URLWithString: then absoluteString", "https://kivy.org/a/b"),
    "f1_1_multipart": ("F1.1", "stringByReplacingOccurrencesOfString:withString:", "a+b"),
    "f1_1_multipart_held": ("F1.1", "The same call, with the arguments held in variables first", "a+b"),
    "f1_2_property_attr": ("F1.2", "NSURLComponents.host written and read as an attribute", "kivy.org"),
    "f1_2_property_methods": ("F1.2", "NSURLComponents setHost: and host", "kivy.org"),
    "f1_3_format": ("F1.3", "NSString stringWithFormat: with %ld and %@", "7-x"),
    "f1_3_array_with_objects": ("F1.3", "NSArray arrayWithObjects: ending in nil, then count", 2),
    "f1_4_object_constant": ("F1.4", "NSLocaleCountryCode, against the fixture's value", RUNTIME),
    "f1_4_scalar_constant": ("F1.4", "NSFoundationVersionNumber, against the fixture's value", RUNTIME),
    "f1_5_function": ("F1.5", "NSStringFromClass(NSArray)", "NSArray"),
    "f1_5_function_struct": ("F1.5", "NSRangeFromString(@\"{3, 4}\"), which returns a struct", (3, 4)),
    "f1_6_framework": ("F1.6", "Load the first system framework not already loaded (CoreLocation, Contacts, EventKit, "
                               "HealthKit, HomeKit), then find its class", RUNTIME),
    "f1_6_dylib": ("F1.6", "Load the app's own dylib, then call +[S3Extra answer]", 42),
    "f1_7_dir": ("F1.7", "dir() on an NSURLComponents instance lists host", True),

    # F2. Types
    "f2_1_user_struct": ("F2.1", "A struct the user defines {int, float, char}, passed and returned", (1, 2.5, 99)),
    "f2_1_struct_pointer_in": ("F2.1", "A pointer to a CGRect, read by Objective-C", 10.0),
    "f2_1_struct_pointer_out": ("F2.1", "A pointer to a CGRect, filled by Objective-C", (1.0, 2.0, 3.0, 4.0)),
    "f2_2_union_arg": ("F2.2", "A union {int, float} passed by value", 7),
    "f2_2_union_return": ("F2.2", "A union {int, float} returned by value", 7),
    "f2_2_bitfield_arg": ("F2.2", "A struct with bit fields 3, 5 and 8 wide, passed by value", 222),
    "f2_2_bitfield_return": ("F2.2", "A struct with bit fields, returned by value", (5, 17, 200)),
    "f2_3_fixed_array": ("F2.3", "An int[4] argument", 10),
    "f2_3_pass_array": ("F2.3", "An int array with a separate count", 10),
    "f2_3_fill_array": ("F2.3", "An int array that Objective-C fills", [0, 1, 4, 9]),
    "f2_3_struct_array_field": ("F2.3", "A struct holding int[4], passed and returned", [1, 2, 3, 4]),
    "f2_4_scalar_out": ("F2.4", "divide:by:quotient: with an NSInteger out parameter", (True, 3)),
    "f2_4_opaque_pointer": ("F2.4", "A CGColorRef returned, then passed back to read its alpha", 0.5),
    "f2_4_error_out": ("F2.4", "An NSError ** out parameter, then its domain and code", ("S3", 42)),
    "f2_5_list_arg": ("F2.5", "A Python list passed where an NSArray is expected", 3),
    "f2_5_dict_arg": ("F2.5", "A Python dict passed where an NSDictionary is expected", "v"),
    "f2_5_to_py": ("F2.5", "An NSArray of strings converted to Python by an explicit call", ["a", "b", "c"]),
    "f2_5_from_py": ("F2.5", "A Python list converted to an NSArray by an explicit call", 2),
    "f2_5_bool_number": ("F2.5", "@[@YES, @NO, @1] converted to Python", [True, False, 1]),
    "f2_6_len": ("F2.6", "len() of an NSArray", 3),
    "f2_6_index": ("F2.6", "Indexing an NSArray", "b"),
    "f2_6_iter": ("F2.6", "Iterating an NSArray", ["a", "b", "c"]),
    "f2_6_in": ("F2.6", "`in` on an NSDictionary", True),
    "f2_6_dict_index": ("F2.6", "Indexing an NSDictionary by key", 2),
    "f2_6_str_ops": ("F2.6", "An NSString compared with a str, and upper()", (True, "HELLO")),
    "f2_7_enum": ("F2.7", "compare: against a named NSComparisonResult constant", True),

    # F3. Defining Objective-C behavior in Python
    "f3_1_instance_method": ("F3.1", "An NSObject subclass whose s3Value Objective-C calls", 11),
    "f3_1_class_method": ("F3.1", "An NSObject subclass whose class method Objective-C calls", 12),
    "f3_2_override_super": ("F3.2", "An NSDateFormatter subclass overriding stringFromDate: and calling super", RUNTIME),
    "f3_3_property_kvc": ("F3.3", "A property on a Python class, read by Objective-C through valueForKey:", 5),
    "f3_3_python_state": ("F3.3", "A Python attribute read by a method Objective-C calls", 21),
    "f3_4_apple_protocol": ("F3.4", "An NSXMLParserDelegate collecting element names", ["root", "item"]),
    "f3_5_app_protocol": ("F3.5", "A protocol declared only by the app, implemented with no registration", 8),
    "f3_5_app_protocol_registered": ("F3.5", "The same protocol, with its encodings registered at runtime", 8),
    "f3_6_notification": ("F3.6", "An NSNotificationCenter observer method", "S3Note"),
    "f3_6_timer": ("F3.6", "An NSTimer target method", True),
    "f3_7_union_arg": ("F3.7", "A delegate method receiving a union", 9),
    "f3_7_array_arg": ("F3.7", "A delegate method receiving an int array and count", 9),
    "f3_7_bool_return": ("F3.7", "A delegate method returning BOOL YES", True),
    "f3_7_object_return": ("F3.7", "A delegate method returning a string", "label-3"),

    # F4. Blocks and function pointers
    "f4_1_sort_comparator": ("F4.1", "sortedArrayUsingComparator: with a Python comparator", ["a", "b", "c"]),
    "f4_1_enumerate_stop": ("F4.1", "enumerateObjectsUsingBlock:, setting *stop after 2 objects", 2),
    "f4_1_completion": ("F4.1", "A completion handler called later on another thread", 49),
    "f4_1_completion__helper": ("F4.1", "The same through an Objective-C helper that calls a delegate", 49),
    "f4_2_delegate_completion": ("F4.2", "A delegate method calling the block it receives", 1),
    "f4_3_dispatch_main": ("F4.3", "dispatch_async to the main queue, run on the main thread", True),
    "f4_4_sort_function": ("F4.4", "sortedArrayUsingFunction:context: with a Python function", ["a", "b", "c"]),

    # F5. Runtime services
    "f5_3_asyncio_cf": ("F5.3", "An NSTimer firing while asyncio runs on the library's Core Foundation loop", True),
    "f5_4_perform_on_main": ("F5.4", "A Python method run on the main thread, asked for from a Python thread", True),

    # F7. Swift
    "f7_1_named_class": ("F7.1", "S3Notebook by its @objc name: initWithTitle: and addNote:", 1),
    "f7_1_generated_name": ("F7.1", "A class with no @objc name, by Swift's generated name", 7),
    "f7_2_string": ("F7.2", "A Swift let String", "Groceries"),
    "f7_2_property_write": ("F7.2", "A Swift var written then read", "Kivy"),
    "f7_2_scalars": ("F7.2", "Swift Double and Bool returns", (0.25, True)),
    "f7_2_optional_nil": ("F7.2", "A Swift String? returning nil", None),
    "f7_2_string_array": ("F7.2", "A Swift [String]", ["x"]),
    "f7_2_int_array": ("F7.2", "A Swift [Int]", [0, 1, 4, 9]),
    "f7_2_nested_dict": ("F7.2", "A nested Swift [String: Any] containing a Bool",
                         {"count": 2, "isEmpty": False, "nested": {"a": [1, 2]}}),
    "f7_2_list_arg": ("F7.2", "A Python list passed as [String]", 3),
    "f7_2_dict_arg": ("F7.2", "A Python dict passed as [String: Any]", "Swift"),
    "f7_3_success": ("F7.3", "A throwing method that succeeds", "x"),
    "f7_3_failure_value": ("F7.3", "A throwing method that throws: the value returned", None),
    "f7_3_read_error": ("F7.3", "A throwing method that throws: the NSError's domain", "S3Swift.NotebookError"),
    "f7_4_completion": ("F7.4", "An async method's completion handler", "hello"),
    "f7_4_throwing_completion": ("F7.4", "An async throws method's handler: (result is nil, error is set)", (True, True)),
    "f7_5_tick_main": ("F7.5", "A Swift protocol method receiving an Int, called on the main thread", [1, 2, 3]),
    "f7_5_bool_return": ("F7.5", "Swift reading a Bool return", [True, True, False]),
    "f7_5_int_return": ("F7.5", "Swift reading an Int return", [10, 20, 30]),
    "f7_5_object_return": ("F7.5", "Swift reading a String return", ["t1", "t2", "t3"]),
    "f7_5_background": ("F7.5", "Called on a thread Swift creates: (ticks, any on the main thread)", ([1, 2, 3], False)),
    "f7_5_exception": ("F7.5", "The first tick raises: (Swift's ticks in that run, ticks in a second run)", (3, 3)),
}


def base(case_id):
    return case_id.split("__")[0]


def expected(case_id):
    return CASES[case_id][2]


def same(a, b):
    """Equality that doesn't treat bool as int, and treats tuples and lists alike."""
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, float) or isinstance(b, float):
        try:
            return abs(a - b) < 1e-9
        except TypeError:
            return False
    return a == b
