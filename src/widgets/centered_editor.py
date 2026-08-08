"""A horizontal container that centers its content."""

from textual.containers import Horizontal


class CenteredEditor(Horizontal):
    """A horizontal container that centers its content."""

    DEFAULT_CSS = """
    CenteredEditor {
        align: center middle;
        height: 1fr;
        width: 100%;
        padding-bottom: 0;
    }

    CenteredEditor.distraction-free {
        padding-top: 2;
    }
    """
    pass
