# pyobjus and Rubicon ObjC: a technical comparison

**Status: draft for factual review.** Nothing here has been reviewed by either project.

This repository holds an evidence-based comparison of [pyobjus](https://github.com/kivy/pyobjus) and [Rubicon ObjC](https://github.com/beeware/rubicon-objc). It supports the discussion in [kivy/kivy#9469](https://github.com/kivy/kivy/issues/9469), and all of its tests and raw data are shared so anyone can check the results.

**Author's role:** Elliot Garbus leads this comparison. Elliot opened the proposal in kivy/kivy#9469 and has stated a view there in favor of Rubicon, was the most active recent contributor to pyobjus, and builds KivyForge and kivy-mobile-wheels. Elliot has since stopped contributing to pyobjus because of the bugs and gaps encountered, won't land the 3 pyobjus PRs still open at the snapshot, is leaving those PRs and the 16 open issues Elliot filed for others to pick up, and now uses Rubicon and plans to contribute to it. Where this affects a result, the section says so.

**AI assistance:** data collection, analysis scripts and drafting were done with AI assistance (Claude, by Anthropic). Elliot Garbus directs the work, reviews it and is responsible for its content.

## Sections

Each section opens with a summary of findings, followed by the supporting facts. Sections make no recommendation. A recommendation, if any, is a separate section written after the comparison is complete.

| # | Section | Metric definitions | Status |
|---|---|---|---|
| 1 | [History and maintenance](sections/01-history-and-maintenance.md) | [Definitions](metrics/01-history-and-maintenance.md) | Draft for factual review |
| 2 | [Architecture](sections/02-architecture.md) | [Definitions](metrics/02-architecture.md) | Draft for factual review |
| 3 | [Capabilities and limitations](sections/03-capabilities.md) | [Definitions](metrics/03-capabilities.md) | Draft for factual review |
| 4 | [Side-by-side examples](sections/04-examples.md) | [Definitions](metrics/04-examples.md) | Draft for factual review |
| 5 | [Testing and CI](sections/05-testing-and-ci.md) | [Definitions](metrics/05-testing-and-ci.md) | Draft for factual review |
| 6 | [Performance](sections/06-performance.md) | [Definitions](metrics/06-performance.md) | Draft for factual review |
| 7 | [Ecosystem considerations](sections/07-ecosystem.md) | [Definitions](metrics/07-ecosystem.md) | Draft for factual review |
| 8 | [Compatibility and migration](sections/08-compatibility-and-migration.md) | [Definitions](metrics/08-compatibility-and-migration.md) | Draft for factual review |

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
