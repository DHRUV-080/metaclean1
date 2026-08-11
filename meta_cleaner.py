
import argparse
import os
import time
import threading
from pathlib import Path

from rich_argparse import RichHelpFormatter
from watchdog.observers import Observer

from main import Precheck
from main import NewImageHandler
from main import logger
from main import load_and_check_folders
from main import load_config
from main import save_config
from main import check_exiftool_installed


# 
# EXIFTOOL CHECK
# 

if not check_exiftool_installed():
    raise SystemExit(1)


# 
# CONFIG
# 

config = load_config()

WATCH_DIRS = config.get("watch_folders", [])

settings = config.get("settings", {})
version = config.get("version", "1.0")

logger.info(
    f"Meta-Cleaner version {version} starting..."
)


# 
# NORMALIZE FOLDER
# 

def normalize_folder(folder):
    return str(
        Path(folder)
        .expanduser()
        .resolve()
    )


# 
# SAVE WATCH FOLDERS
# 

def save_watch_dirs():
    config["watch_folders"] = WATCH_DIRS
    save_config(config)


# 
# ADD FOLDER
# 

def add_watch_folder(observer, handler, folder):
    folder = normalize_folder(folder)

    if not os.path.isdir(folder):
        logger.warning(
            f"Folder does not exist: {folder}"
        )
        return False

    if folder in WATCH_DIRS:
        logger.info(
            f"Folder is already being watched: {folder}"
        )
        return False

    try:
        observer.schedule(
            handler,
            folder,
            recursive=True,
        )
    except Exception as e:
        logger.error(
            f"Could not start watching {folder}: {e}"
        )
        return False

    WATCH_DIRS.append(folder)

    save_watch_dirs()

    logger.info(
        f"Now watching: {folder}"
    )

    return True


# 
# REMOVE FOLDER
# 

def remove_watch_folder(observer, folder):
    folder = normalize_folder(folder)

    if folder not in WATCH_DIRS:
        logger.warning(
            f"Folder is not currently being watched: {folder}"
        )
        return False

    try:
        # Find the Watch object belonging to this folder.
        for watch in list(observer.emitters):
            watched_path = normalize_folder(watch.watch.path)

            if watched_path == folder:
                observer.unschedule(watch.watch)
                break

        WATCH_DIRS.remove(folder)

        save_watch_dirs()

        logger.info(
            f"Stopped watching: {folder}"
        )

        return True

    except Exception as e:
        logger.error(
            f"Could not remove watcher for {folder}: {e}"
        )
        return False


# 
# LIST FOLDERS
# 

def list_watch_folders():
    if not WATCH_DIRS:
        print("No folders are currently being watched.")
        return

    print()
    print("Currently watched folders:")
    print()

    for index, folder in enumerate(WATCH_DIRS, start=1):
        print(f"  {index}. {folder}")

    print()


# 
# COMMAND LOOP
# 

def command_loop(observer, handler, stop_event):
    print()
    print("Meta-Cleaner command interface")
    print("-------")
    print("  add <folder>       Add a folder")
    print("  remove <folder>    Remove a folder")
    print("  list               List watched folders")
    print("  quit               Stop Meta-Cleaner")
    print("  exit               Stop Meta-Cleaner")
    print()

    while not stop_event.is_set():

        try:
            command = input("meta-cleaner> ").strip()

        except (EOFError, KeyboardInterrupt):
            print()
            stop_event.set()
            break

        if not command:
            continue

        parts = command.split(maxsplit=1)

        action = parts[0].lower()

        # --------------------
        # LIST
        # --------------------

        if action == "list":
            list_watch_folders()

        # --------------------
        # ADD
        # --------------------

        elif action == "add":

            if len(parts) != 2:
                print("Usage: add <folder>")
                continue

            folder = parts[1].strip()

            # Remove surrounding quotes if user typed:
            # add "/home/user/My Pictures"
            if (
                len(folder) >= 2
                and folder[0] == folder[-1]
                and folder[0] in ("'", '"')
            ):
                folder = folder[1:-1]

            add_watch_folder(
                observer,
                handler,
                folder,
            )

        # --------------------
        # REMOVE
        # --------------------

        elif action == "remove":

            if len(parts) != 2:
                print("Usage: remove <folder>")
                continue

            folder = parts[1].strip()

            # Allow:
            # remove 1
            #
            # This removes by list number.

            if folder.isdigit():
                index = int(folder)

                if index < 1 or index > len(WATCH_DIRS):
                    print("Invalid folder number.")
                    continue

                folder = WATCH_DIRS[index - 1]

            else:
                if (
                    len(folder) >= 2
                    and folder[0] == folder[-1]
                    and folder[0] in ("'", '"')
                ):
                    folder = folder[1:-1]

            remove_watch_folder(
                observer,
                folder,
            )

        # --------------------
        # QUIT
        # --------------------

        elif action in ("quit", "exit"):
            logger.info("Stopping Meta-Cleaner...")
            stop_event.set()

        # --------------------
        # HELP
        # --------------------

        elif action in ("help", "?"):
            print()
            print("Commands:")
            print("  add <folder>       Add a folder")
            print("  remove <folder>    Remove a folder")
            print("  list               List watched folders")
            print("  quit               Stop Meta-Cleaner")
            print()

        # --------------------
        # UNKNOWN
        # --------------------

        else:
            print(
                "Unknown command. "
                "Use: add, remove, list, quit"
            )


# 
# MAIN
# 

def main():
    observer = Observer()
    handler = NewImageHandler()

    watched_any = False

    # 
    # START EXISTING WATCHERS
    # 

    # Remove duplicates from saved configuration.
    unique_dirs = []

    for folder in WATCH_DIRS:
        folder = normalize_folder(folder)

        if folder not in unique_dirs:
            unique_dirs.append(folder)

    WATCH_DIRS.clear()
    WATCH_DIRS.extend(unique_dirs)

    save_watch_dirs()

    for folder in WATCH_DIRS:

        full_path = Path(folder)

        if full_path.is_dir():

            try:
                observer.schedule(
                    handler,
                    str(full_path),
                    recursive=True,
                )

                logger.info(
                    f"Watching: {full_path}"
                )

                watched_any = True

            except Exception as e:
                logger.error(
                    f"Could not watch {full_path}: {e}"
                )

        else:
            logger.warning(
                f"Skipping missing folder: {full_path}"
            )

    # 
    # NO FOLDERS
    # 

    if not watched_any:
        logger.error(
            "No valid folders to watch. "
            "Use -f to specify a folder."
        )
        return

    # 
    # START OBSERVER
    # 

    observer.start()

    stop_event = threading.Event()

    # 
    # COMMAND THREAD
    # 

    command_thread = threading.Thread(
        target=command_loop,
        args=(
            observer,
            handler,
            stop_event,
        ),
        daemon=True,
    )

    command_thread.start()

    logger.info(
        "Metadata wiper running."
    )

    logger.info(
        "Type 'help' to see available commands."
    )

    # 
    # MAIN WAIT LOOP
    # 

    try:
        while not stop_event.is_set():
            time.sleep(0.5)

    except KeyboardInterrupt:
        logger.info(
            "Ctrl+C received. Stopping..."
        )

        stop_event.set()

    finally:

        observer.stop()
        observer.join()

        logger.info(
            "Meta-Cleaner stopped."
        )


# 
# CLI
# 

parser = argparse.ArgumentParser(
    description="Privacy-focused image metadata cleaner and watcher.",
    formatter_class=RichHelpFormatter,
)

parser.add_argument(
    "-f",
    "--folder",
    type=str,
    help="Folder to watch for new images. Can be specified multiple times.",
    action="append",
    default=[],
)

parser.add_argument(
    "-r",
    "--restart",
    action="store_true",
    help=(
        "Automatically launch the script on system startup. "
        "Startup service setup is not implemented yet."
    ),
)

parser.add_argument(
    "--forget",
    action="store_true",
    help="Forget all previously saved folders to watch.",
)

args = parser.parse_args()


# 
# RESTART SETTING
# 

if args.restart:

    config["settings"]["auto_start"] = True

    save_config(config)

    print(
        "Automatic launch setting enabled."
    )

    print(
        "System startup integration is not implemented yet."
    )


# 
# FORGET
# 

if args.forget:

    config["watch_folders"] = []

    save_config(config)

    print(
        "All saved folders have been forgotten."
    )

    raise SystemExit(0)



# ADD FOLDERS FROM CLI


if args.folder:

    for folder in args.folder:

        folder = normalize_folder(folder)

        if not Path(folder).is_dir():

            logger.warning(
                f"Skipping invalid folder: {folder}"
            )

            continue

        if folder in WATCH_DIRS:

            logger.info(
                f"Folder already being watched: {folder}"
            )

            continue

        WATCH_DIRS.append(folder)


    config["watch_folders"] = WATCH_DIRS

    save_config(config)


# 
# CHECK FOLDERS
# 

load_and_check_folders(WATCH_DIRS)


# 
# NO FOLDERS
# 

if not WATCH_DIRS:

    logger.error(
        "No folders configured. "
        "Use the -f option to specify folders to watch."
    )

    raise SystemExit(1)


# 
# INITIAL PRECHECK
# 

for folder in WATCH_DIRS:

    full_path = Path(folder).expanduser()

    if full_path.is_dir():
        Precheck.check_folder(full_path)


# 
# START
# 

main()