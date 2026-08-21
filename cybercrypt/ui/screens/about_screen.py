"""
about_screen.py
===============

Project information screen: logo, description, developer section,
technology stack, architecture overview, the educational
disclaimer and version information.

NOTE: edit DEVELOPER_NAME and GUIDE_NAME below before presenting.
"""

from __future__ import annotations

import customtkinter as ctk

from cybercrypt import __subtitle__, __title__, __version__
from cybercrypt.ui.screens.base_screen import BaseScreen
from cybercrypt.ui.theme import COLORS, FONTS, ICONS, RADIUS
from cybercrypt.ui.widgets import badge, glass_panel

# ------------------------- EDIT THESE BEFORE PRESENTING ------------------ #
DEVELOPER_NAME = "Your Name"
GUIDE_NAME = "Guide / Faculty Name"
# ------------------------------------------------------------------------- #

# The three algorithm cards shown on the about screen.
_ALGORITHMS = [
    {
        "name": "1 · Caesar Cipher",
        "formula": "E(x) = (x + shift) mod 128",
        "note": "The simplest substitution cipher: one fixed shift for "
                "every character. Brute force is trivial - only 128 "
                "possible shifts. This is why we never rely on it alone.",
        "advantages": "Very easy to understand - the perfect first "
                      "cipher to learn.",
        "limitations": "Only 128 possible keys: brute force breaks it "
                       "in seconds.",
    },
    {
        "name": "2 · Vigenere Cipher",
        "formula": "E(x) = (x + key[i]) mod 128",
        "note": "Each character is shifted by a different amount, driven "
                "by a repeating keyword. It defeats simple frequency "
                "analysis, but a long enough key phrase is needed.",
        "advantages": "A keyword-driven shift defeats frequency analysis "
                      "of single letters.",
        "limitations": "If the keyword repeats, patterns leak - and a "
                       "wrong keyword gives garbage output.",
    },
    {
        "name": "3 · Random XOR Layer",
        "formula": "E(x) = x XOR stream(i)",
        "note": "A Linear Congruential Generator, seeded with a number, "
                "produces a pseudo-random keystream. XOR is its own "
                "inverse, so the same step decrypts.",
        "advantages": "XOR is its own inverse, so decryption is "
                      "identical - very beginner friendly.",
        "limitations": "Pseudo-random, not true randomness: the same "
                       "seed always produces the same keystream.",
    },
]

_TECH_STACK = ["Python 3.13", "CustomTkinter", "Tkinter / ttk", "Pillow"]

# Architecture overview (shown in monospace).
_ARCHITECTURE = (
    "cybercrypt/\n"
    "│\n"
    "├─ core/     the 3 ciphers + multi-layer engine (no UI logic)\n"
    "├─ ui/       theme, animations, widgets, screens, dialogs\n"
    "├─ utils/    colour + time helpers\n"
    "└─ tests/    unit tests for the whole engine"
)


class AboutScreen(BaseScreen):
    """Project information screen (scrollable)."""

    # ------------------------------------------------------------------ #
    # Construction                                                        #
    # ------------------------------------------------------------------ #

    def _build_widgets(self):
        """Create a scrollable page with all the information cards.
        The hero card is the page header, so the scroll starts at the
        shared header position (hero fills the title zone)."""
        self.scroll = self._page_scroll(top=self.header_top())

        self._build_hero_card()
        self._build_description_card()
        self._build_disclaimer_card()
        self._build_algorithm_cards()
        self._build_architecture_card()
        self._build_developer_card()
        self._build_tech_card()
        self._build_version_footer()

    # ------------------------------------------------------------------ #
    # Cards                                                               #
    # ------------------------------------------------------------------ #

    def _build_hero_card(self):
        """Logo medallion, project name and badges."""
        card = glass_panel(self.scroll)
        card.pack(fill="x", padx=2, pady=(2, 8))

        # Large logo medallion.
        medallion = ctk.CTkFrame(card, corner_radius=44, width=88, height=88,
                                 fg_color=COLORS["PRIMARY_DEEP"],
                                 border_width=2,
                                 border_color=COLORS["ACCENT"])
        medallion.pack(pady=(28, 10))
        logo = ctk.CTkLabel(medallion, text=ICONS["LOGO"],
                            font=("Segoe UI", 38, "bold"),
                            text_color=COLORS["ACCENT"])
        logo.place(relx=0.5, rely=0.5, anchor="center")

        title = ctk.CTkLabel(card, text=__title__,
                             font=FONTS["TITLE"],
                             text_color=COLORS["TEXT"])
        title.pack(pady=(0, 2))

        subtitle = ctk.CTkLabel(card, text=__subtitle__,
                                font=FONTS["BODY"],
                                text_color=COLORS["TEXT_MUTED"])
        subtitle.pack(pady=(0, 6))

        badges = ctk.CTkFrame(card, fg_color="transparent")
        badges.pack(pady=(0, 24))
        badge(badges, f"Version {__version__}",
              color=COLORS["ACCENT"]).pack(side="left", padx=(0, 8))
        badge(badges, "University Cyber Security Mini Project",
              color=COLORS["SUCCESS"]).pack(side="left", padx=(8, 0))

    def _build_description_card(self):
        """What the project does."""
        card = glass_panel(self.scroll)
        card.pack(fill="x", padx=2, pady=(0, 10))

        heading = ctk.CTkLabel(card, text="About the Project",
                               font=FONTS["SUBHEADING"],
                               text_color=COLORS["TEXT"])
        heading.pack(padx=22, pady=(16, 4), anchor="w")

        text = ("CyberCrypt Pro is a desktop application that demonstrates "
                "multi-layer encryption. It combines three classical "
                "ciphers - Caesar, Vigenere and a random XOR layer - into "
                "a single engine that encrypts and decrypts any text "
                "offline, with no data ever leaving the device.")
        body = ctk.CTkLabel(card, text=text, font=FONTS["SMALL"],
                            text_color=COLORS["TEXT_MUTED"],
                            justify="left", wraplength=840)
        body.pack(padx=22, pady=(0, 16), anchor="w")

    def _build_disclaimer_card(self):
        """The educational disclaimer - clearly visible."""
        card = ctk.CTkFrame(
            self.scroll,
            corner_radius=RADIUS["CARD"],
            fg_color="#291D0B",  # warm dark amber tint
            border_width=1,
            border_color=COLORS["WARNING"],
        )
        card.pack(fill="x", padx=2, pady=(0, 12))

        text = ("This software demonstrates classical cryptography concepts "
                "for educational purposes. It is NOT designed for "
                "real-world secure communication.")
        label = ctk.CTkLabel(
            card, text=f"!  {text}",
            font=FONTS["BODY"],
            text_color=COLORS["WARNING"],
            wraplength=820, justify="left",
        )
        label.pack(padx=24, pady=16, anchor="w")

    def _build_algorithm_cards(self):
        """One card per layer, with formula and explanation."""
        heading = ctk.CTkLabel(self.scroll, text="The Three Layers",
                               font=FONTS["HEADING"],
                               text_color=COLORS["TEXT"])
        heading.pack(pady=(6, 10), anchor="w")

        for algorithm in _ALGORITHMS:
            card = glass_panel(self.scroll)
            card.pack(fill="x", padx=2, pady=(0, 8))

            name = ctk.CTkLabel(card, text=algorithm["name"],
                                font=FONTS["SUBHEADING"],
                                text_color=COLORS["TEXT"])
            name.pack(padx=22, pady=(14, 2), anchor="w")

            formula = ctk.CTkLabel(card, text=algorithm["formula"],
                                   font=FONTS["MONO"],
                                   text_color=COLORS["ACCENT"])
            formula.pack(padx=22, pady=(2, 4), anchor="w")

            note = ctk.CTkLabel(card, text=algorithm["note"],
                                font=FONTS["SMALL"],
                                text_color=COLORS["TEXT_MUTED"],
                                justify="left", wraplength=840)
            note.pack(padx=22, pady=(0, 8), anchor="w")

            pros = ctk.CTkLabel(
                card,
                text=f"+  {algorithm['advantages']}",
                font=FONTS["MICRO"],
                text_color=COLORS["SUCCESS"],
                justify="left", wraplength=840,
            )
            pros.pack(padx=22, pady=(0, 3), anchor="w")

            cons = ctk.CTkLabel(
                card,
                text=f"—  {algorithm['limitations']}",
                font=FONTS["MICRO"],
                text_color=COLORS["WARNING"],
                justify="left", wraplength=840,
            )
            cons.pack(padx=22, pady=(0, 16), anchor="w")

    def _build_architecture_card(self):
        """How the code is organised."""
        card = glass_panel(self.scroll)
        card.pack(fill="x", padx=2, pady=(0, 10))

        heading = ctk.CTkLabel(card, text="Architecture Overview",
                               font=FONTS["SUBHEADING"],
                               text_color=COLORS["TEXT"])
        heading.pack(padx=22, pady=(14, 4), anchor="w")

        tree = ctk.CTkLabel(card, text=_ARCHITECTURE,
                            font=FONTS["MONO_SMALL"],
                            text_color=COLORS["TEXT_MUTED"],
                            justify="left")
        tree.pack(padx=22, pady=(0, 16), anchor="w")

    def _build_developer_card(self):
        """Who built it."""
        card = glass_panel(self.scroll)
        card.pack(fill="x", padx=2, pady=(0, 10))

        heading = ctk.CTkLabel(card, text="Developer",
                               font=FONTS["SUBHEADING"],
                               text_color=COLORS["TEXT"])
        heading.pack(padx=22, pady=(14, 4), anchor="w")

        developer = ctk.CTkLabel(
            card,
            text=f"Developed by:  {DEVELOPER_NAME}",
            font=FONTS["BODY"],
            text_color=COLORS["TEXT_MUTED"],
        )
        developer.pack(padx=22, pady=(0, 2), anchor="w")

        guide = ctk.CTkLabel(
            card,
            text=f"Guided by:  {GUIDE_NAME}",
            font=FONTS["SMALL"],
            text_color=COLORS["TEXT_FAINT"],
        )
        guide.pack(padx=22, pady=(0, 16), anchor="w")

    def _build_tech_card(self):
        """Technology stack as chips."""
        card = glass_panel(self.scroll)
        card.pack(fill="x", padx=2, pady=(0, 10))

        heading = ctk.CTkLabel(card, text="Technology Stack",
                               font=FONTS["SUBHEADING"],
                               text_color=COLORS["TEXT"])
        heading.pack(padx=22, pady=(12, 8), anchor="w")

        chips = ctk.CTkFrame(card, fg_color="transparent")
        chips.pack(padx=22, pady=(0, 16), anchor="w")
        for stack in _TECH_STACK:
            badge(chips, stack, color=COLORS["ACCENT"]).pack(
                side="left", padx=(0, 8))

    def _build_version_footer(self):
        """Version and phase information."""
        footer = ctk.CTkLabel(
            self.scroll,
            text=f"CyberCrypt Pro v{__version__}  ·  Final Release  ·  "
                 "Fully offline  ·  No data leaves this device",
            font=FONTS["SMALL"],
            text_color=COLORS["TEXT_FAINT"],
        )
        footer.pack(pady=(8, 24))

    def on_show(self):
        """Force layout recalculation when the page becomes visible."""
        self.update_idletasks()
