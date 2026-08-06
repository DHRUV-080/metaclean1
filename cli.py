import argparse
from rich_argparse import RichHelpFormatter
from main import Precheck
from main import NewImageHandler
from watchdog.observers import Observer
import os
from main import logger
from main import load_and_check_folders
import time
from pathlib import Path
from main import load_config,save_config
from platformdirs import user_log_dir, user_config_dir
from main import check_exiftool_installed
if not check_exiftool_installed():
    raise SystemExit(1)
config = load_config()
WATCH_DIRS = config["watch_folders"]
settings = config["settings"]
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
    config["settings"]["auto_start"] = True
    save_config(config)
    ## restart logic here
    print("Setting up automatic launch on system startup...")
if args.forget:
    config["watch_folders"] = []
    save_config(config)
    print("All saved folders have been forgotten.")
    raise SystemExit(0)
if args.folder:
    for folder in args.folder:
        folder = str(Path(folder).expanduser().resolve())

        if not Path(folder).is_dir():
            logger.warning(f"Skipping invalid folder: {folder}")
            continue

        if folder in WATCH_DIRS:
            logger.info(f"Folder already being watched: {folder}")
            continue
            
        WATCH_DIRS.append(folder)
    config["watch_folders"] = WATCH_DIRS
    save_config(config)
load_and_check_folders(WATCH_DIRS)
for d in WATCH_DIRS:
    full_path = os.path.expanduser(d)
    Precheck.check_folder(full_path)

if WATCH_DIRS is None or len(WATCH_DIRS) == 0:
    logger.error("No valid folders to watch. Exiting... use the -f option to specify folders to watch.")
    raise SystemExit(1)

main()




