from pathlib import Path

NEEDLE = "codex" + "test"
TEXT_EXTENSIONS = {
    ".py",
    ".pyi",
    ".md",
    ".txt",
    ".sh",
    ".bat",
    ".ps1",
    ".toml",
    ".json",
    ".yml",
    ".yaml",
    ".cfg",
    ".ini",
}
TEXT_FILENAMES = {"Dockerfile", "Makefile", ".gitignore", "LICENSE", "README"}
SKIP_DIRS = {".git", ".venv", "__pycache__"}


def is_text_file(path: Path) -> bool:
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return True
    return path.name in TEXT_FILENAMES


def should_skip(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return True
    return any(part in SKIP_DIRS for part in parts)


def test_repository_has_no_codex_marker() -> None:
    root = Path(__file__).resolve().parents[1]
    offenders: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if should_skip(path, root):
            continue
        if not is_text_file(path):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = path.read_text(encoding="utf-8", errors="ignore")
        if NEEDLE in content.lower():
            offenders.append(path)
    assert not offenders, (
        "Remove stale references to the codex/test marker in: "
        + ", ".join(str(path) for path in offenders)
    )
