# Meta-Cleaner

**Meta-Cleaner** is a privacy-focused image metadata cleaner and filesystem watcher written in Python.

It uses **ExifTool** to remove image metadata and **Watchdog** to automatically clean supported images when they are created or moved into watched folders.

## Features

* 🧹 Remove image metadata
* 🔍 Scan existing folders
* 👀 Real-time image monitoring
* 📁 Multiple watched folders
* ➕ Add folders while running
* ➖ Remove folders while running
* 📋 List watched folders
* 💾 Persistent configuration
* 🚫 Duplicate-folder protection
* ⏳ Wait for files to finish writing
* 📝 Logging and error handling

## Supported Formats

```text
.jpg  .jpeg  .png  .webp
.heic .heif  .bmp  .tiff  .gif
```

## Requirements

Python 3, ExifTool, and the required Python packages.

### Install ExifTool

Ubuntu/Debian:

```bash
sudo apt install libimage-exiftool-perl
```

### Install Python dependencies

```bash
pip install watchdog platformdirs rich-argparse
```

## Usage

### Start with a folder

```bash
python meta_cleaner.py -f ~/Pictures
```

### Start with multiple folders

```bash
python meta_cleaner.py -f ~/Pictures -f ~/Downloads
```

Folders are saved automatically.

## CLI Options

### `-f`, `--folder`

Adds a folder to the watch list when starting Meta-Cleaner.

```bash
python meta_cleaner.py -f ~/Pictures
```

You can use `-f` multiple times:

```bash
python meta_cleaner.py -f ~/Pictures -f ~/Downloads -f ~/Desktop
```

The folders are saved automatically and loaded the next time Meta-Cleaner starts.

**Use this when:** configuring watched folders at startup.

---

### `--forget`

Removes **all saved watched folders** from the configuration.

```bash
python meta_cleaner.py --forget
```

This does **not** delete the folders or their files. It only clears them from Meta-Cleaner's saved watch list.

**Use this when:** you want to completely reset the saved watch list.

---

### `-r`, `--restart`

Enables the `auto_start` setting.

```bash
python meta_cleaner.py --restart
```

> **Note:** System startup integration is not implemented yet. Currently this only saves the auto-start setting.

## Runtime Commands

While Meta-Cleaner is running:

```text
add <folder>       Add and immediately watch a folder
remove <folder>    Stop watching a folder
remove <number>    Remove a folder by its list number
list               List watched folders
help               Show available commands
quit / exit        Stop Meta-Cleaner
```

### Example

```text
meta-cleaner> list

1. /home/user/Pictures
2. /home/user/Downloads

meta-cleaner> add ~/Desktop
Now watching: /home/user/Desktop

meta-cleaner> remove 2
Stopped watching: /home/user/Downloads
```

Runtime changes are immediately applied to the Watchdog observer and saved to the configuration.

## CLI vs Runtime Commands

| Action             | At Startup    | While Running     |
| ------------------ | ------------- | ----------------- |
| Add folder         | `-f <folder>` | `add <folder>`    |
| Remove folder      | —             | `remove <folder>` |
| List folders       | —             | `list`            |
| Forget all folders | `--forget`    | —                 |
| Auto-start setting | `--restart`   | —                 |
| Stop program       | —             | `quit` / `exit`   |

## Configuration

Watched folders and settings are stored automatically in the user's configuration directory.

To forget all saved folders:

```bash
python meta_cleaner.py --forget
```

## Metadata Cleaning

Meta-Cleaner looks for potentially sensitive metadata such as:

* GPS/location
* Camera and lens information
* Serial numbers
* Owner/creator information
* Dates and times
* Software/editing history
* IPTC/XMP data
* Embedded previews and thumbnails

When cleaning, ExifTool is used to remove metadata from the image.

> **Warning:** Metadata removal can be destructive. Keep backups of important files.

## Logging

Application activity and errors are written to the user's platform log directory.

## Current Limitations

* `--restart` currently only saves the auto-start setting; system startup integration is not implemented yet.
* Metadata verification after cleaning is not currently performed.
* Advanced event debouncing is still a future improvement.

## Project Structure

```text
Meta-Cleaner/
├── main.py
├── meta_cleaner.py
├── requirements.txt
└── README.md
```

### `main.py`

Core metadata cleaning, configuration, logging, and Watchdog handling.

### `meta_cleaner.py`

CLI, folder management, runtime commands, and watcher startup.

## Roadmap

* [ ] Linux systemd auto-start
* [ ] Windows/macOS startup support
* [ ] Metadata verification
* [ ] Dry-run mode
* [ ] Better event debouncing
* [ ] More tests
* [ ] Installable CLI package

## Disclaimer

Meta-Cleaner modifies image files and removes metadata. Test it on copies of important files first.
