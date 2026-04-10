# HeloWrite

```
    __  __     __    _       __     _ __     
   / / / /__  / /___| |     / /____(_) /____ 
  / /_/ / _ \/ / __ \ | /| / / ___/ / __/ _ \
 / __  /  __/ / /_/ / |/ |/ / /  / / /_/  __/
/_/ /_/\___/_/\____/|__/|__/_/  /_/\__/\___/ 
                                             
```

**The Tactical Blade for Prose**. HeloWrite is a distraction-free, terminal-based writing environment built for speed, paranoia, and deep focus. It's not an "app"—it's a void.

No bloat. No bullshit.

https://user-images.githubusercontent.com/44199273/624cdd83-cbda-4c8e-978c-2464e43bb497.mp4

## Why HeloWrite?

HeloWrite is a digital typewriter with an infinite roll of paper and no "Format" menu to hide behind.

It has one job: help you scrape words out of your skull.

HeloWrite treats prose with the same rigor developers treat code, but without the steep learning curve. Terminal-native, standard keybinds, clean aesthetics.

Writing is hard. Everything else is secondary.

- **0.5s Startup**: From Enter to blinking cursor in 500ms.
- **The Void**: High-contrast, minimalist UI designed to stop flashlighting your retinas.
- **Git-First Workflow**: Don't just "sync"—stage, commit, and push your work only when it is worth keeping.

## Operational Essentials
- **Pure Focus**: F11 toggles distraction-free mode. No icons, no ribbons, just you and the syntactical turds you're polishing.
- **Adjustable Optics**: Alt+Left/Right to tune your horizontal padding. Spare your eyes the long trek across the screen.
- **Directory Navigation**: Alt+Up/Down to navigate directory hierarchy with undo-like history. Move up to parent directories and back down through your navigation path.
- **Git Push** (The Staging Area): Use Alt+G (Option+G on macOS) or the Command Palette (Ctrl+P) to push your current file changes. It stashes local changes, adds/commits the current file, and pushes—all without leaving the editor. Git operations are based on the opened file's directory, not the vault path in settings.

## Quick Start

### One-Liner (No Setup Required)

```bash
uvx --from "git+https://github.com/burninc0de/helowrite.git" helowrite
```

Requires [UV](https://astral.sh/uv) (install with `curl -LsSf https://astral.sh/uv/install.sh | sh`).

### Persistent CLI Install (Recommended)

If you want `helowrite` to work in every new terminal without activating a virtual environment, install with `pipx`:

Install `pipx` first (if you do not already have it):

```bash
# Arch Linux
sudo pacman -S python-pipx

# macOS (Homebrew)
brew install pipx

# Debian/Ubuntu
sudo apt install pipx

# Fedora
sudo dnf install pipx

# Generic fallback
python -m pip install --user pipx
python -m pipx ensurepath
```

Then install HeloWrite:

```bash
pipx install "git+https://github.com/burninc0de/helowrite.git"
helowrite your_draft.txt
```

This creates an isolated environment and exposes the `helowrite` command globally in your user PATH.

### Development Install (Editable Source Checkout)

Use this if you want to hack on HeloWrite itself. This install is intentionally tied to your virtual environment.

```bash
# Clone the void
git clone https://github.com/burninc0de/helowrite.git
cd helowrite

# Set up environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install & run
pip install -e .
helowrite your_draft.txt
```

Important: because this is a venv-local editable install, `helowrite` is available only while that venv is active.
When you open a new terminal, run:

```bash
cd helowrite
source venv/bin/activate
helowrite your_draft.txt
```

If you'd rather avoid re-activating a venv in each shell, use the recommended `pipx` install above.

**Requirements**: Python 3.8+

### Troubleshooting: `helowrite: command not found`

- If you installed with `pip install -e .` inside a venv, reactivate that venv in each new terminal.
- If you installed with `pipx` but the command is still missing, ensure `~/.local/bin` is on your PATH.
- You can run `pipx ensurepath`, then restart your shell.

### Development

Run with hot reload during development:

```bash
python dev.py src/app.py [filename.txt]
```

Or run without hot reload:

```bash
python src/app.py [filename.txt]
```

### Testing

1. Install development dependencies (includes `pytest-asyncio`):
   ```bash
   pip install -e .[dev]
   ```

2. Run the full test suite:
   ```bash
   pytest
   ```

3. Run specific interaction tests:
   ```bash
   pytest tests/test_settings_interaction.py
   ```

## Keyboard Shortcuts (The Muscle Memory)

- `Ctrl+S` - Save file
- `Ctrl+Q` - Quit application
- `Ctrl+O` - Open file panel (toggle, auto-focuses for keyboard navigation)
- `Ctrl+N` - Create new file
- `Ctrl+F` - Find/Replace (toggle)
- `Ctrl+P` - Command palette
- `Alt+Left/Right` - Decrease/Increase editor width (Option+Left/Right on macOS)
- `Alt+Up/Down` - Navigate directory up/down with history (Option+Up/Down on macOS)
- `Alt+A` - Select all text (Option+A on macOS)
- `Alt+D` - Create daily note (Option+D on macOS)
- `Alt+I` - Toggle insert newline on Enter (Option+I on macOS)
- `Alt+G` - Git push current file (Option+G on macOS, based on opened file's directory)
- `Alt+H` - Git pull current file (Option+H on macOS, based on opened file's directory)
- `Alt+J` - Git pull vault repository (Option+J on macOS, based on vault path in settings)
- `F1` - Show help
- `F3` - Open settings
- `F5` - Open recent files
- `F11` - Toggle distraction-free mode
- `F12` - About dialog
- `Arrow keys` - Navigate cursor
- `Home/End` - Jump to start/end of line
- `Page Up/Down` - Scroll by page

## Architecture

HeloWrite is built using:

- **Textual** - Modern TUI framework for Python
- **Rich** - Beautiful terminal output and styling
- **Python** - Clean, readable, and maintainable code

## Project Structure

```
helowrite/
├── dev.py                 # Development server with hot reload
├── src/                   # Source code package
│   ├── __init__.py
│   ├── app.py             # Main application module
│   ├── config.py          # Configuration management
│   ├── constants.py       # Constants and help text
│   ├── screens.py         # UI screens and dialogs
│   ├── utils.py           # Utility functions
│   ├── widgets.py         # Custom widgets
│   └── css/               # Stylesheets
│       ├── __init__.py
│       ├── app.tcss       # Main app styles
│       ├── screens.tcss   # Screen styles
│       └── widgets.tcss   # Widget styles
├── tests/                 # Test suite
│   ├── __init__.py
│   ├── conftest.py        # Pytest configuration
│   ├── test_app.py        # Integration tests
│   ├── test_settings_interaction.py # UI interaction tests
│   └── test_*.py          # Unit tests
├── venv/                  # Virtual environment (created by user)
├── helowrite_env/         # Alternative virtual environment
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Project configuration
├── pytest.ini             # Pytest configuration
├── run.sh                 # Wrapper script for venv activation
├── git_sync_errors.log    # Git operation error log (created as needed)
├── AGENTS.md              # Agent instructions (internal)
├── CONTRIBUTING.md        # Contribution guidelines
├── LICENSE                # MIT license
├── README.md              # This file
└── .gitignore             # Git ignore patterns
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT

---

> I fell in love with a machine. That's stupid. So just call me an idiot, and let's be done with it. - **Karl "Helo" Agathon**
