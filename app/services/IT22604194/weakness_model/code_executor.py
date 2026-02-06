import subprocess
import uuid
import os

def run_python(code):
    filename = f"temp_{uuid.uuid4().hex}.py"

    with open(filename, "w") as f:
        f.write(code)

    try:
        result = subprocess.run(
            ["python", filename],
            capture_output=True,
            text=True,
            timeout=5
        )

        return {
            "output": result.stdout,
            "error": result.stderr
        }

    except subprocess.TimeoutExpired:
        return {
            "output": "",
            "error": "Time limit exceeded"
        }

    finally:
        if os.path.exists(filename):
            os.remove(filename)
