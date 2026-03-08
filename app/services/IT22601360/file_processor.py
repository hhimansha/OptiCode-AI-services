"""
File Processor Service
Handles reading and validating multiple uploaded source files.
Student: IT22601360
"""

import os
from typing import List, Tuple, Optional
from dataclasses import dataclass

from app.utils.constants import SUPPORTED_LANGUAGES


# Build a flat map: extension -> language name
EXTENSION_TO_LANGUAGE: dict = {}
for lang, cfg in SUPPORTED_LANGUAGES.items():
    for ext in cfg.get("extensions", []):
        EXTENSION_TO_LANGUAGE[ext.lower()] = lang

# Max file size: 5 MB
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
# Max number of files processed per request
MAX_FILES = 50


@dataclass
class ProcessedFile:
    """Represents a single processed source file"""
    filename: str
    language: str
    code: str
    size_bytes: int
    skipped: bool = False
    skip_reason: Optional[str] = None


class FileProcessor:
    """
    Processes multiple uploaded files:
    - Detects language from file extension
    - Filters by supported extensions
    - Enforces per-file size limits
    """

    def detect_language(self, filename: str) -> Optional[str]:
        """Return language name for the given filename, or None if unsupported."""
        _, ext = os.path.splitext(filename)
        return EXTENSION_TO_LANGUAGE.get(ext.lower())

    def process_uploaded_files(
        self,
        files: List[Tuple[str, bytes]],
        language_override: Optional[str] = None,
    ) -> List[ProcessedFile]:
        """
        Process a list of (filename, bytes) tuples.

        Args:
            files: [(filename, file_bytes), ...]
            language_override: If set, force this language for all files.

        Returns:
            List of ProcessedFile objects (including skipped ones).
        """
        results: List[ProcessedFile] = []

        for i, (filename, content_bytes) in enumerate(files):
            if i >= MAX_FILES:
                results.append(ProcessedFile(
                    filename=filename,
                    language="unknown",
                    code="",
                    size_bytes=len(content_bytes),
                    skipped=True,
                    skip_reason=f"File limit of {MAX_FILES} reached"
                ))
                continue

            # Size check
            if len(content_bytes) > MAX_FILE_SIZE_BYTES:
                results.append(ProcessedFile(
                    filename=filename,
                    language="unknown",
                    code="",
                    size_bytes=len(content_bytes),
                    skipped=True,
                    skip_reason=f"File too large ({len(content_bytes) / 1024:.1f} KB > 5 MB)"
                ))
                continue

            # Language detection
            language = language_override or self.detect_language(filename)

            if not language:
                results.append(ProcessedFile(
                    filename=filename,
                    language="unknown",
                    code="",
                    size_bytes=len(content_bytes),
                    skipped=True,
                    skip_reason="Unsupported file extension"
                ))
                continue

            # Decode
            try:
                code = content_bytes.decode("utf-8", errors="replace")
            except Exception as e:
                results.append(ProcessedFile(
                    filename=filename,
                    language=language,
                    code="",
                    size_bytes=len(content_bytes),
                    skipped=True,
                    skip_reason=f"Could not decode file: {e}"
                ))
                continue

            results.append(ProcessedFile(
                filename=filename,
                language=language,
                code=code,
                size_bytes=len(content_bytes),
            ))

        return results

    def collect_from_directory(
        self,
        directory: str,
        language_filter: Optional[List[str]] = None,
        max_depth: int = 6,
    ) -> List[ProcessedFile]:
        """
        Walk a local directory and collect all supported source files.

        Args:
            directory: Absolute path to a local directory.
            language_filter: If set, only include these languages.
            max_depth: Maximum directory depth to recurse.

        Returns:
            List of ProcessedFile objects.
        """
        results: List[ProcessedFile] = []
        base_depth = directory.rstrip(os.sep).count(os.sep)

        for root, dirs, files in os.walk(directory):
            # Depth control
            current_depth = root.count(os.sep) - base_depth
            if current_depth >= max_depth:
                dirs.clear()
                continue

            # Skip hidden dirs and common noise folders
            dirs[:] = [
                d for d in dirs
                if not d.startswith(".")
                and d not in {"node_modules", "venv", ".venv", "__pycache__",
                              ".git", "dist", "build", "target", "vendor",
                              ".tox", "coverage", ".mypy_cache"}
            ]

            for fname in files:
                if len(results) >= MAX_FILES:
                    break

                fpath = os.path.join(root, fname)
                language = self.detect_language(fname)

                if not language:
                    continue

                if language_filter and language not in language_filter:
                    continue

                try:
                    size = os.path.getsize(fpath)
                    if size > MAX_FILE_SIZE_BYTES:
                        results.append(ProcessedFile(
                            filename=fpath,
                            language=language,
                            code="",
                            size_bytes=size,
                            skipped=True,
                            skip_reason="File too large"
                        ))
                        continue

                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        code = f.read()

                    results.append(ProcessedFile(
                        filename=fpath,
                        language=language,
                        code=code,
                        size_bytes=size,
                    ))
                except Exception as e:
                    results.append(ProcessedFile(
                        filename=fpath,
                        language=language,
                        code="",
                        size_bytes=0,
                        skipped=True,
                        skip_reason=str(e)
                    ))

        return results
