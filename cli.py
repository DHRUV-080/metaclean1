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
from platformdirs import user_log_dir, user_config_dir

from main import save_folders,load_saved_folders
restart_option = False
WATCH_DIRS = load_saved_folders()

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
    logger.info("Metadata wiper running. Press Ctrl+C to stop... Press Ctrl+V to add another folder to watch.")
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
parser.add_argument('-r','--restart',action='store_true',help='Automatically launch the script on system startup. This will add a cron job for the current user.')
parser.add_argument('--forget',action='store_true',help='Forget all previously saved folders to watch. This will clear the saved configuration.')
args = parser.parse_args()
if args.restart:
    restart_option = True
    ## restart logic here
    print("Setting up automatic launch on system startup...")
if args.forget:
    save_folders([])
    print("All saved folders have been forgotten.")
if args.folder:
    WATCH_DIRS.extend(args.folder)
    save_folders(WATCH_DIRS)
    load_and_check_folders(WATCH_DIRS)
    for d in WATCH_DIRS:
        full_path = os.path.expanduser(d)
        Precheck.check_folder(full_path)
    main()
if restart_option == True:
    main()


