# HeloWrite

```
    __  __     __    _       __     _ __     
   / / / /__  / /___| |     / /____(_) /____ 
  / /_/ / _ \/ / __ \ | /| / / ___/ / __/ _ \
 / __  /  __/ / /_/ / |/ |/ / /  / / /_/  __/
/_/ /_/\___/_/\____/|__/|__/_/  /_/\__/\___/ 
                                             
```
![GitHub Release](https://img.shields.io/github/v/release/burninc0de/helowrite?color=orange)
![Test](https://github.com/burninc0de/helowrite/actions/workflows/python-app.yml/badge.svg)


**The Tactical Blade for Prose**. HeloWrite is a distraction-free, terminal-based writing environment built for speed, paranoia, and deep focus. It's not an "app"—it's a void.

One word at a time. No distractions, no detours.

![](https://andreklein.net/wp-content/uploads/2026/07/focus.png)

## Why HeloWrite?

HeloWrite is a digital typewriter with an infinite roll of paper and no "Format" menu to hide behind.

It has one job: help you scrape words out of your skull.

HeloWrite treats prose with the same rigor developers treat code, minus the steep learning curve. Terminal-native, standard keybinds, clean aesthetics.

Writing is hard. Focus is paramount. Everything else is secondary.

- **0.5s Startup**: From Enter to blinking cursor in 500ms.
- **The Void**: High-contrast, minimalist UI designed to stop flashlighting your retinas.
- **Git-First Workflow**: Don't just "sync"—stage, commit, and push your work only when it is worth keeping.

## Operational Essentials
- **Pure Focus**: F11 toggles distraction-free mode. No icons, no ribbons, just you and the text.
- **Adjustable Optics**: Alt+Left/Right to tune your horizontal padding. Spare your eyes the long trek across the screen.
- **Directory Navigation**: Alt+Up/Down to navigate directory hierarchy with undo-like history. Move up to parent directories and back down through your navigation path.
- **Git Push** (The Staging Area): Use Alt+G (Option+G on macOS) or the Command Palette (Ctrl+P) to push your current file changes. It stashes local changes, adds/commits the current file, and pushes—all without leaving the editor. Git operations are based on the opened file's directory, not the vault path in settings.
- **Pomodoro Timer**: Use Ctrl+T to launch a timer modal. Enter minutes, press Enter to start. When complete, a modal appears with success message. Sound credit: [nahmandub on freesound.org](https://freesound.org/people/nahmandub/sounds/131348/)
- **Typewriter Mode**: Toggle with `Ctrl+Shift+T`. When enabled, the cursor stays centered like an old-school typewriter. This was inspired by [a fork](https://github.com/gabinetenoturno/helowrite) by gabinetenoturno. Optional sounds for new line and backspace by [Gate13](https://freesound.org/people/Gate13/sounds/697389/).

![screenshot](https://andreklein.net/wp-content/uploads/2026/06/helowrite_grid3.png)
Extensive themes, distraction-free mode, Git Sync, Pomodoro Timer and more

## Quick Start

### One-Liner (No Setup Required)

```bash
uvx --from "git+https://github.com/burninc0de/helowrite.git" helowrite
```

Requires [UV](https://astral.sh/uv) (install with `curl -LsSf https://astral.sh/uv/install.sh | sh`).

### Persistent CLI Install (Recommended)

If you want `helowrite` to work in every new terminal without activating a virtual environment, install with `pipx`:

Install `pipx` first (if you do not already have it):

<details>
<summary>Arch Linux</summary><br/>

```bash
sudo pacman -S python-pipx
```
</details>

<details>
<summary>macOS (Homebrew)</summary><br/>

```bash
brew install pipx
```
</details>

<details>
<summary>Debian/Ubuntu</summary><br/>

```bash
sudo apt install pipx
```
</details>

<details>
<summary>Fedora</summary><br/>

```bash
sudo dnf install pipx
```
</details>

<details>
<summary>Generic Fallback</summary><br/>


```bash
python -m pip install --user pipx
python -m pipx ensurepath
```
</details>

Then install HeloWrite:

```bash
pipx install "git+https://github.com/burninc0de/helowrite.git"
```

This creates an isolated environment and exposes the `helowrite` command globally in your user PATH.

To upgrade to the latest version:

```bash
pipx upgrade helowrite
```

To uninstall:

```bash
pipx uninstall helowrite
```

### Development Install (Editable Source Checkout)

Use this if you want to hack on HeloWrite itself. We use a virtual environment so your system python stays untouched.

```bash
# Clone the void
git clone https://github.com/burninc0de/helowrite.git
cd helowrite

# Set up environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install & run
pip install -e .
helowrite 
```

Important: because this is a venv-local editable install, `helowrite` is available only while that venv is active.

**Requirements**: Python 3.8+

### Troubleshooting: 

> [!IMPORTANT]
> HeloWrite is built for high-performance terminal environments that support modern input protocols.

- Verified: Ghostty, Kitty, Alacritty.
- Unsupported: macOS Terminal.app, Windows Console, and other legacy emulators.

Depending on your terminal or environment, some key combinations may get eaten by your terminal and/or OS. Make sure to customize your keybinds in `keybindings.conf` if something isn't working as expected.

#### `helowrite: command not found`

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

## Environment Variables

<details>
    <summary>HELOWWRITE_CONFIG_DIR — Custom Config Path</summary><br/>

Override the config directory (defaults to `~/.config/helowrite`):

```bash
HELOWWRITE_CONFIG_DIR=/path/to/config python src/app.py
```

</details>

<details>
    <summary>HELOWRITE_TYPEWRITER_DEBUG — Typewriter Debug Logs</summary><br/>

For debugging cursor positioning and centering logic in typewriter mode:

```bash
HELOWRITE_TYPEWRITER_DEBUG=1 python src/app.py
HELOWRITE_TYPEWRITER_DEBUG=1 python dev.py src/app.py  # hot reload
```

Logs go to `~/.config/helowrite/typewriter_debug.log`.

</details>

<details>
    <summary>HELOWWRITE_SYSTEM_THEME_FILE — System Theme Colors</summary><br/>

Point to a custom colors file in TOML format (e.g. `background`, `foreground`, `accent` keys). Overrides the built-in search paths.

```bash
HELOWWRITE_SYSTEM_THEME_FILE=/path/to/colors.toml python src/app.py
```

</details>

<details>
    <summary>HELOWWRITE_SYSTEM_THEME_NAME_FILE — Theme Display Name</summary><br/>

Path to a file whose contents are used as the theme display name. Falls back to `theme.name` beside the colors file.

```bash
HELOWWRITE_SYSTEM_THEME_NAME_FILE=/path/to/theme.name python src/app.py
```

</details>

<details>
    <summary>HELOWRITE_RUN_PERF — Latency Profiling Tests</summary><br/>

Run performance/latency profiling tests that are skipped by default:

```bash
HELOWRITE_RUN_PERF=1 pytest tests/test_typewriter_scroll_perf.py
```

</details>

## Keyboard Shortcuts (The Muscle Memory)

- `Ctrl+S` - Save file
- `Ctrl+Q` - Quit application
- `Ctrl+O` - Open file panel (toggle, auto-focuses for keyboard navigation)
- `Ctrl+N` - Create new file
- `Ctrl+F` - Find/Replace (toggle)
- `Ctrl+P` - Command palette
- `Ctrl+T` - Pomodoro timer
- `Ctrl+Shift+T` - Toggle typewriter mode
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

## Customizing Hotkeys

HeloWrite writes a user-editable keybindings file the first time it runs:

```bash
~/.config/helowrite/keybindings.conf
```

Each line uses the format `action=key`. Only one binding is supported per action.
You can customize any action by editing that file and restarting HeloWrite.

Example:

```ini
save=ctrl+s
quit=ctrl+q
toggle_distraction_free=f11
toggle_typewriter_mode=ctrl+shift+t
```

Use Textual-style key names, e.g. `ctrl+s`, `ctrl+shift+t`, `alt+enter`, `f1`, `alt+left`.
If a line is malformed or a key is invalid, HeloWrite will ignore that binding and keep the default for the action.

## Snippets

HeloWrite supports a simple snippet engine via `~/.config/helowrite/snippets.conf`.

Each snippet uses the format `trigger=replacement`:

```ini
# trigger=replacement
ddd=Archduke Maximilian of Habsburg-Lorraine
```

Snippets are expanded when the trigger is typed and followed by whitespace or punctuation. Trailing punctuation is preserved, so typing `ddd.` becomes:

```text
Archduke Maximilian of Habsburg-Lorraine.
```

Supported placeholders:
- `%CURRENTTIME` → current time in `HH:MM`
- `%%` → literal `%`

After editing `snippets.conf`, restart HeloWrite to load your changes.

## Markdown Scope

HeloWrite is for prose. Journaling, drafts, essays, braindumps — the stuff you're scraping out of your skull, not typesetting. Syntax highlighting exists so raw markdown stays readable while you write, not so you can format as you go.

It is not a technical or academic writing tool. There's no support for math notation, chemistry formulas, citations, footnotes, tables, sub/superscript, or Pandoc-style rendering — and there won't be. That's a different job, for different software.

What we highlight, and why: enough to keep structure legible at a glance, nothing more.

| Element | Example |
|---|---|
| Headings | `# H1` `## H2` `### H3` |
| Bold | `**text**` |
| Italic | `*text*` |
| Strikethrough | `~~text~~` |
| Inline code | `` `code` `` |
| Fenced code blocks | ` ``` ... ``` ` |
| Links | `[title](url)` |
| Images | `![alt](src)` |
| Blockquotes | `> text` |
| Unordered lists | `- item` `* item` `+ item` |
| Ordered lists | `1. item` `1) item` |
| Task lists | `- [ ] todo` `- [x] done` |

If you need real typesetting — LaTeX-style math, citations, footnotes, Pandoc's extended syntax — that tooling already exists and does it properly. Write your prose here, then hand it off.

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
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Project configuration
├── pytest.ini             # Pytest configuration
├── git_sync_errors.log    # Git operation error log (created as needed)
├── AGENTS.md              # Agent instructions (internal)
├── CONTRIBUTING.md        # Contribution guidelines
├── LICENSE                # MIT license
├── README.md              # This file
└── .gitignore             # Git ignore patterns
```

## Contributing

PRs welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT

---

> I fell in love with a machine. That's stupid. So just call me an idiot, and let's be done with it. - **Karl "Helo" Agathon**
