import argparse
from rich_argparse import RichHelpFormatter
from main import Precheck
from main import NewImageHandler
from watchdog.observers import Observer
import os
from main import logger
import time
from pathlib import Path
from main import load_and_check_folders
def main():
    observer = Observer()
    handler = NewImageHandler()

    watched_any = False
    for d in WATCH_DIRS:    
        full_path = os.path.expanduser(d)
        if os.path.isdir(full_path):
            observer.schedule(handler, full_path, recursive=True)
            logger.info(f"Watching: {full_path}")
            watched_any = True
        else:
            logger.warning(f"Skipping missing folder: {full_path}")

    if not watched_any:
        logger.error("No valid folders to watch. Exiting.")
        return

    observer.start()
    logger.info("Metadata wiper running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

parser = argparse.ArgumentParser(
    description="Item manager",
    formatter_class=RichHelpFormatter
)


parser.add_argument(
    "-f", "--folder",
    type=str,
    help="Folder to watch for new images. Can be specified multiple times.",
    action="append",
    default=[]
)

args = parser.parse_args()

if args.folder:
    WATCH_DIRS = args.folder
    load_and_check_folders(WATCH_DIRS)
    for d in WATCH_DIRS:
        full_path = os.path.expanduser(d)
        Precheck.check_folder(full_path)
    main()


