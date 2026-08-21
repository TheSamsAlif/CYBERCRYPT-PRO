"""
analysis_screen.py
==================

Phase 4 : the Security Analysis dashboard.

A premium, fully educational overview of the last encryption run:

    * summary hero card      (status, stack, time, characters, export)
    * encryption layers      (the three layers + completed status)
    * message statistics     (characters, words, lines, uniqueness)
    * key information        (key lengths, generated random values)
    * performance            (encryption / decryption / layer timings)
    * educational strength   (animated ring + band label + disclaimer)
    * output analysis        (cipher length, printability, encoding)
    * encryption timeline    (Start -> Layer 1..3 -> Completed)
    * algorithm overview     (purpose / advantages / limitations)

Everything updates automatically when a new encryption finishes
(the app calls refresh_report()). Reports NEVER contain the plain
text - privacy by design. Every metric has a hover tooltip.
"""

from __future__ import annotations

import tkinter.filedialog as filedialog

import customtkinter as ctk

from cybercrypt.analysis import (
    ALGORITHM_OVERVIEW,
    ALGORITHM_STACK,
    DISCLAIMER,
    AnalysisReport,
    format_duration,
)
from cybercrypt.ui.animation import fade_sequence
from cybercrypt.ui.charts import (
    ProgressBar,
    ProgressRing,
    TimelineChart,
    animate_counter,
)
from cybercrypt.ui.screens.base_screen import BaseScreen
from cybercrypt.ui.theme import COLORS, FONTS, ICONS
from cybercrypt.ui.tooltip import bind_tooltip
from cybercrypt.ui.widgets import (
    Toast,
    badge,
    glass_panel,
    primary_button,
    secondary_button,
)

# Strength band -> ring colour (educational palette).
_BAND_COLORS = {
    "Very Basic":            COLORS["WARNING"],
    "Basic":                 COLORS["WARNING"],
    "Educational":           COLORS["ACCENT"],
    "Layered":               COLORS["ACCENT"],
    "Advanced Demonstration": COLORS["SUCCESS"],
}


class AnalysisScreen(BaseScreen):
    """The Security Analysis dashboard."""

    # ------------------------------------------------------------------ #
    # Construction                                                        #
    # ------------------------------------------------------------------ #

    def _build_widgets(self):
        self._loading_cards = []
        self._report = None

        self._build_header()

        # Scrollable content (the page is taller than the window).
        self.scroll = self._page_scroll()

        self._build_summary_card()
        self._build_columns()
        self._build_algorithm_card()
        self._build_disclaimer_footer()
        self._animate_loading()
        self._show_empty_state()

    def _build_header(self):
        """Page title + live status chip (shared grid position)."""
        _title, _subtitle = self._page_header(
            "Security Analysis",
            "Educational metrics for the last encryption session.")

        self._status_chip = badge(
            self, f"{ICONS['STATUS']}  Waiting for Encryption",
            color=COLORS["TEXT_FAINT"])
        self._status_chip.place(relx=0.985, y=self.header_top(),
                                anchor="ne")

    # ------------------------------------------------------------------ #
    # Cards                                                               #
    # ------------------------------------------------------------------ #

    def _card(self, title: str, icon: str, tooltip: str) -> ctk.CTkFrame:
        """A glass card with heading, stored for the loading animation."""
        card = glass_panel(self._column)
        self._loading_cards.append(card)

        heading = ctk.CTkLabel(card, text=f"{icon}  {title}",
                               font=FONTS["SUBHEADING"],
                               text_color=COLORS["TEXT"])
        heading.pack(padx=20, pady=(14, 10), anchor="w")
        bind_tooltip(heading, tooltip)
        return card

    def _build_summary_card(self):
        """Hero card: session status, stack, time, characters, export."""
        card = glass_panel(self.scroll)
        card.pack(fill="x", padx=2, pady=(2, 8))
        self._loading_cards.append(card)

        left = ctk.CTkFrame(card, fg_color="transparent")
        left.pack(side="left", padx=20, pady=18)

        self._summary_medallion = ctk.CTkFrame(
            left, corner_radius=30, width=60, height=60,
            fg_color="#0E2A1C", border_width=2,
            border_color=COLORS["SUCCESS"])
        self._summary_medallion.pack(side="left", padx=(0, 16))
        medallion_icon = ctk.CTkLabel(self._summary_medallion,
                                      text=ICONS["CHECK"],
                                      font=("Segoe UI", 26, "bold"),
                                      text_color=COLORS["SUCCESS"])
        medallion_icon.place(relx=0.5, rely=0.5, anchor="center")

        text = ctk.CTkFrame(left, fg_color="transparent")
        text.pack(side="left")

        self._summary_title = ctk.CTkLabel(
            text, text="Encryption Successful",
            font=FONTS["HEADING"], text_color=COLORS["TEXT"])
        self._summary_title.pack(anchor="w")

        self._summary_subtitle = ctk.CTkLabel(
            text, text="Processing Completed",
            font=FONTS["SMALL"], text_color=COLORS["TEXT_MUTED"])
        self._summary_subtitle.pack(anchor="w", pady=(2, 0))
        bind_tooltip(self._summary_subtitle,
                     "The three layers finished processing; all metrics "
                     "below reflect that run.")

        # Metric chips: stack / time / characters.
        chips = ctk.CTkFrame(card, fg_color="transparent")
        chips.pack(side="left", padx=(10, 6), pady=18)

        self._stack_chip = badge(chips, ALGORITHM_STACK, COLORS["ACCENT"])
        self._stack_chip.pack(side="left", padx=(0, 8))
        bind_tooltip(self._stack_chip,
                     "The fixed encryption order of the engine.")

        self._time_chip = badge(chips, "Time: \u2014", COLORS["ACCENT"])
        self._time_chip.pack(side="left", padx=(0, 8))
        bind_tooltip(self._time_chip,
                     "Total processing time of the encryption run.")

        self._chars_chip = badge(chips, "Characters: \u2014",
                                 COLORS["ACCENT"])
        self._chars_chip.pack(side="left", padx=(0, 8))
        bind_tooltip(self._chars_chip,
                     "Length of the encrypted message.")

        # Export actions (report only - never the plain text).
        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(side="right", padx=18, pady=18)

        txt_button = secondary_button(actions, f"{ICONS['COPY']}  TXT",
                                      lambda: self._export("txt"))
        txt_button.pack(side="left", padx=(0, 8))
        bind_tooltip(txt_button,
                     "Export the analysis report as a text file. "
                     "The plain text is never included.")

        json_button = primary_button(actions, "JSON",
                                     lambda: self._export("json"))
        json_button.pack(side="left")
        bind_tooltip(json_button,
                     "Export the analysis report as structured JSON. "
                     "The plain text is never included.")

    def _build_columns(self):
        """Two columns of cards: stats on the left, charts on the right."""
        row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        row.pack(fill="x", padx=2)

        self._column = ctk.CTkFrame(row, fg_color="transparent")
        self._column.pack(side="left", fill="both", expand=True,
                          padx=(0, 6))
        self._build_layers_card()
        self._build_message_card()
        self._build_keys_card()
        self._build_strength_card()

        self._column = ctk.CTkFrame(row, fg_color="transparent")
        self._column.pack(side="left", fill="both", expand=True,
                          padx=(6, 0))
        self._build_performance_card()
        self._build_output_card()
        self._build_timeline_card()

    # -- Card 1: encryption layers ------------------------------------- #

    def _build_layers_card(self):
        card = self._card("Encryption Layers", ICONS["LAYERS"],
                          "The three layers of the engine, in order.")
        self._layer_rows = []

        for index, (name, icon) in enumerate(zip(
                ("Caesar Cipher", "Vigen\u00e8re Cipher",
                 "Random XOR Layer"),
                ("A", "V", "X"))):
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=4)

            medallion = ctk.CTkFrame(row, corner_radius=13, width=26,
                                     height=26,
                                     fg_color=COLORS["GLASS_INPUT"],
                                     border_width=1,
                                     border_color=COLORS["SUCCESS"])
            medallion.pack(side="left")
            medallion.pack_propagate(False)
            icon_label = ctk.CTkLabel(medallion, text=icon,
                                      font=("Segoe UI", 11, "bold"),
                                      text_color=COLORS["SUCCESS"])
            icon_label.place(relx=0.5, rely=0.5, anchor="center")

            name_label = ctk.CTkLabel(row, text=name, font=FONTS["BODY"],
                                      text_color=COLORS["TEXT"])
            name_label.pack(side="left", padx=(10, 0))

            dot = ctk.CTkLabel(row, text=ICONS["DOT"],
                               font=("Segoe UI", 9),
                               text_color=COLORS["SUCCESS"])
            dot.pack(side="right", padx=(0, 8))

            status_label = ctk.CTkLabel(row, text="Completed",
                                        font=FONTS["MICRO"],
                                        text_color=COLORS["SUCCESS"])
            status_label.pack(side="right")

            tooltip = {
                0: "Layer 1: every character shifted by a fixed amount.",
                1: "Layer 2: every character shifted by a keyword-driven "
                   "amount.",
                2: "Layer 3: every character XOR-ed with a seeded "
                   "pseudo-random keystream.",
            }[index]
            for child in (row, medallion, icon_label, name_label,
                          dot, status_label):
                bind_tooltip(child, tooltip)

            self._layer_rows.append({"name": name_label, "status":
                                     status_label})

    # -- Card 2: message statistics ------------------------------------- #

    def _build_message_card(self):
        card = self._card("Message Statistics", ICONS["SESSIONS"],
                          "Basic statistics about the original message.")
        self._message_values = {}

        rows = (
            ("Character Count", "characters",
             "Total number of characters in the message."),
            ("Word Count", " words",
             "Groups of non-space characters separated by whitespace."),
            ("Line Count", " lines",
             "How many lines the message spans."),
            ("Unique Characters", " unique",
             "Distinct characters used (diversity of the message)."),
            ("Whitespace Count", " spaces",
             "Spaces, tabs and newlines inside the message."),
        )
        for caption, suffix, tooltip in rows:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=3)

            caption_label = ctk.CTkLabel(row, text=caption,
                                         font=FONTS["SMALL"],
                                         text_color=COLORS["TEXT_MUTED"])
            caption_label.pack(side="left")
            bind_tooltip(caption_label, tooltip)

            value_label = ctk.CTkLabel(row, text="\u2014",
                                       font=FONTS["SUBHEADING"],
                                       text_color=COLORS["TEXT"])
            value_label.pack(side="right")
            bind_tooltip(value_label, tooltip)

            self._message_values[caption] = (value_label, suffix)

    # -- Card 3: key information ---------------------------------------- #

    def _build_keys_card(self):
        card = self._card("Key Information", ICONS["ALGO"],
                          "Details about the keys used for this run.")
        self._key_values = {}

        rows = (
            ("Secret Key Length", " chars",
             "The Vigen\u00e8re keyword length (the 'secret key')."),
            ("Random Key Length", " digits",
             "How many digits the XOR seed contains."),
            ("Generated Random Values", " values",
             "How many pseudo-random values the Linear Congruential "
             "Generator produced (one per message character)."),
        )
        for caption, suffix, tooltip in rows:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=3)

            caption_label = ctk.CTkLabel(row, text=caption,
                                         font=FONTS["SMALL"],
                                         text_color=COLORS["TEXT_MUTED"])
            caption_label.pack(side="left")
            bind_tooltip(caption_label, tooltip)

            value_label = ctk.CTkLabel(row, text="\u2014",
                                       font=FONTS["SUBHEADING"],
                                       text_color=COLORS["TEXT"])
            value_label.pack(side="right")
            bind_tooltip(value_label, tooltip)

            self._key_values[caption] = (value_label, suffix)

    # -- Card 5: educational strength meter ----------------------------- #

    def _build_strength_card(self):
        card = self._card(
            "Educational Strength Meter", ICONS["SHIELD"],
            "An educational complexity score - NOT real cryptographic "
            "strength.")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=(2, 6))

        self._ring = ProgressRing(inner, size=112, thickness=13)
        self._ring.pack(side="left", padx=(4, 18), pady=4)

        info = ctk.CTkFrame(inner, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)

        self._level_label = ctk.CTkLabel(info, text="Awaiting data",
                                         font=FONTS["HEADING"],
                                         text_color=COLORS["TEXT_MUTED"])
        self._level_label.pack(anchor="w")

        self._score_label = ctk.CTkLabel(
            info, text="Score \u2014 / 100",
            font=FONTS["SMALL"], text_color=COLORS["TEXT_MUTED"])
        self._score_label.pack(anchor="w", pady=(2, 0))
        bind_tooltip(self._score_label,
                     "Combines the layer stack, key lengths, message "
                     "length and character diversity.")

        disclaimer = ctk.CTkLabel(
            card, text=DISCLAIMER,
            font=FONTS["MICRO"], text_color=COLORS["WARNING"],
            justify="left", anchor="w", wraplength=520)
        disclaimer.pack(fill="x", padx=20, pady=(4, 14))
        bind_tooltip(disclaimer,
                     "Educational complexity of the demonstration only.")

    # -- Card 4: performance -------------------------------------------- #

    def _build_performance_card(self):
        card = self._card("Performance", ICONS["CLOCK"],
                          "Measured processing times of the last run.")
        self._performance_rows = []

        rows = (
            ("Encryption Time", "time taken by the three layers."),
            ("Decryption Time", "time taken by the reverse layers."),
            ("Average Layer Time", "encryption time divided by 3."),
            ("Total Processing Time", "encryption + decryption."),
        )
        for caption, tooltip in rows:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=3)

            caption_label = ctk.CTkLabel(row, text=caption,
                                         font=FONTS["SMALL"],
                                         text_color=COLORS["TEXT_MUTED"])
            caption_label.pack(side="left")
            bind_tooltip(caption_label, tooltip)

            value_label = ctk.CTkLabel(row, text="\u2014",
                                       font=FONTS["SUBHEADING"],
                                       text_color=COLORS["TEXT"])
            value_label.pack(side="right")
            bind_tooltip(value_label, tooltip)

            bar = ProgressBar(card, height=8)
            bar.pack(fill="x", padx=20, pady=(0, 4))

            self._performance_rows.append((value_label, bar))

    # -- Card 8: output analysis ---------------------------------------- #

    def _build_output_card(self):
        card = self._card("Output Analysis", ICONS["ENCRYPT"],
                          "Statistics about the produced cipher text.")
        self._output_values = {}

        rows = (
            ("Cipher Length", " chars",
             "Length of the final encrypted output."),
            ("Printable Characters", " chars",
             "Characters that can be printed/displayed normally."),
            ("Non-printable Characters", " chars",
             "Unusual characters in the output (often 0 for this "
             "alphabet)."),
            ("Encoding Used", "",
             "The shared 128-character alphabet of the engine."),
        )
        for caption, suffix, tooltip in rows:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=3)

            caption_label = ctk.CTkLabel(row, text=caption,
                                         font=FONTS["SMALL"],
                                         text_color=COLORS["TEXT_MUTED"])
            caption_label.pack(side="left")
            bind_tooltip(caption_label, tooltip)

            value_label = ctk.CTkLabel(row, text="\u2014",
                                       font=FONTS["SUBHEADING"],
                                       text_color=COLORS["TEXT"])
            value_label.pack(side="right")
            bind_tooltip(value_label, tooltip)

            self._output_values[caption] = (value_label, suffix)

    # -- Card 7: encryption timeline ------------------------------------ #

    def _build_timeline_card(self):
        card = self._card("Encryption Timeline", ICONS["ARROW"],
                          "The processing steps, in order, with their "
                          "measured durations.")
        self._timeline = TimelineChart(card, height=210)
        self._timeline.pack(fill="x", padx=8, pady=(0, 14))
        bind_tooltip(self._timeline,
                     "Each node shows one processing step and how long "
                     "it took.")

    # -- Card 6: algorithm overview ------------------------------------- #

    def _build_algorithm_card(self):
        card = glass_panel(self.scroll)
        card.pack(fill="x", padx=2, pady=(0, 8))
        self._loading_cards.append(card)

        heading = ctk.CTkLabel(card, text=f"{ICONS['INFO']}  "
                               "Algorithm Overview",
                               font=FONTS["SUBHEADING"],
                               text_color=COLORS["TEXT"])
        heading.pack(padx=20, pady=(14, 10), anchor="w")
        bind_tooltip(heading,
                     "Purpose, advantages and limitations of each layer.")

        for algorithm in ALGORITHM_OVERVIEW:
            block = ctk.CTkFrame(card, fg_color="transparent")
            block.pack(fill="x", padx=20, pady=(0, 8))

            name = ctk.CTkLabel(block, text=f"{algorithm['icon']}  "
                                 f"{algorithm['name']}",
                                font=FONTS["BODY"],
                                text_color=COLORS["TEXT"])
            name.pack(anchor="w", pady=(0, 2))

            for caption, key, color in (
                    ("Purpose", "purpose", COLORS["TEXT_MUTED"]),
                    ("Advantages", "advantages", COLORS["SUCCESS"]),
                    ("Limitations", "limitations", COLORS["WARNING"])):
                line = ctk.CTkLabel(
                    block,
                    text=f"{caption}:  {algorithm[key]}",
                    font=FONTS["MICRO"],
                    text_color=color,
                    justify="left", anchor="w", wraplength=1050)
                line.pack(anchor="w", padx=(14, 0))
                bind_tooltip(line, f"{caption} of the {algorithm['name']}.")

    def _build_disclaimer_footer(self):
        footer = ctk.CTkLabel(
            self.scroll,
            text="All metrics are educational. This dashboard describes "
                 "the demonstration - it does not claim real-world "
                 "cryptographic security.",
            font=FONTS["MICRO"],
            text_color=COLORS["TEXT_FAINT"],
        )
        footer.pack(pady=(0, 12))

    # ------------------------------------------------------------------ #
    # Data refresh                                                        #
    # ------------------------------------------------------------------ #

    def _set_status_chip(self, text: str, color: str):
        """Update the header status chip."""
        self._status_chip.destroy()
        self._status_chip = badge(self, f"{ICONS['STATUS']}  {text}",
                                  color=color)
        self._status_chip.place(relx=0.985, y=self.header_top(),
                                anchor="ne")

    def _set_metric(self, values: dict, caption: str, text: str,
                    animate: bool = True):
        """Update one metric row's value label."""
        value_label, suffix = values[caption]
        if text in ("", None):
            value_label.configure(text="\u2014")
            return
        if caption == "Encoding Used":
            value_label.configure(text=text, font=FONTS["MONO_SMALL"])
            return
        if isinstance(text, (int, float)):
            animate_counter(value_label, int(text), suffix=suffix)
        else:
            value_label.configure(text=f"{text}{suffix}")

    def refresh_report(self, report: AnalysisReport):
        """
        Update every card with a new analysis report.

        Arguments:
            report : the report of the last encryption run.
        """
        self._report = report

        # --- Summary hero ----------------------------------------------- #
        self._summary_title.configure(text="Encryption Successful")
        self._summary_subtitle.configure(text="Processing Completed")
        self._time_chip.destroy()
        self._time_chip = badge(self._time_chip.master,
                                f"Time: {format_duration(report.total_time)}",
                                COLORS["ACCENT"])
        self._time_chip.pack(side="left", padx=(0, 8))
        self._chars_chip.destroy()
        self._chars_chip = badge(self._chars_chip.master,
                                 f"Characters: {report.cipher_length}",
                                 COLORS["ACCENT"])
        self._chars_chip.pack(side="left", padx=(0, 8))

        # --- Message statistics ----------------------------------------- #
        message_stats = {
            "Character Count": report.char_count,
            "Word Count": report.word_count,
            "Line Count": report.line_count,
            "Unique Characters": report.unique_chars,
            "Whitespace Count": report.whitespace_count,
        }
        for caption, value in message_stats.items():
            self._set_metric(self._message_values, caption, value)

        # --- Key information --------------------------------------------- #
        key_stats = {
            "Secret Key Length": report.secret_key_length,
            "Random Key Length": report.random_key_length,
            "Generated Random Values": report.generated_random_values,
        }
        for caption, value in key_stats.items():
            self._set_metric(self._key_values, caption, value)

        # --- Performance -------------------------------------------------- #
        longest = max(report.encryption_time, report.decryption_time,
                      report.average_layer_time, 1e-9)
        performance = (
            ("Encryption Time", report.encryption_time),
            ("Decryption Time", report.decryption_time),
            ("Average Layer Time", report.average_layer_time),
            ("Total Processing Time", report.total_time),
        )
        for index, (caption, seconds) in enumerate(performance):
            value_label, bar = self._performance_rows[index]
            value_label.configure(
                text=format_duration(seconds),
                text_color=COLORS["TEXT"])
            bar.set_fraction(seconds / longest if seconds else 0.0)

        # --- Strength meter ---------------------------------------------- #
        color = _BAND_COLORS.get(report.strength_level,
                                 COLORS["ACCENT"])
        self._ring.set_color(color)
        self._ring.set_fraction(report.strength_score / 100)
        self._ring.set_text(str(report.strength_score))
        self._level_label.configure(text=report.strength_level,
                                    text_color=color)
        self._score_label.configure(
            text=f"Score {report.strength_score} / 100 "
                 "(educational complexity)")

        # --- Output analysis --------------------------------------------- #
        output_stats = {
            "Cipher Length": report.cipher_length,
            "Printable Characters": report.printable_chars,
            "Non-printable Characters": report.non_printable_chars,
            "Encoding Used": report.encoding,
        }
        for caption, value in output_stats.items():
            self._set_metric(self._output_values, caption, value)

        # --- Timeline ------------------------------------------------------ #
        self._timeline.set_entries(report.timeline)

        self._set_status_chip("Analysis Updated", COLORS["SUCCESS"])

    def _show_empty_state(self):
        """Reset every card to placeholder values (no run yet)."""
        self._report = None
        self._summary_title.configure(text="Awaiting Encryption")
        self._summary_subtitle.configure(
            text="Encrypt a message to populate this dashboard.")
        self._set_metric(self._message_values, "Character Count", None)
        self._set_metric(self._message_values, "Word Count", None)
        self._set_metric(self._message_values, "Line Count", None)
        self._set_metric(self._message_values, "Unique Characters", None)
        self._set_metric(self._message_values, "Whitespace Count", None)
        self._set_metric(self._key_values, "Secret Key Length", None)
        self._set_metric(self._key_values, "Random Key Length", None)
        self._set_metric(self._key_values,
                         "Generated Random Values", None)
        self._set_metric(self._output_values, "Cipher Length", None)
        self._set_metric(self._output_values,
                         "Printable Characters", None)
        self._set_metric(self._output_values,
                         "Non-printable Characters", None)
        self._set_metric(self._output_values, "Encoding Used", None)
        for value_label, _bar in self._performance_rows:
            value_label.configure(text="\u2014")
        self._ring.set_fraction(0.0, animate=False)
        self._ring.set_text("\u2014")
        self._level_label.configure(text="Awaiting data",
                                    text_color=COLORS["TEXT_MUTED"])
        self._score_label.configure(text="Score \u2014 / 100")
        self._timeline.set_entries([])
        self._set_status_chip("Waiting for Encryption",
                              COLORS["TEXT_FAINT"])

    # ------------------------------------------------------------------ #
    # Export (report only - plain text is never written)                  #
    # ------------------------------------------------------------------ #

    def _export(self, kind: str):
        """
        Save the analysis report as TXT or JSON.

        Arguments:
            kind : "txt" or "json".
        """
        if self._report is None:
            Toast.show(self.app, "Nothing to export yet.",
                       kind="warning")
            return

        default_name = f"cybercrypt-report-{kind}.{kind}"
        path = filedialog.asksaveasfilename(
            parent=self.app,
            title="Export Analysis Report",
            defaultextension=f".{kind}",
            initialfile=default_name,
            filetypes=[(kind.upper(), f"*.{kind}")],
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as handle:
                if kind == "json":
                    handle.write(self._report.to_json())
                else:
                    handle.write(self._report.to_text())
        except OSError as error:
            self.app.show_dialog(
                "Export Failed",
                f"The report could not be saved.\n\n{error}",
                kind="error",
            )
            return

        self.app.set_status("Export Complete", kind="success")
        self._set_status_chip("Export Complete", COLORS["SUCCESS"])
        Toast.show(self.app, "Export Complete.", kind="success")
        self.app.after(2400, lambda: self._set_status_chip(
            "Analysis Updated", COLORS["SUCCESS"]))

    # ------------------------------------------------------------------ #
    # Screen lifecycle                                                    #
    # ------------------------------------------------------------------ #

    def on_show(self):
        """Refresh from the latest session report when the page opens."""
        self.update_idletasks()
        report = getattr(self.app.session, "last_analysis", None)
        if report is not None:
            self.refresh_report(report)
        else:
            self._show_empty_state()

    def _animate_loading(self):
        """Staggered fade-in of the cards (premium loading feel)."""
        self.after(180, lambda: fade_sequence(
            self._loading_cards,
            from_color=COLORS["GLASS_INPUT"],
            to_color=COLORS["GLASS"],
            delay_ms=90, duration_ms=260,
        ))
