"""
=============================================================================
  OptiCode - Unified Backend Launcher
=============================================================================
  Single file to install all requirements and start all Python backend services:
    1. Refactoring API (Flask)       - Port 8000
    2. Risk Analysis API (Flask)     - Port 8001
    3. Learning Content API (Flask)  - Port 8002
    4. Main FastAPI App (Uvicorn)    - Port 8003

  Usage:
    python run_backend.py                  (install + start all)
    python run_backend.py --skip-install   (start without installing)
=============================================================================
"""

import subprocess
import sys
import os
import time
import signal
import socket
from pathlib import Path

# ── Fix Windows emoji encoding issue ──
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ── Paths ──
REFACTOR_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = REFACTOR_DIR.parent
ROOT_DIR = BACKEND_DIR.parent.parent

# ── Requirements files ──
REQUIREMENTS_FILES = [
    REFACTOR_DIR / "requirements.txt",       # Flask services (IT22606860)
    BACKEND_DIR / "requirements.txt",         # Main FastAPI app
]

# ── Service definitions ──
SERVICES = [
    {
        "name": "Refactoring API (Flask)",
        "script": str(REFACTOR_DIR / "refactor_api.py"),
        "cwd": str(REFACTOR_DIR),
        "port": 8000,
        "health": "/health",
        "description": "100+ Refactoring Patterns, Architecture Analysis",
    },
    {
        "name": "Risk Analysis API (Flask)",
        "script": str(REFACTOR_DIR / "risk_analysis_api.py"),
        "cwd": str(REFACTOR_DIR),
        "port": 8001,
        "health": "/health",
        "description": "AI-Powered Risk Assessment",
    },
    {
        "name": "Learning Content API (Flask)",
        "script": str(REFACTOR_DIR / "learning_api.py"),
        "cwd": str(REFACTOR_DIR),
        "port": 8002,
        "health": "/health",
        "description": "50+ Educational Topics",
    },
    {
        "name": "Main FastAPI App (Uvicorn)",
        "script": None,  # launched via uvicorn module
        "cwd": str(BACKEND_DIR),
        "port": 8003,
        "health": "/",
        "description": "Concept Extraction & AI Services",
        "uvicorn_app": "app.main:app",
    },
]

# ── Store processes for cleanup ──
processes = []


# ─────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────

def print_banner(text, char="=", width=80):
    print(char * width)
    print(f"  {text}")
    print(char * width)


def port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def install_requirements():
    """Install all Python requirements."""
    print_banner("STEP 1: Installing Python Requirements")
    for req_file in REQUIREMENTS_FILES:
        if not req_file.exists():
            print(f"  [SKIP] {req_file}  (file not found)")
            continue
        print(f"\n  Installing from: {req_file}")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file), "--quiet"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f"  [OK] Installed successfully")
        else:
            print(f"  [WARN] Some packages may have failed:")
            for line in result.stderr.strip().splitlines()[-5:]:
                print(f"         {line}")
    print()


def start_service(service):
    """Start a single service as a subprocess."""
    name = service["name"]
    port = service["port"]

    if port_in_use(port):
        print(f"  [SKIP] {name} - port {port} already in use")
        return None

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    # Disable Flask's debug mode to prevent reloader subprocess issues
    env["FLASK_DEBUG"] = "0"

    try:
        if service.get("uvicorn_app"):
            # FastAPI via uvicorn
            cmd = [
                sys.executable, "-m", "uvicorn",
                service["uvicorn_app"],
                "--host", "0.0.0.0",
                "--port", str(port),
            ]
        else:
            cmd = [sys.executable, "-u", service["script"]]

        # Create log file for service output
        log_file_path = REFACTOR_DIR / f"{service['name'].lower().replace(' ', '_').replace('(', '').replace(')', '')}.log"
        log_file = open(log_file_path, "w", encoding="utf-8")
        
        proc = subprocess.Popen(
            cmd,
            cwd=service["cwd"],
            stdout=log_file,
            stderr=subprocess.STDOUT,
            env=env,
        )

        # Wait briefly and check it didn't crash immediately
        time.sleep(4)
        if proc.poll() is not None:
            print(f"  [FAIL] {name} exited immediately (code {proc.returncode})")
            log_file.close()
            return None

        print(f"  [OK] {name:35} -> http://localhost:{port}")
        print(f"       Log: {log_file_path}")
        return proc

    except Exception as e:
        print(f"  [FAIL] {name}: {e}")
        return None


def health_check():
    """Check if each service responds on its health endpoint."""
    import urllib.request
    print_banner("Health Check")
    all_ok = True
    for svc in SERVICES:
        url = f"http://localhost:{svc['port']}{svc['health']}"
        # Retry up to 3 times with 2 second delays
        for attempt in range(3):
            try:
                resp = urllib.request.urlopen(url, timeout=5)
                print(f"  [OK]   {svc['name']:35} {url}  ({resp.status})")
                break
            except Exception:
                if attempt < 2:
                    time.sleep(2)
                else:
                    print(f"  [DOWN] {svc['name']:35} {url}")
                    all_ok = False
    return all_ok


def shutdown(sig=None, frame=None):
    """Graceful shutdown of all services."""
    print("\n")
    print_banner("Shutting down all services...")
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    print("  All services stopped.\n")
    sys.exit(0)


# ─────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────

def main():
    signal.signal(signal.SIGINT, shutdown)
    if sys.platform == "win32":
        signal.signal(signal.SIGBREAK, shutdown)

    skip_install = "--skip-install" in sys.argv

    print()
    print_banner("OptiCode - Unified Backend Launcher")
    print(f"  Python  : {sys.version.split()[0]}")
    print(f"  Root    : {ROOT_DIR}")
    print(f"  Backend : {BACKEND_DIR}")
    print()

    # ── Step 1: Install requirements ──
    if not skip_install:
        install_requirements()
    else:
        print("  [SKIP] Requirement installation (--skip-install flag)\n")

    # ── Step 2: Start all services ──
    print_banner("STEP 2: Starting All Python Backend Services")
    print()
    for svc in SERVICES:
        proc = start_service(svc)
        if proc:
            processes.append(proc)
        time.sleep(1)

    if not processes:
        print("\n  [ERROR] No services started! Check errors above.\n")
        sys.exit(1)

    print(f"\n  {len(processes)}/{len(SERVICES)} services started.\n")

    # ── Step 3: Health check ──
    time.sleep(2)
    health_check()

    # ── Summary ──
    print()
    print_banner("ALL SERVICES RUNNING")
    print()
    print("  Service Endpoints:")
    for svc in SERVICES:
        print(f"    {svc['name']:35} http://localhost:{svc['port']}")
    print()
    print("  API Quick Reference:")
    print("    POST http://localhost:8000/api/refactor             - Basic refactoring")
    print("    POST http://localhost:8000/api/priority-refactor    - Top 20 patterns")
    print("    POST http://localhost:8000/api/advanced-refactor    - 100+ patterns")
    print("    POST http://localhost:8000/api/architecture-analyze - Architecture")
    print("    POST http://localhost:8000/api/generate-tests       - Generate tests")
    print("    POST http://localhost:8001/api/risk-analyze         - Risk analysis")
    print("    GET  http://localhost:8002/api/categories           - Learning topics")
    print("    POST http://localhost:8003/concepts/extract         - Concept extraction")
    print()
    print("  Risk Detection & Performance Optimization (NEW):")
    print("    POST http://localhost:8000/api/risk/filesystem      - Filesystem security")
    print("    POST http://localhost:8000/api/risk/injection       - Injection vulnerabilities")
    print("    POST http://localhost:8000/api/risk/resources       - Resource leaks")
    print("    POST http://localhost:8000/api/perf/memory          - Memory optimization")
    print("    POST http://localhost:8000/api/perf/caching         - Caching optimization")
    print("    POST http://localhost:8000/api/unified-risk-perf    - FULL 5-stage pipeline")
    print("    POST http://localhost:8000/api/quick-risk-scan      - Quick security scan")
    print("    POST http://localhost:8000/api/quick-perf-scan      - Quick perf scan")
    print()
    print("  Press Ctrl+C to stop all services.")
    print_banner("", char="-")
    print()

    # ── Keep alive & monitor ──
    try:
        while True:
            time.sleep(5)
            for i, proc in enumerate(processes):
                if proc is not None and proc.poll() is not None:
                    print(f"  [WARN] Service process {i+1} stopped (exit code {proc.returncode})")
                    processes[i] = None
            # Remove dead processes from list
            active = [p for p in processes if p is not None]
            if not active:
                print("  [ERROR] All services have stopped!")
                sys.exit(1)
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()
