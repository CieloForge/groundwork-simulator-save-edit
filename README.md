# Groundwork Simulator Save Editor

A community save file editor for **Groundwork Simulator**.

## Overview

Groundwork Simulator persists its world state to `.groundwork-simulator` save files. This repository provides a lightweight, dependency-free editor for locating, inspecting, and modifying campaign and economy data within those saves.

## Features

- Automatically detects the default save directory for the current platform
- Accepts a direct save file or folder path via command-line argument
- Displays the loaded save's opening balance, live cash, gold held, and active loans
- Allows editing of cash / opening balance, gold weight, and loan state
- Creates a `.bak` backup before writing any changes

## Requirements

- Python 3.12+

> Note: The current interactive editor runs using only the Python standard library.

## Usage

```bash
python3 gw_save_editor.py
```

Or pass a direct file or folder path:

```bash
python3 gw_save_editor.py /path/to/slot-02.groundwork-simulator
```

The editor presents an interactive menu:

1. Set Cash / Opening Balance (EUR)
2. Set Gold Weight (grams)
3. Clear All Loans

## Save Locations

The editor automatically detects the default save directory:

- **macOS:** `~/Library/Application Support/com.groundwork-simulator.groundwork-simulator/saves/slots/`
- **Windows:** `%APPDATA%\com.groundwork-simulator.groundwork-simulator\saves\slots\`
- **Linux / Steam Deck:** `~/.local/share/com.groundwork-simulator.groundwork-simulator/saves/slots/`

> **Note:** The default save directory paths above may need to be adjusted depending on the platform or system configuration. If you are running on a platform not covered here, or if the path does not resolve correctly on your system, please [open an issue](https://github.com/CieloForge/groundwork-simulator-save-edit/issues) and include the directory in which your saves are located so it can be reflected here.

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE).
