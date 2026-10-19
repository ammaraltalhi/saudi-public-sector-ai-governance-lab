import json
from pathlib import Path
import shutil

import pandas as pd
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
ALIGNMENT_PATH = ROOT / "data" / "sdaia_alignment.json"


def load_alignment():
    with ALIGNMENT_PATH.open(encoding="utf-8") as alignment_file:
        return json.load(alignment_file)


def test_alignment_dataset_covers_seven_unique_sdaia_principles():
    principles = load_alignment()["principles"]

    assert len(principles) == 7
    assert len({principle["name"] for principle in principles}) == 7
    assert {principle["name"] for principle in principles} == {
        "Fairness",
        "Privacy & Security",
        "Humanity",
        "Social & Environmental Benefits",
        "Reliability & Safety",
        "Transparency & Explainability",
        "Accountability & Responsibility",
    }


def test_alignment_dataset_references_only_catalogued_controls():
    alignment = load_alignment()
    controls = pd.read_csv(ROOT / "data" / "controls.csv")
    control_ids = set(controls["Control ID"])

    assert all(
        set(principle["controls"]) <= control_ids
        for principle in alignment["principles"]
    )


def test_annexure_c_references_follow_verified_official_principle_labels():
    principles = {
        principle["name"]: set(principle["references"]["annexure_c"])
        for principle in load_alignment()["principles"]
    }

    assert principles == {
        "Fairness": {
            "PD.10", "PD.11", "PD.12", "PD.13",
            "PID.9", "PID.10", "BV.8", "BV.9", "BV.12",
            "DM.8", "DM.9", "DM.10", "DM.11", "DM.12",
        },
        "Privacy & Security": {
            "PD.16", "PID.1", "PID.2", "PID.3", "PID.4", "PID.5", "PID.6",
            "DM.2", "DM.5", "DM.19",
        },
        "Humanity": {
            "PD.14", "PD.15", "PID.11", "PID.12", "BV.13", "DM.20",
        },
        "Social & Environmental Benefits": {
            "PID.13", "BV.10", "DM.13",
        },
        "Reliability & Safety": {
            "PID.14", "BV.1", "BV.2", "BV.3", "BV.4", "DM.4",
        },
        "Transparency & Explainability": {
            "PID.7", "BV.5", "BV.6", "BV.7", "DM.6", "DM.7",
        },
        "Accountability & Responsibility": {
            "PD.1", "PD.2", "PD.3", "PD.4", "PD.5", "PD.6", "PD.7",
            "PD.8", "PD.9", "PID.8", "BV.11", "DM.1", "DM.3",
            "DM.14", "DM.15", "DM.16", "DM.17", "DM.18",
        },
    }


def isolated_app(tmp_path, alignment_content=None, include_alignment=True):
    project_root = tmp_path / "isolated-project"
    data_directory = project_root / "data"
    views_directory = project_root / "views"
    data_directory.mkdir(parents=True)
    views_directory.mkdir()
    shutil.copyfile(ROOT / "data" / "controls.csv", data_directory / "controls.csv")
    shutil.copyfile(
        ROOT / "views" / "sdaia_alignment.py",
        views_directory / "sdaia_alignment.py",
    )
    if include_alignment:
        if alignment_content is None:
            shutil.copyfile(ALIGNMENT_PATH, data_directory / "sdaia_alignment.json")
        else:
            (data_directory / "sdaia_alignment.json").write_text(
                alignment_content,
                encoding="utf-8",
            )
    return AppTest.from_file(views_directory / "sdaia_alignment.py").run()


def assert_alignment_error(app, message):
    assert not app.exception
    assert any(message in item.value for item in app.error)


def test_missing_alignment_file_shows_error(tmp_path):
    app = isolated_app(tmp_path, include_alignment=False)

    assert_alignment_error(app, "SDAIA alignment data file is missing.")


def test_malformed_alignment_json_shows_error(tmp_path):
    app = isolated_app(tmp_path, alignment_content="{ not json")

    assert_alignment_error(app, "not valid UTF-8 JSON")


def test_incomplete_alignment_structure_shows_error(tmp_path):
    incomplete = json.dumps({"schema_version": 1, "source": {}, "principles": []})
    app = isolated_app(tmp_path, alignment_content=incomplete)

    assert_alignment_error(app, "missing required source details")


def test_unknown_control_id_shows_error(tmp_path):
    alignment = load_alignment()
    alignment["principles"][0]["controls"].append("UNKNOWN-99")
    app = isolated_app(tmp_path, alignment_content=json.dumps(alignment))

    assert_alignment_error(app, "references unknown controls: UNKNOWN-99")


def test_duplicate_principle_shows_error(tmp_path):
    alignment = load_alignment()
    alignment["principles"][1]["name"] = alignment["principles"][0]["name"]
    app = isolated_app(tmp_path, alignment_content=json.dumps(alignment))

    assert_alignment_error(app, "contains duplicate principles")


def test_missing_principle_shows_error(tmp_path):
    alignment = load_alignment()
    alignment["principles"].pop()
    app = isolated_app(tmp_path, alignment_content=json.dumps(alignment))

    assert_alignment_error(app, "exactly the seven named principles")


def test_sdaia_alignment_page_renders_read_only_crosswalk_and_disclaimer():
    app = AppTest.from_file(ROOT / "views" / "sdaia_alignment.py").run()

    assert not app.exception
    assert app.title[0].value == "SDAIA Framework Alignment"
    rendered_headings = {item.value for item in app.subheader}
    assert rendered_headings == {
        principle["name"] for principle in load_alignment()["principles"]
    }
    rendered_text = "\n".join(
        item.value.lower()
        for item in (*app.caption, *app.markdown, *app.info)
    )
    assert "illustrative analytical crosswalk" in rendered_text
    assert "not proof that a practice was implemented" in rendered_text
    assert "not sdaia certification" in rendered_text
    assert "principle-specific impact documentation" in rendered_text


def test_sdaia_alignment_is_registered_and_renders_through_app_navigation():
    app = AppTest.from_file(ROOT / "app.py").run()
    app.switch_page("views/sdaia_alignment.py").run()

    assert not app.exception
    assert app.title[0].value == "SDAIA Framework Alignment"
    assert {item.value for item in app.subheader} == {
        principle["name"] for principle in load_alignment()["principles"]
    }
