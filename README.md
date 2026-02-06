# HeloWrite

```
    __  __     __    _       __     _ __     
   / / / /__  / /___| |     / /____(_) /____ 
  / /_/ / _ \/ / __ \ | /| / / ___/ / __/ _ \
 / __  /  __/ / /_/ / |/ |/ / /  / / /_/  __/
/_/ /_/\___/_/\____/|__/|__/_/  /_/\__/\___/ 
                                             
```

**The Tactical Blade for Prose**. HeloWrite is a distraction-free, terminal-based writing environment built for speed, paranoia, and deep focus. It’s not an "app"—it’s a void.

No bloat. No bullshit.

## Why HeloWrite?

Most modern writing tools are browser-based resource hogs that treat your words like secondary data. HeloWrite treats prose with the same rigor developers treat code.

- **0.5s Startup**: From Enter to blinking cursor in 500ms.
- **The Void**: High-contrast, minimalist UI designed to stop flashlighting your retinas.
- **Git-First Workflow**: Don't just "sync"—stage, commit, and push your notes only when they're worth keeping.
## Operational Essentials
- **Pure Focus**: F11 toggles distraction-free mode. No icons, no ribbons, just you and the syntactical turds you're polishing.
- **Adjustable Optics**: Alt+Left/Right to tune your horizontal padding. Spare your eyes the long trek across the screen.
- **Git Push** (The Staging Area): Use Alt+G (Option+G on macOS) or the Command Palette (Ctrl+P) to push your current file changes. It stashes local changes, adds/commits the current file, and pushes—all without leaving the editor.

## Quick Start

### Quick Test Drive (No Setup Required)

Want to try HeloWrite instantly without any installation?

```bash
uvx --from "git+https://github.com/burninc0de/helowrite.git" helowrite
```

This downloads and runs HeloWrite directly from the repository. Requires [UV](https://astral.sh/uv) (install with `curl -LsSf https://astral.sh/uv/install.sh | sh`).

### For Development/Full Installation

```
# Clone the void
git clone https://github.com/burninc0de/helowrite.git
cd helowrite

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: source venv/scripts/activate

# Fire the engines
pip install -e .
helowrite your_draft.txt
```

## Getting Started

### Prerequisites

- Python 3.8+ (run `python --version` to check)
- pip (Python package installer)

### Installation

1. **Clone or download** the repository
2. **Create virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

#### Alternative: Install as package (creates `helowrite` command)

For a more convenient installation that creates a `helowrite` command:

```bash
pip install -e .
```

This installs HeloWrite in editable mode and creates the `helowrite` command in your virtual environment.

### Running

```bash
python app.py [filename.txt]
```

Or if installed as package:

```bash
helowrite [filename.txt]
```

For example:
```bash
python app.py mydocument.txt
```

Or:
```bash
helowrite mydocument.txt
```

### Testing

After activating your virtual environment:

```bash
python -m pytest
```

## Keyboard Shortcuts (The Muscle Memory)

- `Ctrl+S` - Save file
- `Ctrl+Q` - Quit application
- `Ctrl+O` - Open file panel (toggle)
- `Ctrl+N` - Create new file
- `Ctrl+F` - Find/Replace (toggle)
- `Ctrl+P` - Command palette
- `Alt+Left/Right` - Decrease/Increase editor width (Option+Left/Right on macOS)
- `Alt+A` - Select all text (Option+A on macOS)
- `Alt+D` - Create daily note (Option+D on macOS)
- `Alt+G` - Git push current file (Option+G on macOS)
- `Alt+H` - Git pull current file (Option+H on macOS)
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
├── app.py                 # Main application entry point
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
│   ├── test_*.py          # Individual test files
├── venv/                  # Virtual environment (created by user)
├── helowrite_env/         # Alternative virtual environment
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Project configuration
├── pytest.ini             # Pytest configuration
├── run.sh                 # Wrapper script for venv activation
├── git_sync_errors.log    # Git operation error log (created as needed)
├── AGENTS.md              # Agent instructions (internal)
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
