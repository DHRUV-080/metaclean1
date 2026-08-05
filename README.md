# Meta-Cleaner

Meta-Cleaner is a Python command-line utility that automatically removes sensitive EXIF and metadata from images. It can be used interactively, on-demand, or as a background folder watcher to sanitize new images as they arrive.

## Features

- Remove EXIF metadata from supported images
- Watch one or more folders and clean images automatically
- Persistent watched-folder configuration
- Command-line interface with rich help output
- Logging for processed files and errors
- Cross-platform configuration and log directories via platformdirs

## Project Structure

```
cli.py     # CLI entry point, argument parsing, watcher lifecycle
main.py    # Metadata cleaning logic, folder management, event handlers
```

## Usage

Meta-Cleaner runs as a background folder watcher. Instead of cleaning files manually, it monitors one or more folders and automatically removes metadata from newly added images.

### Watch a Folder

```bash
cli -f ~/Pictures
```

The folder is saved to the configuration, so it will be monitored again the next time the application starts.

---

### Watch Multiple Folders

```bash
cli \
    -f ~/Pictures \
    -f ~/Downloads \
    -f ~/Desktop
```

Each folder is validated before monitoring begins.

---

### Forget Saved Folders

Remove every previously saved watch directory.

```bash
cli --forget
```

This clears the saved configuration.

---

### Enable Startup

```bash
cli --restart
```

Configures Meta-Cleaner to launch automatically when the system starts (implementation in progress).

---

### How It Works

1. Load saved watch folders.
2. Add any folders supplied via `-f`.
3. Save the updated configuration.
4. Validate each folder.
5. Start a filesystem observer.
6. Detect newly created images.
7. Remove sensitive metadata.
8. Continue monitoring until the application is stopped.

---

### Stopping the Service

Press:

```text
Ctrl+C
```

to stop the watcher safely.


## Future Improvements
- Parallel processing for large batches
- Hash-based duplicate detection
- Optional image optimization after cleaning
- File integrity verification
- System tray background service
- Localization
- Performance benchmarking
- Comprehensive API for library usage
