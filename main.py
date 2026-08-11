
import shutil
import os
import subprocess
import time
import logging
from pathlib import Path
import json
import copy

from watchdog.events import FileSystemEventHandler
from platformdirs import user_log_dir, user_config_dir


# 
# PATHS / LOGGING
# 

LOG_DIR = Path(user_log_dir("meta-cleaner", "MrIncognito7"))
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "meta-cleaner.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)

logger = logging.getLogger("meta-cleaner")

console = logging.StreamHandler()
console.setFormatter(logging.Formatter("%(message)s"))

if not logger.handlers:
    logger.addHandler(console)
else:
    # Make sure console output exists even if logging configured elsewhere.
    if console not in logger.handlers:
        logger.addHandler(console)


# 
# CONFIG
# 

CONFIG_DIR = Path(user_config_dir("meta-cleaner", "MrIncognito7"))
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "version": "1.0",
    "watch_folders": [],
    "settings": {
        "auto_start": False,
        "log_level": "INFO",
    },
}


def check_exiftool_installed() -> bool:
    if shutil.which("exiftool") is None:
        logger.error(
            "exiftool not found. Meta-Cleaner cannot clean metadata without it.\n"
            "Install it with: sudo apt install libimage-exiftool-perl"
        )
        return False

    return True


def load_config():
    if not CONFIG_FILE.exists():
        save_config(copy.deepcopy(DEFAULT_CONFIG))
        return copy.deepcopy(DEFAULT_CONFIG)

    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Could not read config file: {e}")
        logger.warning("Using default configuration.")

        config = copy.deepcopy(DEFAULT_CONFIG)
        save_config(config)
        return config

    # Make sure required keys exist.
    if not isinstance(config, dict):
        logger.warning("Invalid config format. Using default configuration.")
        config = copy.deepcopy(DEFAULT_CONFIG)

    if not isinstance(config.get("watch_folders"), list):
        config["watch_folders"] = []

    if not isinstance(config.get("settings"), dict):
        config["settings"] = copy.deepcopy(DEFAULT_CONFIG["settings"])

    for key, value in DEFAULT_CONFIG["settings"].items():
        config["settings"].setdefault(key, value)

    config.setdefault("version", DEFAULT_CONFIG["version"])

    return config


def save_config(config):
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        temp_file = CONFIG_FILE.with_suffix(".tmp")

        with open(temp_file, "w") as f:
            json.dump(config, f, indent=4)

        temp_file.replace(CONFIG_FILE)

    except OSError as e:
        logger.error(f"Could not save configuration: {e}")


# 
# SENSITIVE METADATA
# 

SENSITIVE_TAGS = {
    # GPS / Location
    "GPS": "reveals exact physical location",

    # Device / Camera identification
    "SerialNumber": "uniquely ties this photo to your specific device",
    "LensID": "reveals your exact camera/lens, ties photos together",
    "LensModel": "reveals your exact camera/lens, ties photos together",
    "LensSerialNumber": "uniquely ties this photo to your specific lens",
    "LensInfo": "reveals lens details, ties photos together",
    "BodySerialNumber": "uniquely ties this photo to your specific device",
    "InternalSerialNumber": "uniquely ties this photo to your specific device",
    "CameraID": "uniquely ties this photo to your specific device",
    "DeviceManufacturer": "reveals your device manufacturer",
    "DeviceModel": "reveals your exact device model",
    "DeviceSettingDescription": "reveals device-specific settings, fingerprinting risk",
    "Make": "reveals your device brand",
    "Model": "reveals your exact device model",

    # Ownership / Identity
    "OwnerName": "directly identifies you by name",
    "Artist": "directly identifies you by name",
    "Copyright": "may contain your name or identifying info",
    "By-line": "directly identifies the creator by name",
    "By-lineTitle": "may reveal your job title/role",
    "CopyrightNotice": "may contain your name or identifying info",
    "Credit": "may identify you or your organization",
    "Contact": "may contain direct contact information",
    "CreatorContactInfo": "may contain direct contact information",

    # Date / Time
    "DateTimeOriginal": "reveals exactly when this was taken",
    "CreateDate": "reveals exactly when this was taken",
    "ModifyDate": "reveals when this was last edited",
    "DateTimeDigitized": "reveals exactly when this was digitized",
    "SubSecTimeOriginal": "reveals precise sub-second capture time",
    "SubSecTimeDigitized": "reveals precise sub-second capture time",
    "Creation Time": "reveals exactly when this was created (PNG)",

    # Software / Processing history
    "Software": "reveals what app/OS you used",
    "ProcessingSoftware": "reveals what software processed this file",
    "HistorySoftwareAgent": "reveals full edit history software chain",
    "DocumentID": "unique identifier, can correlate files back to you",
    "InstanceID": "unique identifier, can correlate files back to you",
    "OriginalDocumentID": "unique identifier, can correlate files back to you",
    "DerivedFrom": "reveals this file's edit lineage/source file",

    # Color profile (ICC)
    "ProfileCMMType": "reveals device/software manufacturer",
    "ProfileCreator": "reveals device/software manufacturer",
    "ProfileDescription": "may reveal device/software info",
    "ProfileDateTime": "reveals when the color profile was created",

    # Unique identifiers
    "ImageUniqueID": "unique per-photo ID, potentially traceable",
    "OriginalRawFileName": "may reveal original filename/naming pattern",

    # Thumbnails / embedded previews
    "ThumbnailImage": "may leak original uncropped/unedited image content",
    "PreviewImage": "may leak original uncropped/unedited image content",
    "JpgFromRaw": "may leak original uncropped/unedited image content",
    "OtherImage": "may leak hidden embedded image content",

    # IPTC descriptive fields
    "Keywords": "may contain descriptive/identifying tags added by software",
    "Caption-Abstract": "may contain a written description revealing context",
    "Headline": "may contain a written description revealing context",
    "City": "reveals location at a city level",
    "Sub-location": "reveals specific location details",
    "Province-State": "reveals location at a regional level",
    "Country-PrimaryLocationName": "reveals location at a country level",

    # General XMP catch-all
    "XMP": "may contain edit history, keywords, or embedded location data",
}


IMAGE_EXTS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".heic",
    ".heif",
    ".bmp",
    ".tiff",
    ".gif",
}


# 
# USER CONFIRMATION
# 

def confirm(question: str) -> bool:
    while True:
        try:
            answer = input(f"{question} [y/n]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return False

        if answer in ("y", "yes"):
            return True

        if answer in ("n", "no"):
            return False

        print("Please answer 'y' or 'n'.")


# 
# PRECHECK
# 

class Precheck:

    @staticmethod
    def find_sensitive_tags(file_data):
        """Flatten grouped ExifTool JSON and return sensitive tags."""
        flat = {}

        for group, value in file_data.items():
            if group == "System":
                continue

            if isinstance(value, dict):
                flat.update(value)
            else:
                flat[group] = value

        found = []

        for tag_name, tag_value in flat.items():
            for keyword, reason in SENSITIVE_TAGS.items():
                if keyword.lower() in tag_name.lower():
                    found.append((tag_name, tag_value, reason))
                    break

        return found

    @staticmethod
    def check_folder(folder: Path):
        sensit = 0
        clean = 0

        try:
            result = subprocess.run(
                [
                    "exiftool",
                    "-j",
                    "-a",
                    "-u",
                    "-g1",
                    "-r",
                    str(folder),
                ],
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            logger.error(
                "exiftool not installed. "
                "Run: sudo apt install libimage-exiftool-perl"
            )
            return

        if result.returncode != 0:
            logger.error(
                f"ExifTool failed while checking {folder}: "
                f"{result.stderr.strip()}"
            )
            return

        try:
            all_files_data = json.loads(result.stdout)
        except json.JSONDecodeError:
            logger.error(f"No readable files in: {folder}")
            return

        for file_data in all_files_data:
            sensitive = Precheck.find_sensitive_tags(file_data)

            if sensitive:
                sensit += 1
            else:
                clean += 1

        if sensit > 0:
            logger.info(
                f"Checked {len(all_files_data)} files in {folder}: "
                f"{clean} clean, {sensit} with sensitive metadata."
            )

            confirmation = confirm(
                "Do you want to wipe sensitive metadata from these files?"
            )

            if confirmation:
                wiped = 0

                for file_data in all_files_data:
                    name = file_data["SourceFile"]
                    sensitive = Precheck.find_sensitive_tags(file_data)

                    if sensitive:
                        if wipe_image(Path(name)):
                            wiped += 1

                logger.info(
                    f"Wiped metadata from {wiped} files in {folder}."
                )

            else:
                logger.info(
                    "Wipe operation cancelled by user. "
                    "Sensitive files were not modified."
                )

        else:
            logger.info(f"All files in {folder} were clean.")


# 
# FOLDER CHECK
# 

def load_and_check_folders(watch_dirs):
    for d in watch_dirs:
        full_path = Path(d).expanduser()

        if not full_path.is_dir():
            logger.warning(f"Skipping missing folder: {full_path}")
        else:
            try:
                count = sum(
                    1
                    for f in full_path.iterdir()
                    if f.is_file()
                )

                logger.info(
                    f"Found {count} files in {full_path}."
                )

            except OSError as e:
                logger.warning(
                    f"Could not inspect {full_path}: {e}"
                )


# 
# FILE STABILITY
# 

def wait_until_stable(
    path: Path,
    timeout: float = 10.0,
    interval: float = 0.3,
) -> bool:

    end_time = time.time() + timeout
    last_size = -1

    while time.time() < end_time:
        try:
            size = path.stat().st_size
        except FileNotFoundError:
            return False

        if size == last_size and size > 0:
            return True

        last_size = size
        time.sleep(interval)

    return False


# 
# METADATA WIPE
# 

def wipe_image(path: Path):
    try:
        result = subprocess.run(
            [
                "exiftool",
                "-all=",
                "-icc_profile:all=",
                "-overwrite_original",
                str(path),
            ],
            check=True,
            capture_output=True,
        )

        logger.info(f"Metadata cleaned: {path}")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(
            f"exiftool failed on {path}: "
            f"{e.stderr.decode(errors='ignore')}"
        )
        return False

    except FileNotFoundError:
        logger.error(
            "exiftool not installed. "
            "Run: sudo apt install libimage-exiftool-perl"
        )
        return False


# 
# WATCHDOG HANDLER
# 

class NewImageHandler(FileSystemEventHandler):

    def on_created(self, event):
        if event.is_directory:
            return

        path = Path(event.src_path)

        if path.suffix.lower() not in IMAGE_EXTS:
            return

        if not wait_until_stable(path):
            logger.warning(
                f"File never stabilized, skipping: {path}"
            )
            return

        wipe_image(path)

    def on_moved(self, event):
        if event.is_directory:
            return

        path = Path(event.dest_path)

        if path.suffix.lower() not in IMAGE_EXTS:
            return

        if not wait_until_stable(path):
            logger.warning(
                f"File never stabilized, skipping: {path}"
            )
            return

        success = wipe_image(path)

        if not success:
            logger.error(
            f"Failed to clean metadata from moved image: {path}"
            )