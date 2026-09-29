"""Tkinter desktop IDE for Echo — edit, Run, output."""

from __future__ import annotations

import queue
import re
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, font as tkfont, messagebox, ttk

from echo import __version__
from echo.frontend.tokens import KEYWORDS, TYPE_NAMES
from echo.ide.runner import RunResult, run_source
from echo.runtime.builtins import builtin_names

STARTER = 'say("Hello, Echo!");\n'
GUTTER_WIDTH = 58
MAX_HIGHLIGHT_CHARS = 200_000
IS_MAC = sys.platform == "darwin"

MONO_FONTS = ("JetBrains Mono", "SF Mono", "Menlo", "Cascadia Mono", "Consolas", "DejaVu Sans Mono")
UI_FONTS = ("SF Pro Text", "Inter", "Segoe UI", "Helvetica Neue", "Ubuntu", "DejaVu Sans")

_SYNTAX_RE = re.compile(
    r"(?P<comment>//[^\n]*|/\*[\s\S]*?\*/)"
    r"|(?P<string>\"\"\"[\s\S]*?\"\"\"|'''[\s\S]*?'''"
    r"|\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])*')"
    r"|(?P<number>\b\d+(?:\.\d+)?\b)"
    r"|(?P<name>[A-Za-z_]\w*)"
)
_IMPORT_RE = re.compile(r"^\s*import\b", re.MULTILINE)


class Palette:
    bg = "#0f1117"
    surface = "#161922"
    surface_hi = "#1e2230"
    border = "#252b3b"
    text = "#d8dee9"
    muted = "#7c8699"
    faint = "#4d5668"
    accent = "#5b8cff"
    accent_hi = "#7aa2ff"
    success = "#46c26a"
    danger = "#f4677a"
    selection = "#28344f"
    line_highlight = "#171b26"
    keyword = "#c792f0"
    type_name = "#67d3f5"
    string = "#98d472"
    number = "#ffb86b"
    comment = "#586074"
    builtin = "#5fd0cc"
    call = "#7fa6ff"


def launch(source_path: str | Path | None = None) -> int:
    """Open the Echo IDE window. Blocks until the window is closed."""
    app = EchoIdeApp(source_path=source_path)
    app.run()
    return 0


class FlatButton(tk.Frame):
    """Label-based button so colors survive the macOS aqua theme."""

    def __init__(
        self,
        master: tk.Misc,
        text: str,
        command,
        *,
        font,
        primary: bool = False,
        padx: int = 13,
        pady: int = 6,
    ) -> None:
        self._idle_bg = Palette.accent if primary else Palette.surface_hi
        self._hover_bg = Palette.accent_hi if primary else Palette.border
        fg = "#ffffff" if primary else Palette.text
        super().__init__(master, bg=self._idle_bg, highlightthickness=0, bd=0, cursor="hand2")
        self._command = command
        self._label = tk.Label(
            self,
            text=text,
            bg=self._idle_bg,
            fg=fg,
            font=font,
            padx=padx,
            pady=pady,
            cursor="hand2",
        )
        self._label.pack()
        for widget in (self, self._label):
            widget.bind("<Enter>", lambda _e: self._paint(self._hover_bg))
            widget.bind("<Leave>", lambda _e: self._paint(self._idle_bg))
            widget.bind("<ButtonRelease-1>", self._on_click)

    def _paint(self, color: str) -> None:
        self.configure(bg=color)
        self._label.configure(bg=color)

    def _on_click(self, _event: tk.Event) -> None:
        self._paint(self._hover_bg)
        self._command()


class EditorText(tk.Text):
    """Text widget that emits <<Change>> on edits, cursor moves, and scrolls."""

    def __init__(self, master: tk.Misc, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self._proxy_target = f"{self._w}_actual"
        self.tk.call("rename", self._w, self._proxy_target)
        self.tk.createcommand(self._w, self._proxy)

    def _proxy(self, *args: str):
        try:
            result = self.tk.call((self._proxy_target,) + args)
        except tk.TclError:
            return None
        if args[0] in ("insert", "delete", "replace", "xview", "yview") or (
            args[:2] == ("mark", "set") and len(args) > 2 and args[2] == "insert"
        ):
            self.event_generate("<<Change>>", when="tail")
        return result


class LineNumbers(tk.Canvas):
    def __init__(self, master: tk.Misc, *, editor: tk.Text, font) -> None:
        super().__init__(
            master,
            width=GUTTER_WIDTH,
            bg=Palette.bg,
            highlightthickness=0,
            bd=0,
            takefocus=False,
        )
        self._editor = editor
        self._font = font

    def redraw(self) -> None:
        self.delete("all")
        current = int(self._editor.index(tk.INSERT).split(".")[0])
        index = self._editor.index("@0,0")
        while True:
            metrics = self._editor.dlineinfo(index)
            if metrics is None:
                break
            line = int(index.split(".")[0])
            self.create_text(
                GUTTER_WIDTH - 14,
                metrics[1],
                anchor="ne",
                text=str(line),
                font=self._font,
                fill=Palette.text if line == current else Palette.faint,
            )
            index = self._editor.index(f"{index}+1line")


class EchoIdeApp:
    def __init__(self, source_path: str | Path | None = None) -> None:
        self.root = tk.Tk()
        self.root.title(f"Echo IDE {__version__}")
        self.root.geometry("1040x720")
        self.root.minsize(820, 560)
        self.root.configure(bg=Palette.bg)

        self._mono = self._pick_font(MONO_FONTS, "Courier", 13 if IS_MAC else 11)
        self._mono_small = (self._mono[0], self._mono[1] - 2)
        self._ui = self._pick_font(UI_FONTS, "Helvetica", 12 if IS_MAC else 9)
        self._ui_bold = (*self._ui, "bold")

        self.path: Path | None = None
        self._dirty = False
        self._running = False
        self._baseline = ""
        self._highlight_job: str | None = None
        self._results: queue.Queue[tuple[RunResult, float]] = queue.Queue()

        self._style_scrollbars()
        self._build_menu()
        self._build_toolbar()
        self._build_status_bar()
        self._build_body()
        self._bind_keys()

        if source_path is not None:
            self._open_path(Path(source_path).expanduser().resolve())
        else:
            self._load_text(STARTER)
        self._show_output_placeholder()

        self.root.protocol("WM_DELETE_WINDOW", self._on_quit)
        self.editor.focus_set()

    def run(self) -> None:
        self.root.mainloop()

    # ------------------------------------------------------------------ setup

    def _pick_font(self, candidates: tuple[str, ...], fallback: str, size: int) -> tuple[str, int]:
        available = set(tkfont.families(self.root))
        for name in candidates:
            if name in available:
                return (name, size)
        return (fallback, size)

    def _style_scrollbars(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "Echo.Vertical.TScrollbar",
            gripcount=0,
            background=Palette.border,
            darkcolor=Palette.border,
            lightcolor=Palette.border,
            troughcolor=Palette.bg,
            bordercolor=Palette.bg,
            arrowcolor=Palette.bg,
            arrowsize=0,
            width=10,
        )
        style.map("Echo.Vertical.TScrollbar", background=[("active", Palette.surface_hi)])

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New", command=self._new, accelerator=self._accel("N"))
        file_menu.add_command(label="Open…", command=self._open, accelerator=self._accel("O"))
        file_menu.add_command(label="Save", command=self._save, accelerator=self._accel("S"))
        file_menu.add_command(label="Save As…", command=self._save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self._on_quit, accelerator=self._accel("Q"))
        menubar.add_cascade(label="File", menu=file_menu)

        run_menu = tk.Menu(menubar, tearoff=0)
        run_menu.add_command(label="Run", command=self._run, accelerator=self._accel("R"))
        run_menu.add_command(label="Clear Output", command=self._clear_output)
        menubar.add_cascade(label="Run", menu=run_menu)

        self.root.config(menu=menubar)

    def _accel(self, key: str) -> str:
        return f"Cmd+{key}" if IS_MAC else f"Ctrl+{key}"

    def _build_toolbar(self) -> None:
        bar = tk.Frame(self.root, bg=Palette.surface)
        bar.pack(side=tk.TOP, fill=tk.X)
        inner = tk.Frame(bar, bg=Palette.surface)
        inner.pack(fill=tk.X, padx=14, pady=10)

        brand = tk.Frame(inner, bg=Palette.surface)
        brand.pack(side=tk.LEFT, padx=(0, 16))
        tk.Label(brand, text="◆", bg=Palette.surface, fg=Palette.accent, font=self._ui_bold).pack(side=tk.LEFT)
        tk.Label(
            brand, text="Echo", bg=Palette.surface, fg=Palette.text, font=self._ui_bold, padx=6
        ).pack(side=tk.LEFT)

        FlatButton(inner, "▶  Run", self._run, font=self._ui_bold, primary=True).pack(side=tk.LEFT)
        for label, command in (("Open", self._open), ("Save", self._save)):
            FlatButton(inner, label, command, font=self._ui).pack(side=tk.LEFT, padx=(8, 0))

        self.file_chip = tk.Label(
            inner,
            text="untitled.echo",
            bg=Palette.surface,
            fg=Palette.muted,
            font=self._ui,
        )
        self.file_chip.pack(side=tk.RIGHT)

        tk.Frame(self.root, bg=Palette.border, height=1).pack(side=tk.TOP, fill=tk.X)

    def _build_body(self) -> None:
        panes = tk.PanedWindow(
            self.root,
            orient=tk.VERTICAL,
            bg=Palette.border,
            sashwidth=5,
            sashrelief=tk.FLAT,
            bd=0,
            handlesize=0,
            handlepad=0,
        )
        panes.pack(fill=tk.BOTH, expand=True)
        panes.add(self._build_editor_pane(panes), minsize=180, stretch="always")
        panes.add(self._build_output_pane(panes), minsize=110, stretch="never", height=210)

    def _build_editor_pane(self, master: tk.Misc) -> tk.Frame:
        frame = tk.Frame(master, bg=Palette.bg)
        self.editor = EditorText(
            frame,
            wrap=tk.NONE,
            undo=True,
            font=self._mono,
            bg=Palette.bg,
            fg=Palette.text,
            insertbackground=Palette.accent,
            insertwidth=2,
            selectbackground=Palette.selection,
            selectforeground=Palette.text,
            inactiveselectbackground=Palette.selection,
            highlightthickness=0,
            bd=0,
            padx=12,
            pady=10,
            spacing1=2,
            spacing3=2,
            tabs="2c",
        )
        self.gutter = LineNumbers(frame, editor=self.editor, font=self._mono_small)
        scrollbar = ttk.Scrollbar(
            frame,
            orient=tk.VERTICAL,
            style="Echo.Vertical.TScrollbar",
            command=self.editor.yview,
        )
        self.editor.configure(yscrollcommand=scrollbar.set)

        self.gutter.pack(side=tk.LEFT, fill=tk.Y)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.editor.tag_configure("current_line", background=Palette.line_highlight)
        for tag, color in (
            ("comment", Palette.comment),
            ("string", Palette.string),
            ("number", Palette.number),
            ("keyword", Palette.keyword),
            ("type", Palette.type_name),
            ("builtin", Palette.builtin),
            ("call", Palette.call),
        ):
            self.editor.tag_configure(tag, foreground=color)
        self.editor.tag_lower("current_line")

        self.editor.bind("<<Change>>", self._on_change)
        self.editor.bind("<<Modified>>", self._on_modified)
        self.editor.bind("<Configure>", lambda _e: self.gutter.redraw())
        self.editor.bind("<Tab>", self._on_tab)
        self.editor.bind("<Return>", self._on_return)
        return frame

    def _build_output_pane(self, master: tk.Misc) -> tk.Frame:
        frame = tk.Frame(master, bg=Palette.surface)

        header = tk.Frame(frame, bg=Palette.surface)
        header.pack(side=tk.TOP, fill=tk.X, padx=14, pady=(8, 6))
        tk.Label(
            header, text="OUTPUT", bg=Palette.surface, fg=Palette.muted, font=self._ui_bold
        ).pack(side=tk.LEFT)
        self.status_pill = tk.Label(
            header, text="● Ready", bg=Palette.surface, fg=Palette.muted, font=self._ui, padx=12
        )
        self.status_pill.pack(side=tk.LEFT)
        FlatButton(header, "Clear", self._clear_output, font=self._ui, padx=10, pady=3).pack(
            side=tk.RIGHT
        )

        body = tk.Frame(frame, bg=Palette.surface)
        body.pack(fill=tk.BOTH, expand=True)
        self.output = tk.Text(
            body,
            wrap=tk.WORD,
            font=self._mono_small,
            bg=Palette.surface,
            fg=Palette.text,
            insertbackground=Palette.accent,
            selectbackground=Palette.selection,
            highlightthickness=0,
            bd=0,
            padx=14,
            pady=4,
            state=tk.DISABLED,
        )
        scrollbar = ttk.Scrollbar(
            body, orient=tk.VERTICAL, style="Echo.Vertical.TScrollbar", command=self.output.yview
        )
        self.output.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.output.tag_configure("stderr", foreground=Palette.danger)
        self.output.tag_configure("meta", foreground=Palette.faint)
        return frame

    def _build_status_bar(self) -> None:
        tk.Frame(self.root, bg=Palette.border, height=1).pack(side=tk.BOTTOM, fill=tk.X)
        bar = tk.Frame(self.root, bg=Palette.surface)
        bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_path = tk.Label(
            bar, text="untitled.echo", bg=Palette.surface, fg=Palette.muted, font=self._ui
        )
        self.status_path.pack(side=tk.LEFT, padx=14, pady=5)
        tk.Label(
            bar, text=f"Echo {__version__}", bg=Palette.surface, fg=Palette.faint, font=self._ui
        ).pack(side=tk.RIGHT, padx=(0, 14))
        self.status_caret = tk.Label(
            bar, text="Ln 1, Col 1", bg=Palette.surface, fg=Palette.muted, font=self._ui
        )
        self.status_caret.pack(side=tk.RIGHT, padx=14)

    def _bind_keys(self) -> None:
        bindings = {
            "n": self._new,
            "o": self._open,
            "s": self._save,
            "r": self._run,
            "q": self._on_quit,
        }
        for key, command in bindings.items():
            for modifier in ("Control", "Command"):
                self.root.bind_all(f"<{modifier}-{key}>", lambda _e, c=command: self._shortcut(c))
        self.root.bind_all("<F5>", lambda _e: self._shortcut(self._run))

    def _shortcut(self, command) -> str:
        command()
        return "break"

    # ------------------------------------------------------------------ editor

    def _load_text(self, text: str) -> None:
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", text)
        self.editor.edit_reset()
        self.editor.edit_modified(False)
        self._baseline = text
        self._dirty = False
        self._refresh_labels()
        self._highlight()
        self.gutter.redraw()

    def _editor_text(self) -> str:
        return self.editor.get("1.0", "end-1c")

    def _on_change(self, _event: tk.Event | None = None) -> None:
        self.gutter.redraw()
        line, column = self.editor.index(tk.INSERT).split(".")
        self.status_caret.configure(text=f"Ln {line}, Col {int(column) + 1}")
        self.editor.tag_remove("current_line", "1.0", tk.END)
        self.editor.tag_add("current_line", "insert linestart", "insert lineend+1c")

    def _on_modified(self, _event: tk.Event | None = None) -> None:
        if not self.editor.edit_modified():
            return
        self.editor.edit_modified(False)
        self._dirty = self._editor_text() != self._baseline
        self._refresh_labels()
        self._schedule_highlight()

    def _on_tab(self, _event: tk.Event) -> str:
        self.editor.insert(tk.INSERT, "  ")
        return "break"

    def _on_return(self, _event: tk.Event) -> str:
        line = self.editor.get("insert linestart", "insert")
        indent = line[: len(line) - len(line.lstrip(" "))]
        if line.rstrip().endswith("{"):
            indent += "  "
        self.editor.insert(tk.INSERT, f"\n{indent}")
        self.editor.see(tk.INSERT)
        return "break"

    def _schedule_highlight(self) -> None:
        if self._highlight_job is not None:
            self.root.after_cancel(self._highlight_job)
        self._highlight_job = self.root.after(120, self._highlight)

    def _highlight(self) -> None:
        self._highlight_job = None
        source = self._editor_text()
        for tag in ("comment", "string", "number", "keyword", "type", "builtin", "call"):
            self.editor.tag_remove(tag, "1.0", tk.END)
        if len(source) > MAX_HIGHLIGHT_CHARS:
            return
        builtins = builtin_names()
        for match in _SYNTAX_RE.finditer(source):
            kind = match.lastgroup
            if kind == "name":
                word = match.group()
                if word in KEYWORDS:
                    kind = "keyword"
                elif word in TYPE_NAMES:
                    kind = "type"
                elif word in builtins:
                    kind = "builtin"
                elif source[match.end() :].lstrip(" ").startswith("("):
                    kind = "call"
                else:
                    continue
            start = self.editor.index(f"1.0+{match.start()}c")
            end = self.editor.index(f"1.0+{match.end()}c")
            self.editor.tag_add(kind, start, end)

    # -------------------------------------------------------------------- file

    def _refresh_labels(self) -> None:
        name = self.path.name if self.path else "untitled.echo"
        mark = " •" if self._dirty else ""
        self.root.title(f"Echo IDE — {name}{mark}")
        self.file_chip.configure(text=f"{name}{mark}", fg=Palette.text if self._dirty else Palette.muted)
        self.status_path.configure(text=str(self.path) if self.path else "untitled.echo")

    def _confirm_discard(self) -> bool:
        if not self._dirty:
            return True
        return messagebox.askyesno("Unsaved changes", "Discard unsaved changes?", parent=self.root)

    def _new(self) -> None:
        if not self._confirm_discard():
            return
        self.path = None
        self._load_text(STARTER)

    def _open(self) -> None:
        if not self._confirm_discard():
            return
        chosen = filedialog.askopenfilename(
            parent=self.root,
            title="Open Echo file",
            filetypes=[("Echo files", "*.echo"), ("All files", "*.*")],
        )
        if chosen:
            self._open_path(Path(chosen))

    def _open_path(self, path: Path) -> None:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Open failed", str(exc), parent=self.root)
            return
        self.path = path
        self._load_text(text)

    def _save(self) -> None:
        if self.path is None:
            self._save_as()
            return
        self._write_path(self.path)

    def _save_as(self) -> None:
        chosen = filedialog.asksaveasfilename(
            parent=self.root,
            title="Save Echo file",
            defaultextension=".echo",
            filetypes=[("Echo files", "*.echo"), ("All files", "*.*")],
        )
        if not chosen:
            return
        path = Path(chosen)
        if path.suffix == "":
            path = path.with_suffix(".echo")
        self._write_path(path)

    def _write_path(self, path: Path) -> None:
        text = self._editor_text()
        try:
            path.write_text(text, encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Save failed", str(exc), parent=self.root)
            return
        self.path = path
        self._baseline = text
        self._dirty = False
        self._refresh_labels()

    # --------------------------------------------------------------------- run

    def _set_status(self, text: str, color: str) -> None:
        self.status_pill.configure(text=f"● {text}", fg=color)

    def _clear_output(self) -> None:
        self.output.configure(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.configure(state=tk.DISABLED)
        self._set_status("Ready", Palette.muted)

    def _show_output_placeholder(self) -> None:
        self._write_output("Run your program to see output here.\n", "meta")

    def _write_output(self, text: str, tag: str | None = None) -> None:
        self.output.configure(state=tk.NORMAL)
        self.output.insert(tk.END, text, tag or ())
        self.output.see(tk.END)
        self.output.configure(state=tk.DISABLED)

    def _run(self) -> None:
        if self._running:
            return
        source = self._editor_text()

        # Imports resolve from disk, so the file must match the buffer.
        if _IMPORT_RE.search(source) and self._dirty:
            self._save()
            if self._dirty:
                return

        self._running = True
        self._clear_output()
        self._set_status("Running…", Palette.accent)
        path = self.path
        started = time.perf_counter()

        def worker() -> None:
            result = run_source(
                source,
                filename=str(path) if path else "<ide>",
                path=path if path and path.is_file() else None,
            )
            self._results.put((result, time.perf_counter() - started))

        threading.Thread(target=worker, daemon=True).start()
        self._poll_run()

    def _poll_run(self) -> None:
        # Tk calls must stay on the UI thread, so the worker hands results over a queue.
        try:
            result, elapsed = self._results.get_nowait()
        except queue.Empty:
            if self._running:
                self.root.after(40, self._poll_run)
            return
        self._on_run_done(result, elapsed)

    def _on_run_done(self, result: RunResult, elapsed: float) -> None:
        self._running = False
        self.output.configure(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.configure(state=tk.DISABLED)

        if result.stdout:
            self._write_output(result.stdout)
        if result.stderr:
            if result.stdout and not result.stdout.endswith("\n"):
                self._write_output("\n")
            self._write_output(result.stderr, "stderr")
        if not result.output:
            self._write_output("(no output)\n", "meta")

        if result.exit_code == 0:
            self._set_status(f"Finished in {elapsed:.2f}s", Palette.success)
        else:
            self._set_status(f"Exited with code {result.exit_code}", Palette.danger)

    def _on_quit(self) -> None:
        if self._confirm_discard():
            self.root.destroy()
