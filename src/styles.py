"""Shared application-level Textual CSS."""

APP_DEFAULT_CSS = """Screen {
    background: $surface;
}

    CenteredEditor {
        align: center middle;
        height: 1fr;
        width: 100%;
        padding-bottom: 0;
    }

    CenteredEditor.distraction-free {
        padding-top: 2;
    }

    TextArea {
        border: none;
        background: transparent;
        width: 70%;
        height: 100%;
        padding: 2 4;
        scrollbar-size: 1 1;
        scrollbar-color: $surface-lighten-2;
        scrollbar-color-hover: $surface-lighten-1;
        scrollbar-background: $surface;
    }

    #editor {
        border: none;
    }

    TextArea.distraction-free {
        padding: 1 2;
    }

    /* Scrollbar styling for distraction-free (fullscreen) mode */
    TextArea.distraction-free {
        scrollbar-background: $surface;
        scrollbar-background-hover: $surface;
        scrollbar-background-active: $surface;
        scrollbar-color: #d0d0d0;
        scrollbar-color-hover: #cfcfcf;
        scrollbar-color-active: #bfbfbf;
        scrollbar-size: 1 1;
    }

    /* TextArea internal content background - force match screen */
    TextArea > .text-area--content {
        background: $surface !important;
    }

    /* Also try targeting the text area lines directly */
    .text-area--lines {
        background: $surface;
    }

    /* Cursor styling - uses theme color by default */
    .text-area--cursor {
        background: $primary;
        color: #ffffff;
        text-style: bold;
    }

    .text-area--cursor-line {
        background: $primary-lighten-1;
    }

    StatusBar {
        background: $primary-darken-2;
        color: $text;
        padding: 0 1;
        height: 1;
        margin: 0;
    }

    #message-bar {
        background: $success;
        color: $text;
        padding: 0 1;
        height: 1;
        margin: 0;
    }

    Footer {
        padding: 0;
        margin: 0;
        dock: bottom;
    }

    #distraction-word-count {
        height: 1;
        text-align: right;
        padding: 0 2;
        margin: 1 0;
        color: $text;
        background: transparent;
        opacity: 0;
        display: none;
    }

    #distraction-word-count.visible {
        display: block;
        opacity: 0.3;
    }

    /* Command Palette - make it narrower and centered */
    CommandPalette {
        align: center middle;
    }

    CommandPalette > Vertical {
        width: 60%;
        max-width: 80;
    }

    /* Command Palette thin scrollbar */
    CommandPalette CommandList {
        scrollbar-size: 1 1;
        scrollbar-color: $surface-lighten-2;
        scrollbar-color-hover: $surface-lighten-1;
        scrollbar-background: $surface;
    }

    CommandPalette ScrollableContainer {
        scrollbar-size: 1 1;
    }

    /* KeyPanel (Keys help) thin scrollbar */
    KeyPanel {
        scrollbar-size: 1 1;
        scrollbar-color: $surface-lighten-2;
        scrollbar-color-hover: $surface-lighten-1;
        scrollbar-background: $surface;
    }
    """
