from __future__ import annotations

import sys

from .config import get_config
from .run_collect import main as collect_main
from .run_enrich import main as enrich_main
from .run_score import main as score_main
from .run_user_score import main as user_score_main


def _run_step(label: str, func, index: int, total: int) -> None:
    print(f"[pipeline] Step {index}/{total}: {label}...")
    try:
        func()
    except Exception as exc:
        print(
            f"[pipeline] ERROR during '{label}': {exc}",
            file=sys.stderr,
        )
        sys.exit(1)


def main() -> None:
    total_steps = 4
    print(
        "[pipeline] Starting full Reddit pipeline (collect → enrich → score → user_score)..."
    )

    _run_step("Collect posts", collect_main, 1, total_steps)
    _run_step("Enrich users", enrich_main, 2, total_steps)
    _run_step("Score posts", score_main, 3, total_steps)
    _run_step("Score users", user_score_main, 4, total_steps)

    cfg = get_config()
    print("\n[pipeline] All steps completed successfully.")
    print("[pipeline] Outputs:")
    print(f"  raw_posts:         {cfg.paths.raw_posts_path}")
    print(f"  users_enriched:    {cfg.paths.users_enriched_path}")
    print(f"  posts_scored_csv:  {cfg.paths.posts_scored_path}")
    print(f"  posts_scored_jsonl:{cfg.paths.posts_scored_jsonl_path}")
    print(f"  users_scored_csv:  {cfg.paths.users_scored_path}")
    users_scored_jsonl_path = getattr(cfg.paths, "users_scored_jsonl_path", None)
    if users_scored_jsonl_path is not None:
        print(f"  users_scored_jsonl:{users_scored_jsonl_path}")

    print("\n[pipeline] Done.")


if __name__ == "__main__":
    main()
