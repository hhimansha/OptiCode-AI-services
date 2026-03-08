import subprocess
import uuid
import os
import sys

# Always write temp files to the same folder as this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def run_python(code, test_input=""):
    filename = os.path.join(BASE_DIR, f"temp_{uuid.uuid4().hex}.py")

    with open(filename, "w", encoding="utf-8") as f:
        f.write(code)

    try:
        result = subprocess.run(
            [sys.executable, filename],
            input=test_input if test_input else None,
            capture_output=True,
            text=True,
            timeout=5,
            encoding="utf-8"
        )

        return {
            "output": result.stdout.strip(),
            "error": result.stderr.strip()
        }

    except subprocess.TimeoutExpired:
        return {
            "output": "",
            "error": "Time limit exceeded"
        }

    except Exception as e:
        return {
            "output": "",
            "error": str(e)
        }

    finally:
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass