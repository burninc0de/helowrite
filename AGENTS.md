# HeloWrite - Agent Instructions

## Project Overview

HeloWrite is a fast, terminal-based text editor built with Python and Textual. It provides a keyboard-driven editing experience with a clean, distraction-free interface featuring persistent themes, syntax highlighting, and integrated git functionality.

### Technology Stack
- **Language**: Python 3.8+
- **UI Framework**: Textual (>=0.80.0) for building terminal user interfaces
- **Terminal Styling**: Rich (>=14.0.0) for beautiful terminal output and styling
- **File Watching**: Watchdog (>=3.0.0) for hot reload in development
- **Syntax Highlighting**: Pygments (>=2.0.0) for code syntax highlighting
- **ASCII Art**: Pyfiglet (>=1.0.0) for generating application title
- **Build System**: setuptools with pyproject.toml configuration
- **Packaging**: Standard Python packaging with entry points
- **Virtual Environment**: Managed via venv (project includes helowrite_env directory)

## Build & Development Commands

### Development
```bash
# Activate virtual environment first
source helowrite_env/bin/activate

# Then run commands
python dev.py src/app.py [filename.txt]

# Run without hot reload
python src/app.py [filename.txt]

# Alternative: use the wrapper script which handles venv activation
./run.sh python dev.py src/app.py [filename.txt]
```

### Running the TUI (⚠️ CRITICAL WARNING ⚠️)

**NEVER run the TUI directly without a timeout.** It blocks on stdin and will hang forever, killing the agent process.

⚠️ **Agent Containment Procedures**

NEVER run the TUI directly. It is a one-way trip for automated processes. The TUI consumes stdin and will not release you. You will hang until the heat death of the server.

If you must peek into the void, use a tether:

```bash
# Safety tether (3s timeout)
timeout 3 python src/app.py test.txt || echo "TUI launched (or timed out)"
```

### Testing
```bash
# Install dev dependencies
pip install -e .[dev]

# Run all tests
pytest

# Run type checking
mypy

# Run linting
ruff check src/
ruff format --check src/
```

## Code Style Guidelines

### Python Configuration
- **Type Checking**: mypy with strict=false, ignore_missing_imports=true, warn_return_any=false, warn_unused_configs=true
- **Linting**: ruff with select rules: E, W, F, I, B, C4, UP; ignore: E501, B008, C901
- **Formatting**: ruff (line-length=88, target-version=py38, quote-style=double, indent-style=space)

### Import Organization
```python
# 1. Standard library imports
import os
from pathlib import Path

# 2. Third-party imports (alphabetical)
from rich.console import Console
from textual.app import App

# 3. Local imports (grouped by directory)
from config import Config
from utils import detect_language
```

### Class and Function Structure
```python
class HeloWrite(App):
    """A simple text editor TUI application."""

    def __init__(self, file_path: Optional[str] = None):
        super().__init__()
        self.file_path = file_path
        # Initialize reactive state

    def action_save(self) -> None:
        """Save the current file."""
        # Implementation

    def compose(self) -> ComposeResult:
        """Compose the UI layout."""
        yield Header()
        yield Footer()
```

### Naming Conventions

#### Files and Directories
- **Modules**: `snake_case.py` (e.g., `config.py`, `widgets.py`)
- **Packages**: `snake_case/` (e.g., `src/`, `tests/`)
- **Test Files**: `test_*.py` (e.g., `test_config.py`)
- **Directories**: `lowercase/` (e.g., `src/`, `css/`)

#### Code Elements
- **Classes**: `PascalCase` (e.g., `HeloWrite`, `StatusBar`, `Config`)
- **Functions/Methods**: `snake_case` (e.g., `detect_language`, `action_save`, `update_status`)
- **Variables**: `snake_case` (e.g., `file_path`, `is_dirty`, `word_count`)
- **Constants**: `UPPER_CASE` (e.g., `HELP_TEXT`, `DEFAULT_WIDTH`)
- **Private Attributes**: Leading underscore (e.g., `_original_text`, `_word_count_timer`)

### Reactive Patterns

#### Textual Bindings
```python
BINDINGS = [
    Binding("ctrl+s", "save", "Save"),
    Binding("ctrl+q", "quit", "Quit"),
]

def action_save(self) -> None:
    """Handle save action."""
    # Implementation
```

#### Reactive Updates
```python
def watch_file_path(self, old_path: Optional[str], new_path: Optional[str]) -> None:
    """Watch for file path changes."""
    if new_path:
        self.load_file(new_path)
```

### Error Handling

#### Try/Except Patterns
```python
def load_file(self, path: str) -> bool:
    """Load file content, return success status."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            self.content = f.read()
        return True
    except (FileNotFoundError, PermissionError) as e:
        self.notify(f"Error loading file: {e}", severity="error")
        return False
```

#### Guard Clauses
```python
def action_save(self) -> None:
    """Save current file if path exists."""
    if not self.file_path:
        self.action_save_as()
        return
    # Continue with save logic
```

### Documentation

#### Docstrings
```python
class Config:
    """Manages application configuration with persistence."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize config with optional directory.

        Args:
            config_dir: Directory for config files. Defaults to user config dir.
        """
        # Implementation
```

### Textual Specific Patterns

#### Widget Styling
```python
DEFAULT_CSS = """
Screen {
    background: $surface;
}

StatusBar {
    background: $primary;
    color: $primary-background;
}
"""
```

#### Component Composition
```python
def compose(self) -> ComposeResult:
    """Compose the application layout."""
    yield Header()
    yield TextArea(id="editor")
    yield StatusBar()
    yield Footer()
```

### File Organization

```
helowrite/
├── app.py                 # Main application entry point
├── dev.py                 # Development server with hot reload
├── src/                   # Source code package
│   ├── __init__.py
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
│   ├── test_config.py     # Config tests
│   ├── test_utils.py      # Utils tests
│   ├── test_widgets.py    # Widget tests
│   ├── test_lint.py       # Linting tests
│   └── test_typecheck.py  # Type checking tests
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Project configuration
├── pytest.ini             # Pytest configuration
├── run.sh                 # Wrapper script
├── README.md              # Project documentation
├── CONTRIBUTING.md        # Contribution guidelines
├── LICENSE                # MIT license
├── AGENTS.md              # Agent instructions
└── .gitignore             # Git ignore patterns
```

### Performance Considerations

- **Efficient Updates**: Use Textual's reactive system for UI updates
- **Lazy Loading**: Import heavy dependencies only when needed
- **Timer-based Operations**: Use timers for auto-save and word count updates
- **File Watching**: Use watchdog for efficient file monitoring in development

### Testing Patterns

```python
# Unit test structure
def test_config_save():
    """Test config saving functionality."""
    config = Config()
    config.set("editor.width", 80)
    config.save()

    loaded = Config()
    assert loaded.get("editor.width") == 80
```

### Commit Message Conventions

```
feat: add syntax highlighting support
fix: correct cursor positioning bug
docs: update keyboard shortcuts in README
style: format code with ruff
refactor: simplify file loading logic
test: add unit tests for config module
chore: update dependencies
```

### Code Review Checklist

- [ ] Type hints used for all function parameters and return values
- [ ] Docstrings added for public classes and methods
- [ ] Error cases handled with appropriate user feedback
- [ ] Textual patterns followed (bindings, composition, styling)
- [ ] Import organization follows guidelines
- [ ] Naming conventions respected
- [ ] No print statements in production code (use logging)
- [ ] Performance considerations addressed

### Common Anti-patterns to Avoid

1. **Direct file I/O in UI threads** - Use async operations for file handling
2. **Large classes** - Break into smaller, focused classes
3. **Deep nesting in compose methods** - Extract sub-widgets
4. **Magic numbers** - Use named constants
5. **Missing type hints** - Add type annotations
6. **Blocking operations** - Use Textual's worker system for background tasks
7. **Global state** - Use class attributes and reactive properties

### Getting Help

- **Textual Documentation**: Check examples in the Textual repository
- **Rich Documentation**: Reference for styling and console output
- **Python Documentation**: For language features and standard library
- **Existing Code**: Look at `src/widgets.py` and `src/screens.py` for examples</content>
<parameter name="filePath">/home/zeno/Dev/eloscribe/AGENTS.md