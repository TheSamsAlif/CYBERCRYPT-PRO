"""
dashboard_screen.py
===================

The home screen. Premium hero area, four animated statistic cards,
the encryption pipeline and the three layer cards.

The whole page lives inside a scrollable frame and every card uses
a natural (pack) layout, so nothing is ever clipped, no text
overlaps and the page can always reach the bottom.
"""

from __future__ import annotations

import customtkinter as ctk

from cybercrypt.ui.animation import bind_smart_hover, fade_sequence
from cybercrypt.ui.screens.base_screen import BaseScreen
from cybercrypt.ui.theme import COLORS, FONTS, ICONS
from cybercrypt.ui.widgets import glass_panel, primary_button, secondary_button

# The three layers shown as cards on the dashboard.
_LAYERS = [
    {
        "number": "01",
        "name": "Caesar Cipher",
        "formula": "E(x) = (x + shift) mod 128",
        "description": "Shifts every character by a fixed number of "
                       "positions. The classic cipher of ancient Rome.",
    },
    {
        "number": "02",
        "name": "Vigenere Cipher",
        "formula": "E(x) = (x + key[i]) mod 128",
        "description": "Uses a repeating keyword, so every character "
                       "is shifted by a different amount.",
    },
    {
        "number": "03",
        "name": "Random XOR Layer",
        "formula": "E(x) = x XOR stream(i)",
        "description": "A seeded pseudo-random keystream is XOR-ed with "
                       "the text. XOR is its own inverse.",
    },
]

# Pipeline chips: the encryption order shown on the dashboard.
_PIPELINE = ["Plain Text", "Caesar", "Vigenere", "Random XOR", "Cipher Text"]

# Stat cards: (icon, caption, colour, style hint).
_STAT_CARDS = [
    {"icon": ICONS["SESSIONS"], "caption": "Encrypted Sessions",
     "color": COLORS["ACCENT"], "value_key": "encrypt"},
    {"icon": ICONS["ALGO"], "caption": "Current Algorithm",
     "color": COLORS["ACCENT"], "value_key": "algorithm"},
    {"icon": ICONS["LAYERS"], "caption": "Encryption Layers",
     "color": COLORS["PRIMARY"], "value_key": "layers"},
    {"icon": ICONS["STATUS"], "caption": "Application Status",
     "color": COLORS["SUCCESS"], "value_key": "status"},
]


class DashboardScreen(BaseScreen):
    """The home / overview screen."""

    # ------------------------------------------------------------------ #
    # Construction                                                        #
    # ------------------------------------------------------------------ #

    def _build_widgets(self):
        self._stat_values = {}
        self._loading_cards = []

        self._page_header(
            "Dashboard",
            "Your encryption workspace, at a glance.")

        # Scrollable content: the page can grow and scroll naturally.
        self.scroll = self._page_scroll()

        self._build_hero()
        self._build_stat_cards()
        self._build_pipeline_card()
        self._build_layer_cards()
        self._build_footer()
        self._animate_loading()

    # ------------------------------------------------------------------ #
    # Card helpers (natural flow, no fixed heights)                       #
    # ------------------------------------------------------------------ #

    def _panel(self, hover: bool = True) -> ctk.CTkFrame:
        """A full-width glass panel packed into the scroll."""
        panel = glass_panel(self.scroll)
        panel.pack(fill="x", padx=2, pady=(0, 8))
        self._loading_cards.append(panel)
        if hover:
            bind_smart_hover(
                panel,
                lambda: COLORS["GLASS"], lambda: COLORS["GLASS_HOVER"],
                lambda: COLORS["BORDER"], lambda: COLORS["ACCENT"],
            )
        return panel

    def _cell(self, parent) -> ctk.CTkFrame:
        """A hoverable glass cell for side-by-side cards."""
        cell = glass_panel(parent)
        bind_smart_hover(
            cell,
            lambda: COLORS["GLASS"], lambda: COLORS["GLASS_HOVER"],
            lambda: COLORS["BORDER"], lambda: COLORS["ACCENT"],
        )
        self._loading_cards.append(cell)
        return cell

    # ------------------------------------------------------------------ #
    # Sections                                                            #
    # ------------------------------------------------------------------ #

    def _build_hero(self):
        """Title, subtitle and quick actions (stacked, spaced)."""
        card = self._panel()

        title = ctk.CTkLabel(card, text="Secure Text Encryption, Reinvented",
                             font=FONTS["DISPLAY"],
                             text_color=COLORS["TEXT"], anchor="w")
        title.pack(anchor="w", padx=24, pady=(14, 2))

        subtitle = ctk.CTkLabel(
            card,
            text="Three classical ciphers, layered into one engine - "
                 "wrapped in a premium glass experience.",
            font=FONTS["BODY"], text_color=COLORS["TEXT_MUTED"],
            anchor="w", justify="left",
        )
        subtitle.pack(anchor="w", padx=24, pady=(0, 12))

        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(anchor="w", padx=24, pady=(0, 16))
        primary_button(
            actions, f"Start Encrypting  {ICONS['ARROW']}",
            lambda: self.app.switch_screen("encrypt"), height=40,
        ).pack(side="left", padx=(0, 10))
        secondary_button(
            actions, "How it Works",
            lambda: self.app.switch_screen("about"), height=40,
        ).pack(side="left")

    def _build_stat_cards(self):
        """Four statistic cards in a row (equal, consistent height)."""
        row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        row.pack(fill="x", padx=2, pady=(0, 8))

        for index, spec in enumerate(_STAT_CARDS):
            card = self._cell(row)
            card.pack(side="left", fill="both", expand=True,
                      padx=(0 if index == 0 else 4,
                            4 if index == len(_STAT_CARDS) - 1 else 0))

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=16, pady=16)

            head = ctk.CTkFrame(inner, fg_color="transparent")
            head.pack(fill="x")

            medallion = ctk.CTkFrame(
                head, corner_radius=12, width=36, height=36,
                fg_color=COLORS["TINT_BLUE"],
                border_width=1, border_color=spec["color"])
            medallion.pack(side="left")
            medallion.pack_propagate(False)
            icon = ctk.CTkLabel(medallion, text=spec["icon"],
                                font=("Segoe UI", 15),
                                text_color=spec["color"])
            icon.place(relx=0.5, rely=0.5, anchor="center")

            caption = ctk.CTkLabel(head, text=spec["caption"],
                                   font=FONTS["MICRO"],
                                   text_color=COLORS["TEXT_MUTED"])
            caption.pack(side="left", padx=(10, 4))

            value = ctk.CTkLabel(inner, text="",
                                 font=FONTS["STAT_NUMBER"],
                                 text_color=spec["color"], anchor="w")
            value.pack(anchor="w", pady=(8, 0))
            self._stat_values[spec["value_key"]] = value

    def _card(self, parent) -> ctk.CTkFrame:
        """A glass card that grows with its content."""
        cell = glass_panel(parent)
        bind_smart_hover(
            cell,
            lambda: COLORS["GLASS"], lambda: COLORS["GLASS_HOVER"],
            lambda: COLORS["BORDER"], lambda: COLORS["ACCENT"],
        )
        self._loading_cards.append(cell)
        return cell

    def _build_pipeline_card(self):
        """The visual encryption-order strip."""
        card = self._panel(hover=False)

        label = ctk.CTkLabel(card, text="ENCRYPTION PIPELINE",
                             font=FONTS["MICRO"],
                             text_color=COLORS["TEXT_FAINT"], anchor="w")
        label.pack(anchor="w", padx=18, pady=(14, 8))

        strip = ctk.CTkFrame(card, fg_color="transparent")
        strip.pack(fill="x", padx=18, pady=(0, 16))

        for index, step in enumerate(_PIPELINE):
            is_outer = index == 0 or index == len(_PIPELINE) - 1
            chip_color = (COLORS["PRIMARY_DEEP"] if is_outer
                          else COLORS["GLASS_INPUT"])
            border_color = COLORS["ACCENT"] if is_outer else COLORS["BORDER"]

            chip = ctk.CTkFrame(strip, corner_radius=14, fg_color=chip_color,
                                border_width=1, border_color=border_color)
            chip.pack(side="left", expand=True, fill="both",
                      padx=(0, 4), ipady=8)
            chip_text = ctk.CTkLabel(
                chip, text=step, font=FONTS["SMALL"],
                text_color=(COLORS["TEXT"] if is_outer
                            else COLORS["TEXT_MUTED"]))
            chip_text.pack(padx=8, pady=4)

            if index < len(_PIPELINE) - 1:
                arrow = ctk.CTkLabel(strip, text=ICONS["ARROW"],
                                     font=FONTS["SUBHEADING"],
                                     text_color=COLORS["ACCENT"])
                arrow.pack(side="left", padx=2)

    def _build_layer_cards(self):
        """Three glass cards, one per encryption layer."""
        row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        row.pack(fill="x", padx=2, pady=(0, 8))

        for index, layer in enumerate(_LAYERS):
            card = self._card(row)
            card.pack(side="left", fill="both", expand=True,
                      padx=(0 if index == 0 else 4,
                            4 if index == len(_LAYERS) - 1 else 0))

            header = ctk.CTkFrame(card, fg_color="transparent")
            header.pack(fill="x", padx=16, pady=(16, 4))
            number = ctk.CTkLabel(header, text=layer["number"],
                                  font=FONTS["SUBHEADING"],
                                  text_color=COLORS["ACCENT"])
            number.pack(side="left")
            name = ctk.CTkLabel(header, text=layer["name"],
                                font=FONTS["SUBHEADING"],
                                text_color=COLORS["TEXT"])
            name.pack(side="left", padx=(8, 0))

            divider = ctk.CTkFrame(card, height=1,
                                   fg_color=COLORS["BORDER_SOFT"],
                                   corner_radius=0)
            divider.pack(fill="x", padx=16, pady=(0, 8))

            description = ctk.CTkLabel(
                card, text=layer["description"], font=FONTS["SMALL"],
                text_color=COLORS["TEXT_MUTED"], justify="left",
                anchor="w", wraplength=260,
            )
            description.pack(anchor="w", padx=16, pady=(0, 8))

            formula = ctk.CTkLabel(card, text=layer["formula"],
                                   font=FONTS["MONO_SMALL"],
                                   text_color=COLORS["ACCENT"], anchor="w")
            formula.pack(anchor="w", padx=16, pady=(0, 16))

    def _build_footer(self):
        """A gorgeous animated footer at the very bottom of the page."""
        card = glass_panel(self.scroll)
        card.pack(fill="x", padx=2, pady=(16, 24))
        self._loading_cards.append(card)

        bind_smart_hover(
            card,
            lambda: COLORS["GLASS"], lambda: COLORS["GLASS_HOVER"],
            lambda: COLORS["BORDER"], lambda: COLORS["ACCENT"],
        )

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(pady=16)

        # Small medallion/logo
        medallion = ctk.CTkFrame(
            inner, corner_radius=12, width=32, height=32,
            fg_color=COLORS["TINT_BLUE"],
            border_width=1, border_color=COLORS["ACCENT"]
        )
        medallion.pack(side="left", padx=(0, 12))
        medallion.pack_propagate(False)

        icon = ctk.CTkLabel(medallion, text=ICONS["LOGO"],
                            font=("Segoe UI", 14, "bold"),
                            text_color=COLORS["ACCENT"])
        icon.place(relx=0.5, rely=0.5, anchor="center")

        text_container = ctk.CTkFrame(inner, fg_color="transparent")
        text_container.pack(side="left")

        title = ctk.CTkLabel(
            text_container,
            text="Developed By Sams Alif",
            font=FONTS["HEADING"],
            text_color=COLORS["TEXT"],
            anchor="w"
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            text_container,
            text="Secure Multi-Layer Text Encryption System",
            font=FONTS["MICRO"],
            text_color=COLORS["TEXT_FAINT"],
            anchor="w"
        )
        subtitle.pack(anchor="w")

    # ------------------------------------------------------------------ #
    # Loading animation                                                   #
    # ------------------------------------------------------------------ #

    def _animate_loading(self):
        """
        Fade the cards in one after another (staggered "load").
        Cards start darker and brighten into the glass colour.
        """
        self.after(180, lambda: fade_sequence(
            self._loading_cards,
            from_color=COLORS["GLASS_INPUT"],
            to_color=COLORS["GLASS"],
            delay_ms=120, duration_ms=280,
        ))

    # ------------------------------------------------------------------ #
    # Screen lifecycle                                                    #
    # ------------------------------------------------------------------ #

    def on_show(self):
        """Refresh the statistics every time the dashboard opens."""
        self.update_idletasks()
        stats = self.app.session

        self._stat_values["encrypt"].configure(
            text=str(stats.encrypt_count))
        self._stat_values["algorithm"].configure(
            text="Caesar → Vigenere → XOR", font=FONTS["MONO_SMALL"])
        self._stat_values["layers"].configure(text="3")
        self._stat_values["status"].configure(
            text="Ready", font=("Segoe UI", 22, "bold"))