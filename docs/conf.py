from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

project = "klc-llm-pipeline"
author = "Kellogg RS"
copyright = "2026"
release = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinxarg.ext",
]

autosummary_generate = True
autodoc_member_order = "bysource"

templates_path = ["_templates"]
exclude_patterns = []

html_theme = "sphinx_rtd_theme"

html_static_path = ["_static"]

