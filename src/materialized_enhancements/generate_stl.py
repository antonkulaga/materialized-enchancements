"""Generate 3D-printable STL/OBJ files from protein structures using Jmol + 3DP-Jmol.

3DP-Jmol (MIT, Mihasan & Herráez) converts macromolecular structures into
printable meshes with proper scale factors, strut generation, and rendering styles.

Jmol (Java) is downloaded on first use to ~/.local/share/jmol/.
Override with --jmol-jar or JMOL_JAR env var.
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
from enum import Enum
from pathlib import Path

import typer

log = logging.getLogger(__name__)

STRUCTURES_DIR = Path("data/input/structures")
OUTPUT_DIR = Path("data/output/stl")
SCRIPT_PATH = Path(__file__).resolve().parent.parent.parent / "scripts" / "3dp_jmol" / "3DP-Jmol.v.alfa1.public"

JMOL_HOME = Path.home() / ".local" / "share" / "jmol"
JMOL_VERSION = "16.3.55"
_JMOL_MAJOR_MINOR = ".".join(JMOL_VERSION.split(".")[:2])
JMOL_DOWNLOAD_URL = (
    "https://sourceforge.net/projects/jmol/files/"
    f"Jmol/Version%20{_JMOL_MAJOR_MINOR}/Jmol%20{JMOL_VERSION}/"
    f"Jmol-{JMOL_VERSION}-binary.tar.gz/download"
)


class RenderStyle(str, Enum):
    cartoon = "cartoon"
    backbone = "backbone"
    trace = "trace"
    ribbon = "ribbon"
    ballandstick = "ballandstick"
    sesurface = "sesurface"
    sasurface = "sasurface"
    spacefill = "spacefill"


def _ensure_java() -> str:
    java_cmd = shutil.which("java")
    if not java_cmd:
        raise typer.BadParameter(
            "Java is required but not found in PATH. "
            "Install a JRE/JDK (e.g. `sudo apt install default-jre`)."
        )
    result = subprocess.run([java_cmd, "-version"], capture_output=True, text=True)
    version_line = result.stderr.strip().splitlines()[0] if result.stderr else "unknown"
    typer.echo(f"Java: {version_line}")
    return java_cmd


def _find_jmol_jar(jmol_jar: Path | None = None) -> Path | None:
    if jmol_jar and jmol_jar.exists():
        return jmol_jar

    env_jar = os.environ.get("JMOL_JAR")
    if env_jar:
        p = Path(env_jar)
        if p.exists():
            return p

    jar_dir = JMOL_HOME / f"jmol-{JMOL_VERSION}"
    jar_path = jar_dir / "Jmol.jar"
    if jar_path.exists():
        return jar_path

    candidates = sorted(JMOL_HOME.rglob("Jmol.jar"))
    if candidates:
        return candidates[0]

    return None


def _download_jmol() -> Path:
    JMOL_HOME.mkdir(parents=True, exist_ok=True)

    typer.echo(f"Downloading Jmol {JMOL_VERSION} (~80 MB) from SourceForge...")
    with tempfile.TemporaryDirectory() as tmpdir:
        archive = Path(tmpdir) / "jmol.tar.gz"
        curl_cmd = shutil.which("curl")
        wget_cmd = shutil.which("wget")

        if curl_cmd:
            subprocess.run(
                [curl_cmd, "-L", "-o", str(archive), JMOL_DOWNLOAD_URL],
                check=True,
            )
        elif wget_cmd:
            subprocess.run(
                [wget_cmd, "-O", str(archive), JMOL_DOWNLOAD_URL],
                check=True,
            )
        else:
            raise RuntimeError("Neither curl nor wget found. Install one to download Jmol.")

        if not archive.exists() or archive.stat().st_size < 1_000_000:
            raise RuntimeError(f"Download failed or file too small: {archive}")

        typer.echo("Extracting...")
        with tarfile.open(archive, "r:gz") as tar:
            tar.extractall(JMOL_HOME, filter="data")

    jar_path = JMOL_HOME / f"jmol-{JMOL_VERSION}" / "Jmol.jar"
    if not jar_path.exists():
        candidates = sorted(JMOL_HOME.rglob("Jmol.jar"))
        if candidates:
            jar_path = candidates[0]
        else:
            raise FileNotFoundError(
                f"Jmol.jar not found after extraction in {JMOL_HOME}. "
                "Download manually from https://jmol.sourceforge.net/ and set JMOL_JAR."
            )

    typer.echo(f"Jmol installed at {jar_path}")
    return jar_path


def _find_or_download_jmol(jmol_jar: Path | None = None) -> Path:
    found = _find_jmol_jar(jmol_jar)
    if found:
        return found
    return _download_jmol()


def _parametrize_script(
    template: str,
    pdb_path: Path,
    output_path: Path,
    style: str,
    scale: float,
    hydrogen: bool,
    color: bool,
) -> str:
    s = template

    h_val = "on" if hydrogen else "off"
    s = re.sub(r"var hydrogenAtoms = '(?:on|off)'", f"var hydrogenAtoms = '{h_val}'", s)

    s = re.sub(r"PrintScaleFactorUser = [\d.]+;", f"PrintScaleFactorUser = {scale};", s)

    c_val = "yes" if color else "no"
    s = re.sub(r"colorPrinter = '(?:yes|no)'", f"colorPrinter = '{c_val}'", s, count=1)

    pdb_abs = str(pdb_path.resolve()).replace("\\", "/")
    s = re.sub(r"^load =.*$", f'load "{pdb_abs}"', s, flags=re.MULTILINE)

    s = re.sub(r'opt = "[^"]*"', f'opt = "{style}"', s, count=1)

    out_abs = str(output_path.resolve()).replace("\\", "/")
    s = re.sub(r"write test_color\.obj;", f'write "{out_abs}";', s)
    s = re.sub(r"write test\.stl;", f'write "{out_abs}";', s)

    return s


def _run_jmol(
    java_cmd: str,
    jmol_jar: Path,
    script_content: str,
    timeout: int = 300,
) -> subprocess.CompletedProcess[str]:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".spt", delete=False) as f:
        f.write(script_content)
        script_file = Path(f.name)

    try:
        return subprocess.run(
            [java_cmd, "-jar", str(jmol_jar), "-n", "-s", str(script_file)],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    finally:
        script_file.unlink(missing_ok=True)


def convert_pdb_to_stl(
    pdb_path: Path,
    output_path: Path,
    java_cmd: str,
    jmol_jar: Path,
    template: str,
    style: str = "cartoon",
    scale: float = 0,
    hydrogen: bool = False,
    color: bool = False,
    timeout: int = 300,
) -> bool:
    script = _parametrize_script(template, pdb_path, output_path, style, scale, hydrogen, color)
    try:
        result = _run_jmol(java_cmd, jmol_jar, script, timeout=timeout)
    except subprocess.TimeoutExpired:
        typer.echo(f"    FAIL (timeout after {timeout}s)")
        return False

    if result.returncode != 0:
        typer.echo(f"    FAIL (exit {result.returncode})")
        for line in (result.stderr or "").strip().splitlines()[-5:]:
            typer.echo(f"      {line}")
        return False

    if output_path.exists() and output_path.stat().st_size > 0:
        size_kb = output_path.stat().st_size / 1024
        typer.echo(f"    OK ({size_kb:.0f} KB)")
        return True

    typer.echo("    FAIL (output file not created)")
    for line in (result.stdout or "").strip().splitlines()[-5:]:
        typer.echo(f"      {line}")
    return False


app = typer.Typer(help="Generate 3D-printable STL/OBJ from protein structures via Jmol + 3DP-Jmol.")


@app.command("setup")
def setup(
    jmol_jar: Path | None = typer.Option(None, "--jmol-jar", envvar="JMOL_JAR", help="Path to existing Jmol.jar"),
) -> None:
    """Download Jmol and verify the full pipeline is ready."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    typer.echo("=== Setup: protein structure → STL pipeline ===\n")

    typer.echo("1. Checking Java...")
    java_cmd = _ensure_java()

    typer.echo("\n2. Checking Jmol...")
    found = _find_jmol_jar(jmol_jar)
    if found:
        typer.echo(f"   Jmol.jar found at {found}")
    else:
        typer.echo("   Jmol not found, downloading...")
        found = _download_jmol()
    jar = found

    typer.echo("\n3. Checking 3DP-Jmol script...")
    if SCRIPT_PATH.exists():
        typer.echo(f"   Script found at {SCRIPT_PATH}")
    else:
        typer.echo(f"   MISSING: {SCRIPT_PATH}", err=True)
        raise typer.Exit(1)

    typer.echo("\n4. Checking protein structures...")
    if STRUCTURES_DIR.exists():
        pdbs = list(STRUCTURES_DIR.glob("*.pdb"))
        typer.echo(f"   Found {len(pdbs)} PDB files in {STRUCTURES_DIR}")
    else:
        typer.echo(f"   No structures directory at {STRUCTURES_DIR}")
        typer.echo("   Run `uv run download-structures` first.")

    typer.echo("\n5. Quick Jmol smoke test...")
    test_script = 'load DATA "pdb"\nATOM      1  CA  ALA A   1       0.000   0.000   0.000  1.00  0.00\nEND\nend "pdb"\nprint "SMOKE_TEST_OK"\n'
    result = _run_jmol(java_cmd, jar, test_script, timeout=30)
    if "SMOKE_TEST_OK" in (result.stdout or ""):
        typer.echo("   Jmol runs OK (headless)")
    else:
        typer.echo("   WARNING: Jmol smoke test did not print expected output.")
        typer.echo(f"   stdout: {(result.stdout or '')[:200]}")
        typer.echo(f"   stderr: {(result.stderr or '')[:200]}")

    typer.echo("\n=== Setup complete ===")
    typer.echo("Run `uv run stl generate --all` to convert all structures.")


@app.command("generate")
def generate(
    pdb_files: list[Path] = typer.Argument(None, help="PDB file(s) to convert. Use --all for batch."),
    all_structures: bool = typer.Option(False, "--all", help="Process all PDB files in data/input/structures/"),
    style: RenderStyle = typer.Option(RenderStyle.cartoon, "--style", "-s", help="Rendering style"),
    scale: float = typer.Option(0, "--scale", help="Print scale (0 = auto-max, 0.3 = 30%%)"),
    hydrogen: bool = typer.Option(False, "--hydrogen/--no-hydrogen", help="Include hydrogen atoms"),
    color: bool = typer.Option(False, "--color/--no-color", help="Multicolor OBJ instead of monochrome STL"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing outputs"),
    output_dir: Path = typer.Option(OUTPUT_DIR, "--output-dir", "-o", help="Output directory"),
    jmol_jar: Path | None = typer.Option(None, "--jmol-jar", envvar="JMOL_JAR", help="Path to Jmol.jar"),
    timeout: int = typer.Option(300, "--timeout", help="Per-structure timeout in seconds"),
) -> None:
    """Convert PDB protein structures to 3D-printable STL (or OBJ) files."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if all_structures:
        if not STRUCTURES_DIR.exists():
            typer.echo(f"Structures directory not found: {STRUCTURES_DIR}", err=True)
            raise typer.Exit(1)
        files = sorted(STRUCTURES_DIR.glob("*.pdb"))
    elif pdb_files:
        files = [f for f in pdb_files if f.suffix.lower() == ".pdb"]
    else:
        typer.echo("Provide PDB file(s) as arguments or use --all to batch-convert.", err=True)
        raise typer.Exit(1)

    if not files:
        typer.echo("No PDB files found.", err=True)
        raise typer.Exit(1)

    if not SCRIPT_PATH.exists():
        typer.echo(f"3DP-Jmol script not found at {SCRIPT_PATH}", err=True)
        raise typer.Exit(1)
    template = SCRIPT_PATH.read_text()

    java_cmd = _ensure_java()
    jar = _find_or_download_jmol(jmol_jar)

    output_dir.mkdir(parents=True, exist_ok=True)
    ext = ".obj" if color else ".stl"

    typer.echo(f"Converting {len(files)} structure(s) → {style.value} {ext} @ scale={scale or 'auto'}")
    typer.echo(f"Output: {output_dir.resolve()}\n")

    succeeded = 0
    failed = 0
    skipped = 0

    for pdb in files:
        if not pdb.exists():
            typer.echo(f"  SKIP {pdb.name} (file not found)")
            skipped += 1
            continue

        out_name = f"{pdb.stem}_{style.value}{ext}"
        out_path = output_dir / out_name

        if out_path.exists() and not force:
            typer.echo(f"  SKIP {pdb.name} → {out_name} (exists, use --force)")
            skipped += 1
            continue

        typer.echo(f"  [{succeeded + failed + 1}/{len(files) - skipped}] {pdb.name} → {out_name}")
        ok = convert_pdb_to_stl(
            pdb_path=pdb,
            output_path=out_path,
            java_cmd=java_cmd,
            jmol_jar=jar,
            template=template,
            style=style.value,
            scale=scale,
            hydrogen=hydrogen,
            color=color,
            timeout=timeout,
        )
        if ok:
            succeeded += 1
        else:
            failed += 1

    typer.echo(f"\nDone: {succeeded} succeeded, {failed} failed, {skipped} skipped")
    if failed:
        raise typer.Exit(1)


def main() -> None:
    app()
