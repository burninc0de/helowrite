# Command Palette Template

This document explains how to add new custom commands to HeloWrite's Command Palette.

## Principles

- **Run Command**: Commands should execute immediately when selected from the palette.
- **Feedback in Message Bar**: Always provide user feedback via the message bar (`self.show_message()`).
  - Show "Command started..." if it takes time.
  - Show success/failure messages when complete.
- **Async Handling**: For long-running operations, use sync callback that starts an async worker to keep the UI responsive.
- **Error Handling**: Catch exceptions, log to appropriate files, and show user-friendly messages.

## How to Add a Command

1. **Define the Callback Method**:
   - Add a method to the `HeloWrite` class in `src/app.py`.
   - For simple sync commands: `def my_command(self): ...`
   - For async commands: `def my_command(self): self.run_worker(self._async_my_command())` and `async def _async_my_command(self): ...`

2. **Yield SystemCommand in get_system_commands**:
   - In the `get_system_commands` method, yield `SystemCommand("Title", "Description", self.my_command)`

3. **Handle Imports and Logic**:
   - Import necessary modules inside the method to avoid top-level imports.
   - Use `self.show_message()` for feedback.

## Example: Simple Sync Command

```python
def insert_hello(self):
    """Insert 'Hello World' at cursor."""
    editor = self.query_one("#editor", HeloWriteTextArea)
    editor.insert("Hello World")
    self.show_message("Inserted 'Hello World'")

# In get_system_commands:
yield SystemCommand("Insert Hello", "Insert 'Hello World' at cursor", self.insert_hello)
```

## Example: Async Command (Git Sync)

```python
def git_sync(self):
    """Sync current file to git."""
    if not self.file_path:
        self.show_message("No file open")
        return
    self.show_message("Git sync started...")
    self.run_worker(self._async_git_sync())

async def _async_git_sync(self):
    """Async git operations."""
    # Imports and logic here
    # ...
    self.show_message("Git sync completed")

# In get_system_commands:
yield SystemCommand("Git Sync", "Add, commit, and push the current file", self.git_sync)
```

## Best Practices

- Keep command titles short and descriptive.
- Descriptions should explain what the command does.
- Test commands thoroughly, including edge cases.
- If a command modifies files, check permissions and handle errors.
- For commands that need user input, consider using Textual screens instead of palette.

## Adding to This Document

When you add a new command, document it here with a brief example.