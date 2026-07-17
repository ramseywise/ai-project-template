# nbks/ — analysis notebooks

Exploratory analyses kept as plain `.py` scripts in the percent/py:percent
style (git-diffable, runnable headless via `make nbks-corpus`, openable as
notebooks in VS Code/Jupytext).

- `corpus_analysis.py` — corpus statistics for the ingested article set
  (sizes, categories, token distributions) to sanity-check ingestion before
  trusting retrieval quality numbers.

Convention: notebooks are read-only consumers of `core/` and the data dirs —
no pipeline logic lives here. Promote anything reusable into a real module
with tests.
