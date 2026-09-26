"""Dataset validation for JARVIS-X."""
from pathlib import Path
import json


class DatasetValidator:
    """Validates dataset files and structure."""

    def __init__(self, dataset_dir: str):
        """
        Initialize the validator.
        
        Args:
            dataset_dir: Path to dataset directory.
        """
        self.dataset_dir = Path(dataset_dir)

    def validate_directory(self, directory: str) -> str:
        """
        Validate all files in a directory.
        
        Args:
            directory: Directory path to validate.
            
        Returns:
            str: Validation report.
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            return f"✗ Directory does not exist: {directory}"

        files = list(dir_path.glob("*"))
        if not files:
            return f"ℹ Directory is empty: {directory}"

        report_lines = [f"✓ Validation Report for: {directory}"]
        valid_count = 0
        error_count = 0

        for file in files:
            if file.is_file():
                try:
                    if file.suffix == ".json":
                        with open(file) as f:
                            json.load(f)
                        report_lines.append(f"  ✓ {file.name}")
                        valid_count += 1
                    else:
                        report_lines.append(f"  ~ {file.name} (unknown format)")
                except Exception as e:
                    report_lines.append(f"  ✗ {file.name}: {e}")
                    error_count += 1

        report_lines.append(f"\nSummary: {valid_count} valid, {error_count} errors")
        return "\n".join(report_lines)
