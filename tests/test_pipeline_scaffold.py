"""Phase 1 smoke coverage for the documented CLI contract."""

from src.pipeline import main


def test_mock_mode_is_api_key_free(capsys: object, tmp_path: object) -> None:
    """The initial mock entry point must be runnable before integrations exist."""
    assert main(["--mode", "mock", "--output-dir", str(tmp_path)]) == 0
    assert "Validated story map" in capsys.readouterr().out  # type: ignore[attr-defined]
