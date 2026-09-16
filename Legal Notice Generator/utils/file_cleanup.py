import os
import time
import threading
from pathlib import Path

EXPIRY_SECONDS = 300

def cleanup_generated_files(folder):

    folder = Path(folder)

    while True:

        now = time.time()

        for file in folder.glob("*"):

            try:

                if file.is_file():

                    age = now - file.stat().st_mtime

                    if age > EXPIRY_SECONDS:

                        file.unlink()

                        print(f"[CLEANUP] Deleted {file.name}")

            except Exception as e:

                print(e)

        time.sleep(10)


def start_cleanup(folder):

    thread = threading.Thread(
        target=cleanup_generated_files,
        args=(folder,),
        daemon=True
    )

    thread.start()