from pathlib import Path

import release


def test_get_integration_name(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    integration_dir = Path("custom_components/huesyncbox")
    integration_dir.mkdir(parents=True)
    Path("custom_components/__pycache__").mkdir()

    assert release.get_integration_name() == "huesyncbox"
