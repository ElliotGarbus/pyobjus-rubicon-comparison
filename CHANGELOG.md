# Changelog

Corrections and changes to published sections, newest first.

## section-7-draft-1

First public draft of Section 7, for factual review.

Section 1 said first-party and downstream dependents would be covered in Section 7. Section 7 counts public code that imports each library, and Kivy's and Plyer's own use of pyobjus moved to Section 8, so Section 1 now says so.

## section-6-draft-4

Section 6 now explains Rubicon's larger memory footprint on import. On the Mac, 10.4 MB of its 11.7 MB comes from two standard-library calls Rubicon makes at import: `importlib.metadata`, to read its version number, and `platform.processor()`. Rubicon's own modules add 0.85 MB after them. A new measurement, `rubicon_import.py`, gives each step.

## section-6-draft-3

Section 6 no longer reports M3 footprint figures for Rubicon, which draft 2 gave as memory kept after objects were freed. Every object was freed. The figures are memory freed and held by the allocator, raised after `alloc` then `init` by a reference cycle that CPython's `ctypes.cast` leaves for the cycle collector, so they aren't Rubicon's memory use. The evidence is in the results.

PyObjC, measured on the Mac as a reference, is no longer shown in the section, which compares pyobjus and Rubicon. Its figures remain in the results.

## section-6-draft-2

Section 6 now gives the cause of pyobjus's `CGRect` slowdown, which draft 1 said wasn't investigated. pyobjus adds the address of every struct argument to a list it never clears, `ctypes_struct_cache`, and searches the whole list on every struct return. A new measurement, `cgrect_cache.py`, confirms it: clearing the list restores the original speed. Each such call also keeps about 48 bytes of Python memory, which is added to claim 7's amounts.

## section-6-draft-1

First public draft of Section 6, for factual review.

## section-5-draft-1

First public draft of Section 5, for factual review.

## section-4-draft-1

First public draft of Section 4, for factual review.

## section-3-draft-1

First public draft of Section 3, for factual review.

## section-2-draft-2

Corrected Section 2's statement that Rubicon blocks and function pointers can't return structs, after [freakboy3742 questioned it](https://github.com/kivy/kivy/issues/9469#issuecomment-6649760982). They raise `TypeError` until the struct type is patched, and defining a Python method that returns the type patches it. Changed the summary table, finding 5 and the CB2 results. Added 5 scenarios, run on the Mac only.

## section-2-draft-1

First public draft of Section 2, for factual review.

## section-1-draft-1

First public draft of Section 1, for factual review.
