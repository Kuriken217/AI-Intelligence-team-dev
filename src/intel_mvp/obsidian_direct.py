from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

try:
    from .pipeline import PipelineResult, run_pipeline
    from .prior_knowledge import load_user_settings
    from .url_run import UrlRunResult, run_pipeline_from_urls
except ImportError:
    from pipeline import PipelineResult, run_pipeline
    from prior_knowledge import load_user_settings
    from url_run import UrlRunResult, run_pipeline_from_urls


DEFAULT_OBSIDIAN_OUTPUT_ROOT = "AI_Intelligence_Unit"


@dataclass(frozen=True)
class ObsidianWriteCheck:
    vault_path: Path
    output_root: Path
    ok: bool
    message: str


def resolve_obsidian_paths(settings_path: Path) -> tuple[Path, Path]:
    settings = load_user_settings(settings_path)
    vault_value = settings.get("obsidian_vault_path")
    if not vault_value:
        raise ValueError("obsidian_vault_path is required in the settings file.")

    vault_path = Path(vault_value)
    output_root_name = str(settings.get("obsidian_output_root", DEFAULT_OBSIDIAN_OUTPUT_ROOT)).strip()
    if not output_root_name:
        output_root_name = DEFAULT_OBSIDIAN_OUTPUT_ROOT

    output_root = vault_path / output_root_name
    validate_child_path(vault_path, output_root)
    return vault_path, output_root


def validate_child_path(parent: Path, child: Path) -> None:
    parent_abs = parent.resolve(strict=False)
    child_abs = child.resolve(strict=False)
    try:
        child_abs.relative_to(parent_abs)
    except ValueError as error:
        raise ValueError(f"Output path must stay inside the Obsidian vault: {child_abs}") from error


def check_obsidian_write(settings_path: Path) -> ObsidianWriteCheck:
    vault_path, output_root = resolve_obsidian_paths(settings_path)
    try:
        if not vault_path.exists():
            return ObsidianWriteCheck(vault_path, output_root, False, "Vault path does not exist.")

        output_root.mkdir(parents=True, exist_ok=True)
        test_path = output_root / ".codex_write_test.md"
        test_body = "# Codex Obsidian Write Test\n\nThis file confirms direct write access.\n"
        test_path.write_text(test_body, encoding="utf-8")
        read_back = test_path.read_text(encoding="utf-8")
        test_path.unlink()

        if read_back != test_body:
            return ObsidianWriteCheck(vault_path, output_root, False, "Write test read-back did not match.")

        return ObsidianWriteCheck(vault_path, output_root, True, "Direct Obsidian write check passed.")
    except OSError as error:
        return ObsidianWriteCheck(vault_path, output_root, False, str(error))


def run_pipeline_to_obsidian(request_path: Path, sources_path: Path, settings_path: Path) -> PipelineResult:
    _vault_path, output_root = resolve_obsidian_paths(settings_path)
    return run_pipeline(
        request_path=request_path,
        sources_path=sources_path,
        vault_path=output_root,
        run_root_path=output_root / "runs",
    )


def run_urls_to_obsidian(
    request_path: Path,
    url_sources_path: Path,
    settings_path: Path,
    work_dir: Path,
    enrich: bool = False,
    timeout_seconds: int = 15,
) -> UrlRunResult:
    _vault_path, output_root = resolve_obsidian_paths(settings_path)
    return run_pipeline_from_urls(
        request_path=request_path,
        url_sources_path=url_sources_path,
        vault_path=output_root,
        work_dir=work_dir,
        enrich=enrich,
        timeout_seconds=timeout_seconds,
        run_root_path=output_root / "runs",
    )
