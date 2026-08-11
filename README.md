## CLI Options

Meta-Cleaner provides several command-line options for configuring the watcher when starting the program.

### `-f`, `--folder`

Adds a folder to the list of folders that Meta-Cleaner should watch.

```bash
python meta_cleaner.py -f ~/Pictures
```

You can specify `-f` multiple times to watch multiple folders:

```bash
python meta_cleaner.py \
    -f ~/Pictures \
    -f ~/Downloads \
    -f ~/Desktop
```

The folders are saved to the configuration automatically, so they will be loaded the next time Meta-Cleaner starts.

**Use this when:** you want to configure your watched folders when launching Meta-Cleaner.

---

### `--forget`

Removes **all saved watched folders** from the configuration.

```bash
python meta_cleaner.py --forget
```

This does not delete the actual folders or any files inside them. It only removes them from Meta-Cleaner's saved watch list.

**Use this when:** you want to start with a completely empty watch list.

---

### `-r`, `--restart`

Enables the `auto_start` setting in the configuration.

```bash
python meta_cleaner.py --restart
```

⚠️ **Currently, this does not actually configure Meta-Cleaner to start automatically with the operating system.** The startup/service implementation is still unfinished.

**Use this when:** preparing to enable automatic startup once the startup feature is implemented.

---

## Runtime Commands

After Meta-Cleaner has started, folders can also be managed without restarting the program.

```text
add <folder>
```

Immediately starts watching a new folder:

```text
meta-cleaner> add ~/Pictures/New
```

---

```text
remove <folder>
```

Stops watching a specific folder:

```text
meta-cleaner> remove ~/Pictures/New
```

You can also remove a folder by its number:

```text
meta-cleaner> remove 2
```

---

```text
list
```

Displays all currently watched folders:

```text
meta-cleaner> list

1. /home/user/Pictures
2. /home/user/Downloads
3. /home/user/Desktop
```

---

```text
help
```

Displays the available runtime commands.

---

```text
quit
```

or:

```text
exit
```

Stops Meta-Cleaner safely.

### CLI vs Runtime Commands

| Feature            | CLI           | Runtime           |
| ------------------ | ------------- | ----------------- |
| Add folder         | `-f <folder>` | `add <folder>`    |
| Remove folder      | —             | `remove <folder>` |
| List folders       | —             | `list`            |
| Forget all folders | `--forget`    | —                 |
| Auto-start setting | `--restart`   | —                 |
| Stop program       | —             | `quit` / `exit`   |

**In short:** use the CLI options when **starting** Meta-Cleaner, and use the runtime commands when you want to manage the watcher **without restarting it**.
