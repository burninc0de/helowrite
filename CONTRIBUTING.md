# Contributing to HeloWrite

Thank you for your interest in contributing to HeloWrite! This document provides guidelines for contributing to the project.

## Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/helowrite.git
   cd helowrite
   ```

2. **Create and activate virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python app.py [filename]
   ```

5. **Run tests**:
   ```bash
   pytest
   ```

## Development Guidelines

### Code Style
- Use `ruff` for code formatting and linting
- Follow PEP 8 conventions
- Use type hints where appropriate
- Keep functions and methods focused on single responsibilities

### Commit Conventions
- Use conventional commit format: `type: description`
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
- Example: `feat: add dark mode toggle`

### Testing
- Write tests for new features
- Ensure all tests pass before submitting PRs
- Test both functionality and edge cases

### Pull Request Process
1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes
4. Run tests and ensure they pass
5. Format code with `ruff`
6. Submit a pull request with a clear description

## Architecture Overview

HeloWrite is built with:
- **Textual**: TUI framework for Python
- **Rich**: Terminal styling and formatting
- **Python 3.8+**: Core language

Key components:
- `app.py`: Main application class
- `src/config.py`: Configuration management
- `src/widgets.py`: Custom UI widgets
- `src/screens.py`: Dialog screens
- `src/utils.py`: Utility functions

## Reporting Issues

When reporting bugs or requesting features:
- Use the GitHub issue tracker
- Provide clear reproduction steps
- Include your Python version and OS
- For bugs, include error messages and stack traces

## License

By contributing to HeloWrite, you agree that your contributions will be licensed under the MIT License.