"""
Repository Processor Service
Handles cloning GitHub repos to a temp directory and collecting source files.
Student: IT22601360
"""

import os
import re
import shutil
import tempfile
from typing import List, Optional, Tuple
from dataclasses import dataclass

from app.services.IT22601360.file_processor import FileProcessor, ProcessedFile


@dataclass
class RepoMetadata:
    """Metadata about the cloned repository"""
    repo_url: str
    branch: str
    clone_dir: str
    total_files_found: int
    languages_found: List[str]


class RepoProcessor:
    """
    Clones a GitHub repository and collects supported source files.

    Uses GitPython if available; falls back to a subprocess git call.
    Always cleans up the temp directory after collecting files.
    """

    def __init__(self):
        self.file_processor = FileProcessor()
        self._check_git_available()

    def _check_git_available(self):
        """Check which git method is available"""
        try:
            import git  # noqa: F401
            self._use_gitpython = True
        except ImportError:
            self._use_gitpython = False

    def _validate_github_url(self, url: str) -> str:
        """Validate and normalize a GitHub URL"""
        url = url.strip()
        # Accept https:// and git@github.com: formats
        github_https = re.match(
            r'^https://github\.com/[\w\-\.]+/[\w\-\.]+(?:\.git)?$', url
        )
        github_ssh = re.match(
            r'^git@github\.com:[\w\-\.]+/[\w\-\.]+(?:\.git)?$', url
        )
        if not github_https and not github_ssh:
            raise ValueError(
                f"Invalid GitHub URL: '{url}'. "
                "Expected format: https://github.com/user/repo"
            )
        # Normalize to https
        if github_ssh:
            url = url.replace("git@github.com:", "https://github.com/").replace(".git", "")
        if not url.endswith(".git"):
            url = url + ".git"
        return url

    def _clone_repo(self, url: str, clone_dir: str, branch: Optional[str]) -> None:
        """Clone the repository into clone_dir"""
        if self._use_gitpython:
            import git
            kwargs = {"depth": 1}  # Shallow clone for speed
            if branch:
                kwargs["branch"] = branch
            try:
                git.Repo.clone_from(url, clone_dir, **kwargs)
            except git.exc.GitCommandError as e:
                raise RuntimeError(f"Git clone failed: {e}") from e
        else:
            # Fallback: subprocess
            import subprocess
            cmd = ["git", "clone", "--depth", "1"]
            if branch:
                cmd += ["-b", branch]
            cmd += [url, clone_dir]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                raise RuntimeError(
                    f"Git clone failed (returncode={result.returncode}): {result.stderr[:500]}"
                )

    def clone_and_collect(
        self,
        repo_url: str,
        branch: Optional[str] = None,
        language_filter: Optional[List[str]] = None,
    ) -> Tuple[List[ProcessedFile], RepoMetadata]:
        """
        Clone a GitHub repo and collect all supported source files.

        Args:
            repo_url: GitHub HTTPS or SSH URL.
            branch: Branch to clone. Defaults to the repo's default branch.
            language_filter: Only include these languages (e.g. ['python', 'javascript']).

        Returns:
            (list of ProcessedFile, RepoMetadata)
        """
        validated_url = self._validate_github_url(repo_url)
        effective_branch = branch or "main"

        # Create a temporary directory for the clone
        clone_dir = tempfile.mkdtemp(prefix="opticode_repo_")

        try:
            print(f"🔄 Cloning {validated_url} (branch={effective_branch}) to {clone_dir}...")
            try:
                self._clone_repo(validated_url, clone_dir, effective_branch)
            except RuntimeError:
                # Try 'master' if 'main' fails and no branch was specified
                if not branch and effective_branch == "main":
                    print("⚠️  'main' branch not found, trying 'master'...")
                    shutil.rmtree(clone_dir, ignore_errors=True)
                    clone_dir = tempfile.mkdtemp(prefix="opticode_repo_")
                    self._clone_repo(validated_url, clone_dir, "master")
                    effective_branch = "master"
                else:
                    raise

            print(f"✅ Clone successful. Collecting source files...")

            # Collect files from the cloned directory
            files = self.file_processor.collect_from_directory(
                directory=clone_dir,
                language_filter=language_filter,
                max_depth=6,
            )

            languages = list({f.language for f in files if not f.skipped})

            metadata = RepoMetadata(
                repo_url=repo_url,
                branch=effective_branch,
                clone_dir=clone_dir,
                total_files_found=len(files),
                languages_found=sorted(languages),
            )

            print(f"📁 Found {len(files)} source files in {len(languages)} language(s)")
            return files, metadata

        finally:
            # Always clean up the cloned temp directory
            try:
                shutil.rmtree(clone_dir, ignore_errors=True)
                print(f"🧹 Cleaned up temp dir: {clone_dir}")
            except Exception as cleanup_err:
                print(f"⚠️  Cleanup warning: {cleanup_err}")
