# pyobjus and Rubicon ObjC: a technical comparison

**Status: draft, not yet published.** Nothing here has been reviewed by either project.

This repository holds an evidence-based comparison of [pyobjus](https://github.com/kivy/pyobjus) and [Rubicon ObjC](https://github.com/beeware/rubicon-objc). It supports the discussion in [kivy/kivy#9469](https://github.com/kivy/kivy/issues/9469), and all of its tests and raw data are shared so anyone can check the results.

**Author's role:** Elliot Garbus leads this comparison. Elliot opened the proposal in kivy/kivy#9469 and has stated a view there in favor of Rubicon, was the most active recent contributor to pyobjus, and builds KivyForge and kivy-mobile-wheels. Elliot has since stopped contributing to pyobjus because of the bugs and gaps encountered, won't land the 3 pyobjus PRs still open at the snapshot, and now uses Rubicon and plans to contribute to it. Where this affects a result, the section says so.

**AI assistance:** data collection, analysis scripts and drafting were done with AI assistance (Claude, by Anthropic). Elliot Garbus directs the work, reviews it and is responsible for its content.

## Sections

Each section opens with a summary of findings, followed by the supporting facts. Sections make no recommendation. A recommendation, if any, is a separate section written after the comparison is complete.

| # | Section | Metric definitions | Status |
|---|---|---|---|
| 1 | [History and maintenance](sections/01-history-and-maintenance.md) | [Definitions](metrics/01-history-and-maintenance.md) | Draft, awaiting review |
| 2 | Architecture | | Not started |
| 3 | Capabilities and limitations | | Not started |
| 4 | Side-by-side examples | | Not started |
| 5 | Testing and CI | | Not started |
| 6 | Performance | | Not started |
| 7 | Ecosystem considerations | | Not started |
| 8 | Compatibility and migration | | Not started |

## Layout

- [METHODOLOGY.md](METHODOLOGY.md): evidence labels, version baseline, test platforms and working definitions
- [CLAIMS.md](CLAIMS.md): claims from the discussion that this comparison tests
- [CHANGELOG.md](CHANGELOG.md): corrections and changes to published sections
- `sections/`: the comparison itself
- `metrics/`: what each section measures, defined before the data is collected
- `scripts/`: data collection and analysis
- `results/`: raw data and derived results, by section and snapshot date
- `benchmarks/`: performance tests
- `examples/`: side-by-side example code

## Corrections

If a fact here is wrong, please open an issue or pull request with a source. Corrections are logged in the changelog.

## License

The text, code and derived results in this repository are available under the [MIT License](LICENSE). Data collected from GitHub, PyPI and other sources remains subject to those sources' terms.
