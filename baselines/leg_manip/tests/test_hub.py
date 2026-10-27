from concurrent.futures import ThreadPoolExecutor, TimeoutError
from pathlib import Path
from threading import Event
from types import SimpleNamespace
from zipfile import ZipFile

import pytest

from leg_manip import hub


def _mock_hub(monkeypatch, files):
    monkeypatch.setattr(
        hub,
        "HfApi",
        lambda: SimpleNamespace(
            repo_info=lambda *a, **kw: SimpleNamespace(sha="a" * 40)
        ),
    )
    monkeypatch.setattr(
        hub, "hf_hub_download", lambda repo, name, **kw: str(files[name])
    )


def _archive(tmp_path, name="press_button.zarr.zip"):
    path = tmp_path / name
    with ZipFile(path, "w") as archive:
        archive.writestr("press_button.zarr/.zgroup", '{"zarr_format": 2}')
        archive.writestr("press_button.zarr/data/value", "complete")
    return path


def test_download_preserves_task_subdirectories(tmp_path, monkeypatch):
    a, b = tmp_path / "a", tmp_path / "b"
    a.write_text("button weights")
    b.write_text("dishwasher weights")
    _mock_hub(monkeypatch, {"button/model.bin": a, "dishwasher/model.bin": b})
    first, _ = hub.download("user/models", "button/model.bin", out_dir=tmp_path / "out")
    second, _ = hub.download(
        "user/models", "dishwasher/model.bin", out_dir=tmp_path / "out"
    )
    assert first != second
    assert first.read_text() == "button weights"
    assert second.read_text() == "dishwasher weights"


def test_download_renamed_archive_returns_existing_dataset(tmp_path, monkeypatch):
    archive = _archive(tmp_path)
    _mock_hub(monkeypatch, {"nested/renamed.zarr.zip": archive})
    path, sha = hub.download(
        "user/data", "nested/renamed.zarr.zip", out_dir=tmp_path / "out"
    )
    assert sha == "a" * 40
    assert path.name == "renamed.zarr"
    assert path.parent.name == "nested"
    assert (path / "data/value").read_text() == "complete"


def test_download_repairs_incomplete_legacy_extraction(tmp_path, monkeypatch):
    archive = _archive(tmp_path)
    _mock_hub(monkeypatch, {archive.name: archive})
    target = tmp_path / "out/user__data" / ("a" * 12) / "press_button.zarr"
    target.mkdir(parents=True)
    (target / ".zgroup").write_text('{"zarr_format": 2}')
    path, _ = hub.download("user/data", archive.name, out_dir=tmp_path / "out")
    assert (path / "data/value").read_text() == "complete"


def test_concurrent_download_waits_for_complete_extraction(tmp_path, monkeypatch):
    archive = _archive(tmp_path)
    _mock_hub(monkeypatch, {archive.name: archive})
    entered, release = Event(), Event()
    original = ZipFile.extractall

    def slow_extract(self, path, *args, **kwargs):
        partial = Path(path) / "press_button.zarr"
        partial.mkdir(parents=True, exist_ok=True)
        entered.set()
        assert release.wait(5)
        return original(self, path, *args, **kwargs)

    monkeypatch.setattr(ZipFile, "extractall", slow_extract)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(
            hub.download, "user/data", archive.name, out_dir=tmp_path / "out"
        )
        assert entered.wait(5)
        second = pool.submit(
            hub.download, "user/data", archive.name, out_dir=tmp_path / "out"
        )
        try:
            with pytest.raises(TimeoutError):
                second.result(timeout=0.2)
        finally:
            release.set()
        for future in (first, second):
            path, _ = future.result(timeout=5)
            assert (path / "data/value").read_text() == "complete"
