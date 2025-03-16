import subprocess
from datetime import datetime
import os

current_time = datetime.now()

python_path = "" # python path from your env or lap

manage_py_path = ""  # manage.py path

try:
    print("Starting Django server...")
    server_command = f"{python_path} {manage_py_path} runserver"
    os.system(server_command)

    if current_time.hour < 10:
        print("Running mark_absent.py before 10:00 AM...")
        mark_absent_command = [python_path, "management\commands\mark_absent.py"] # mark_absent.py path
        result = subprocess.run(mark_absent_command, capture_output=True, text=True)

        print("Output from mark_absent.py:")
        print(result.stdout)
        if result.stderr:
            print("Errors from mark_absent.py:")
            print(result.stderr)
    else:
        print("Current time is after 10:00 AM. Skipping mark_absent.py.")

except Exception as e:
    print(f"An error occurred: {e}")
