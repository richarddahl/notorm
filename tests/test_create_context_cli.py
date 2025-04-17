import sys
import subprocess
from pathlib import Path


def test_create_context(tmp_path):
    # Define context name and output directory
    context_name = "MyContext"
    output_dir = tmp_path / "mycontext"
    # Run the CLI script to create context
    # Use project root as working directory
    project_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-m", "src.scripts.ddd_lib", "create-context", context_name, "--output", str(output_dir)],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    # CLI should exit successfully
    assert result.returncode == 0, result.stderr
    # Verify that each layer directory exists
    for layer in ("domain", "application", "infrastructure", "api"):  # noqa: WPS336
        layer_path = output_dir / layer
        assert layer_path.is_dir(), f"Missing layer directory: {layer_path}"