from __future__ import annotations

from pathlib import Path

try:
    from .prior_knowledge import load_user_settings
except ImportError:
    from prior_knowledge import load_user_settings


def main() -> int:
    settings = load_user_settings(Path("config/user_settings.json"))
    vault_path = Path(settings["obsidian_vault_path"])

    try:
        exists = vault_path.exists()
    except OSError as error:
        print(f"exists=false")
        print(f"error={ascii(str(error))}")
        return 1

    print(f"exists={str(exists).lower()}")
    if exists:
        markdown_count = sum(1 for _ in vault_path.rglob("*.md"))
        print(f"markdown_count={markdown_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
