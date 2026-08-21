"""
architecture_screen.py
======================

Phase 5 : Architecture page.

Visualizes how CyberCrypt Pro is put together:

    * System Architecture   - User -> UI -> Engine -> Analysis -> Output
    * Encryption Flow       - the three layers applied in order
    * Decryption Flow       - the three layers reversed
    * Project Timeline      - Input -> Encryption -> Analysis ->
                              Output -> Export

Every flow is drawn with the reusable FlowChart widget: glass nodes
connected by animated arrows (a bright dot travels along each
connector). All animation stops automatically while the page is
hidden.
"""

from __future__ import annotations

import customtkinter as ctk

from cybercrypt.ui.charts import FlowChart
from cybercrypt.ui.screens.base_screen import BaseScreen
from cybercrypt.ui.theme import COLORS, FONTS, ICONS
from cybercrypt.ui.widgets import section_heading

_ARCHITECTURE_STEPS = (
    (ICONS["USER"] if "USER" in ICONS else "U", "User",
     "sends a message"),
    (ICONS["ENCRYPT"], "UI",
     "CustomTkinter glass interface"),
    (ICONS["SHIELD"], "Encryption Engine",
     "core/ : Caesar \u00b7 Vigen\u00e8re \u00b7 XOR"),
    (ICONS["ANALYSIS"], "Analysis Engine",
     "analysis.py : reports & strength"),
    (ICONS["CHECK"], "Output",
     "cipher \u00b7 report \u00b7 export"),
)

_ENCRYPTION_STEPS = (
    (ICONS["ENCRYPT"], "Input & Keys",
     "message + shift, keyword, seed"),
    ("A", "Layer 1 - Caesar Cipher",
     "fixed shift over 128 characters"),
    ("V", "Layer 2 - Vigen\u00e8re Cipher",
     "keyword-driven shifting"),
    ("X", "Layer 3 - Random XOR Layer",
     "seeded pseudo-random keystream"),
    (ICONS["CHECK"], "Cipher Text",
     "the encrypted result"),
)

_DECRYPTION_STEPS = (
    (ICONS["DECRYPT"], "Cipher & Keys",
     "cipher + the same three keys"),
    ("X", "Layer 3 - Random XOR (reversed)",
     "remove the keystream first"),
    ("V", "Layer 2 - Vigen\u00e8re (reversed)",
     "undo the keyword shifts"),
    ("A", "Layer 1 - Caesar (reversed)",
     "reverse the fixed shift"),
    (ICONS["CHECK"], "Plain Text",
     "the recovered message"),
)

_TIMELINE_STEPS = (
    (ICONS["ENCRYPT"], "Input", "your message"),
    (ICONS["SHIELD"], "Encryption", "three live layers"),
    (ICONS["ANALYSIS"], "Analysis", "educational report"),
    (ICONS["CHECK"], "Output", "cipher + metrics"),
    (ICONS["COPY"], "Export", "TXT or JSON report"),
)


class ArchitectureScreen(BaseScreen):
    """The architecture, flowcharts and project timeline page."""

    # ------------------------------------------------------------------ #
    # Construction                                                        #
    # ------------------------------------------------------------------ #

    def _build_widgets(self):
        self._flow_charts = []

        self._page_header(
            "Architecture",
            "How the application is built and how data flows "
            "through it.")

        self.scroll = self._page_scroll()

        self._build_architecture()
        self._build_flows()
        self._build_timeline()

    def _section_heading(self, icon: str, heading: str):
        """A glass heading card for one section (shared widget)."""
        section_heading(self.scroll, icon, heading)

    def _build_architecture(self):
        """User -> UI -> Engine -> Analysis -> Output."""
        self._section_heading(ICONS["ARCHITECTURE"],
                              "System Architecture")

        diagram = FlowChart(self.scroll, list(_ARCHITECTURE_STEPS),
                            direction="horizontal", node_height=86)
        diagram.pack(fill="x", padx=2)
        self._flow_charts.append(diagram)

        caption = ctk.CTkLabel(
            self.scroll,
            text="The user interacts with the UI; the UI calls the "
                 "engine; the analysis engine inspects the run and "
                 "produces the output and reports.",
            font=FONTS["MICRO"], text_color=COLORS["TEXT_FAINT"])
        caption.pack(anchor="w", padx=22, pady=(8, 4))

    def _build_flows(self):
        """Encryption flow and decryption flow side by side."""
        self._section_heading(ICONS["ARROW"],
                              "Encryption & Decryption Flows")

        row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        row.pack(fill="x", padx=2)

        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True, padx=(0, 6))

        encrypt_title = ctk.CTkLabel(left, text="Encryption Flow",
                                     font=FONTS["BODY"],
                                     text_color=COLORS["ACCENT"])
        encrypt_title.pack(anchor="w", padx=14, pady=(0, 6))

        encrypt_chart = FlowChart(left, list(_ENCRYPTION_STEPS),
                                  direction="vertical")
        encrypt_chart.pack(fill="x")
        self._flow_charts.append(encrypt_chart)

        right = ctk.CTkFrame(row, fg_color="transparent")
        right.pack(side="left", fill="x", expand=True, padx=(6, 0))

        decrypt_title = ctk.CTkLabel(right, text="Decryption Flow",
                                     font=FONTS["BODY"],
                                     text_color=COLORS["ACCENT"])
        decrypt_title.pack(anchor="w", padx=14, pady=(0, 6))

        decrypt_chart = FlowChart(right, list(_DECRYPTION_STEPS),
                                  direction="vertical")
        decrypt_chart.pack(fill="x")
        self._flow_charts.append(decrypt_chart)

    def _build_timeline(self):
        """Input -> Encryption -> Analysis -> Output -> Export."""
        self._section_heading(ICONS["CLOCK"], "Project Timeline")

        timeline = FlowChart(self.scroll, list(_TIMELINE_STEPS),
                             direction="horizontal", node_height=86)
        timeline.pack(fill="x", padx=2)
        self._flow_charts.append(timeline)

        caption = ctk.CTkLabel(
            self.scroll,
            text="One complete journey of the application: type a "
                 "message, watch it being encrypted, study the "
                 "analysis, copy the output and export the report.",
            font=FONTS["MICRO"], text_color=COLORS["TEXT_FAINT"])
        caption.pack(anchor="w", padx=22, pady=(8, 18))

    # ------------------------------------------------------------------ #
    # Screen lifecycle                                                    #
    # ------------------------------------------------------------------ #

    def on_show(self):
        """Reveal the flow nodes with a staggered fade on arrival."""
        self.update_idletasks()
        for index, chart in enumerate(self._flow_charts):
            chart.after(index * 60, chart.reveal)

    def on_shortcut(self):
        """Ctrl+Enter re-runs the reveal animation."""
        self.on_show()
