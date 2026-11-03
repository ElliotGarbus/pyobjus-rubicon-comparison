# Methodology

## Evidence labels

Each factual claim carries one of these labels.

| Label | Meaning |
|---|---|
| **Measured** | We ran it, and the script, versions and raw output are included. |
| **Source** | Read in the code or official docs, and linked at a pinned commit or version. |
| **Reported** | Stated in an issue or discussion and linked, but not independently confirmed. |
| **Inferred** | Our reasoning from the evidence above, with that reasoning shown. |
| **Unknown** | Couldn't be established, with a note on what would settle it. |

## Rules

1. Every fact is checked against a primary source.
2. Every number that changes over time carries the date it was collected.
3. Each section's metrics are defined and approved before its data is collected. Any later change to a definition is recorded with the reason.
4. Sections report findings only. They make no recommendation and use no composite scores.
5. Every claim about either project gets the same checks, whoever made it.

## Versions

Each project is compared at two points:

- its latest release on PyPI
- its default branch, pinned to an exact commit

Each finding says which point it applies to. One pinned baseline covers Sections 2 to 6, so changes landing during the study don't shift results between sections. Everything is rerun against the latest versions before any recommendation is written.

Section 1 uses its own dated snapshot, because it measures history up to a point in time.

## Test platforms

| Platform | Used for |
|---|---|
| Apple Silicon Mac | Behavior and benchmarks |
| Physical iPhone | Behavior and benchmarks |
| iOS simulator | Behavior only; simulator timings are not reported as device performance |

Intel Macs are out of scope.

iOS benchmarks use a minimal app without Kivy on Python 3.15, built with KivyForge and kivy-mobile-wheels, so Kivy doesn't add noise to the timings. A separate Kivy app tests whether the two libraries coexist. Both the tool and the wheels are maintained by this comparison's author, so build steps are included for others to follow.

## Working definitions

### Options under discussion

The thread in kivy/kivy#9469 raises three options. The comparison collects the facts needed to assess all of them, and doesn't choose between them.

- **A:** Rubicon ObjC becomes Kivy's first-party bridge and pyobjus is frozen.
- **B:** Kivy keeps pyobjus and fills its gaps.
- **C:** Kivy stays neutral between bridges.

### Freeze

"Freeze" means no new features, with critical fixes only, on a best-effort basis and with no named owner. It carries no commitment to wheels for new Python versions.

### Other bridges

pyobjc and PySwiftKit get a short note rather than a full comparison. pyobjc is still counted in the migration scope wherever Kivy uses it.
