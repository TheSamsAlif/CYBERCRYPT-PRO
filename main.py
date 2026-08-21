"""
main.py
=======

Entry point of CyberCrypt Pro.

Run it with:
    python main.py
"""

from __future__ import annotations

import customtkinter as ctk

from cybercrypt.app import CyberCryptApp


def main():
    """Configure the theme and launch the application window."""
    # Disable CustomTkinter's automatic DPI scaling so that our
    # hardcoded pixel layout values (SPACING, _TITLE_LINE_PX, card
    # gaps, etc.) map 1:1 to real pixels on Windows at 125%/150%.
    try:
        ctk.deactivate_automatic_dpi_awareness()
    except AttributeError:
        pass  # older CustomTkinter builds may not have this
    ctk.set_widget_scaling(1.0)
    ctk.set_window_scaling(1.0)

    # Force the dark "glass" appearance.
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = CyberCryptApp()
    app.mainloop()


if __name__ == "__main__":
    main()
