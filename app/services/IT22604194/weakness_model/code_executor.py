import subprocess
import uuid
import os

def run_python(code, test_input=""):
    filename = f"temp_{uuid.uuid4().hex}.py"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(code)

    try:
        result = subprocess.run(
            ["python", filename],
            input=test_input,
            capture_output=True,
            text=True,
            timeout=5
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

    finally:
        if os.path.exists(filename):
            os.remove(filename)
