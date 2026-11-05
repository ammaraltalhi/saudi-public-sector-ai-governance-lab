"""Translate presentation only; keep workflow values and exported cases canonical."""
import re
from functools import wraps
from pathlib import Path

import streamlit as _st

LANGUAGE_KEY = "interface_language"
_ARABIC = dict(
    line.split("\t", 1)
    for line in Path(__file__).with_name("arabic.tsv").read_text(encoding="utf-8").splitlines()
    if line and not line.startswith("# ")
)
_TEMPLATES = [(re.compile(re.escape(key).replace(re.escape("{value}"), "(.+?)")),
               text.split("{value}")) for key, text in _ARABIC.items() if "{value}" in key]
_DISPLAY_COLUMNS = {
    "Applicability", "Evidence Status", "Readiness Impact", "Status", "status",
    "Governance Area", "Control", "Operational requirement", "Stage", "Risk Level",
    "Risk Level Source", "inherent_level", "residual_level", "methodology",
    "category", "residual_basis", "treatment_strategy", "Owner", "Evidence", "Frequency",
    "AI System", "Business Owner", "Purpose", "Data Categories", "Human Oversight",
    "Current blockers and actions", "Lifecycle follow-up",
}
_TEXT_METHODS = {
    "title", "header", "subheader", "caption", "markdown", "write", "info",
    "success", "warning", "error", "checkbox", "text_input", "text_area",
    "selectbox", "number_input", "button", "form_submit_button", "download_button",
    "file_uploader", "metric", "expander",
}
_RTL = """
<style>
[data-testid="stMain"], [data-testid="stSidebar"], [data-baseweb="popover"] {
    direction: rtl;
    text-align: start;
}
[data-testid="stMain"] input, [data-testid="stMain"] textarea { text-align: start; }
[data-testid="stDataFrame"], [data-testid="stJson"], pre, code { direction: ltr; }
[data-testid="stNumberInput"] input { direction: ltr; }
</style>
"""


def arabic():
    return _st.session_state.get(LANGUAGE_KEY) == "ar"


def tr(value):
    if not arabic() or not isinstance(value, str):
        return value
    return _translate(value)


def _translate(value):
    key = " ".join(value.split())
    if key in _ARABIC:
        return _ARABIC[key]
    # Bilingual labels are defined by the underlying Saudi methodology.
    if re.fullmatch(r"[^\n—]+ — [\u0600-\u06ff ]+", value):
        return value.split(" — ", 1)[1]
    if key.startswith("**") and key.endswith("**"):
        return "**" + _translate(key[2:-2]) + "**"
    for pattern, pieces in _TEMPLATES:
        match = pattern.fullmatch(key)
        if match:
            return pieces[0] + "".join(_ARABIC.get(part, part) + tail
                                      for part, tail in zip(match.groups(), pieces[1:]))
    prefix = re.match(r"^(\*\*)?([^:\n]+):(\*\*)? (.+)$", value, re.S)
    if prefix:
        opening, label, closing, rest = prefix.groups()
        if label in _ARABIC:
            return f"{opening or ''}{_ARABIC[label]}:{closing or ''} {_ARABIC.get(rest, rest)}"
    numbered = re.match(r"^((?:\d+[:.]|[•-]) )(.+)$", value)
    if numbered:
        return numbered[1] + _translate(numbered[2])
    rating = re.fullmatch(r"(\d+ — )(.+)", value)
    if rating:
        return rating[1] + _translate(rating[2])
    return value


def display_table(value):
    if not arabic():
        return value
    import pandas as pd
    from pandas.io.formats.style import Styler

    if isinstance(value, Styler):
        value = value.data
    if isinstance(value, list) and all(isinstance(row, dict) for row in value):
        value = pd.DataFrame(value)
    if not isinstance(value, pd.DataFrame):
        return value
    result = value.copy()
    for name in result.columns:
        if name in _DISPLAY_COLUMNS:
            result[name] = result[name].map(tr)
    result.columns = [tr(name) for name in result.columns]
    if not isinstance(result.index, pd.RangeIndex):
        result.index = result.index.map(tr)
    return result


class _UI:
    """Small adapter around the display APIs used by the existing pages."""

    def __init__(self, target):
        self._target = target

    def __enter__(self):
        return self._target.__enter__()

    def __exit__(self, *args):
        return self._target.__exit__(*args)

    def __getattr__(self, name):
        fn = getattr(self._target, name)
        if name in _TEXT_METHODS or name in {"Page", "table", "dataframe", "data_editor"}:
            @wraps(fn)
            def localized(*args, **kwargs):
                if not arabic():
                    return fn(*args, **kwargs)
                if name in {"dataframe", "table"} and args:
                    args = (display_table(args[0]), *args[1:])
                if name == "data_editor":
                    columns = kwargs.get("column_config", {})
                    kwargs["column_config"] = {key: {**config, "label": tr(config.get("label", key))}
                                               for key, config in columns.items()}
                if name in _TEXT_METHODS and args:
                    args = (tr(args[0]), *args[1:])
                for key in ("label", "title", "help", "placeholder"):
                    if key in kwargs:
                        kwargs[key] = tr(kwargs[key])
                if name == "selectbox":
                    format_value = kwargs.get("format_func", str)
                    kwargs["format_func"] = lambda option: _translate(str(format_value(option)))
                if name == "metric" and len(args) > 1:
                    args = (args[0], tr(args[1]), *args[2:])
                return fn(*args, **kwargs)
            return localized
        if name == "columns":
            return lambda *args, **kwargs: [_UI(column) for column in fn(*args, **kwargs)]
        return fn


st = _UI(_st)


def language_picker():
    _st.sidebar.selectbox(
        "اللغة / Language", ("en", "ar"), key=LANGUAGE_KEY,
        format_func={"en": "English", "ar": "العربية"}.get,
    )
    if arabic():
        _st.markdown(_RTL, unsafe_allow_html=True)
