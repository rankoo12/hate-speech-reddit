from __future__ import annotations

from src.config import get_config


def test_get_config_creates_data_dir_and_paths_are_under_it(tmp_path, monkeypatch):
    """
    Basic sanity check: get_config() should ensure data_dir exists, and all
    known paths should live under that directory.
    """
    # Override BASE_DIR/data indirectly by changing cwd if needed.
    # Here we just call get_config() and assert structure is sane.
    cfg = get_config()

    data_dir = cfg.paths.data_dir
    assert data_dir.exists()
    assert data_dir.is_dir()

    # All important paths should be inside data_dir
    assert str(cfg.paths.raw_posts_path).startswith(str(data_dir))
    assert str(cfg.paths.users_enriched_path).startswith(str(data_dir))
    assert str(cfg.paths.posts_scored_path).startswith(str(data_dir))
    assert str(cfg.paths.posts_scored_jsonl_path).startswith(str(data_dir))
    assert str(cfg.paths.users_scored_path).startswith(str(data_dir))
