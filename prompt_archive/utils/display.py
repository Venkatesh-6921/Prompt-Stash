"""
Prompt Archive — Rich display helpers.
Gemini CLI-inspired terminal UI: ASCII logo, tips panel, styled output.
"""
from __future__ import annotations
import platform, socket
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

VAULT_THEME = Theme({
    "vault.brand":   "bold magenta",
    "vault.success": "bright_green",
    "vault.warn":    "yellow",
    "vault.error":   "bold red",
    "vault.info":    "cyan",
    "vault.dim":     "dim",
})
console = Console(theme=VAULT_THEME)

# ── ASCII Logo (PROMPT ARCHIVE) ───────────────────────────────────────────────
_LOGO = [
    "  ██████╗ ██████╗  ██████╗ ███╗   ███╗██████╗ ████████╗",
    "  ██╔══██╗██╔══██╗██╔═══██╗████╗ ████║██╔══██╗╚══██╔══╝",
    "  ██████╔╝██████╔╝██║   ██║██╔████╔██║██████╔╝   ██║   ",
    "  ██╔═══╝ ██╔══██╗██║   ██║██║╚██╔╝██║██╔═══╝    ██║   ",
    "  ██║     ██║  ██║╚██████╔╝██║ ╚═╝ ██║██║        ██║   ",
    "  ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝        ╚═╝   ",
    "",
    "   █████╗ ██████╗  ██████╗██╗  ██╗██╗██╗   ██╗███████╗",
    "  ██╔══██╗██╔══██╗██╔════╝██║  ██║██║██║   ██║██╔════╝",
    "  ███████║██████╔╝██║     ███████║██║██║   ██║█████╗  ",
    "  ██╔══██║██╔══██╗██║     ██╔══██║██║╚██╗ ██╔╝██╔══╝  ",
    "  ██║  ██║██║  ██║╚██████╗██║  ██║██║ ╚████╔╝ ███████╗",
    "  ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝  ╚══════╝",
]
_LOGO_COLORS = [
    "magenta","magenta","bright_magenta","bright_magenta","magenta","magenta",
    "bright_black",
    "magenta","magenta","bright_magenta","bright_magenta","magenta","magenta","magenta",
]

def print_logo() -> None:
    console.print()
    for line, color in zip(_LOGO, _LOGO_COLORS):
        console.print(f"[{color}]{line}[/{color}]")
    console.print()

def print_tips() -> None:
    tips = Text()
    tips.append("Tips for getting started:\n", style="bold magenta")
    items = [
        ("arc save \"name\"",           "Save a new prompt — opens your editor."),
        ("arc use \"django-debug\"",    "Copy a prompt to clipboard, ready to paste."),
        ("arc search refactor cli",    "Search prompts by name, tag, or code."),
        ("arc list",                   "Browse all saved prompts in a table."),
        ("arc log \"django-debug\"",    "See version history for a prompt."),
        ("arc push",                   "Back up your archive to GitHub."),
        ("arc --help",                 "Full list of commands and options."),
    ]
    for i, (cmd, desc) in enumerate(items, 1):
        tips.append(f"  {i}. ", style="dim")
        tips.append(cmd, style="bold cyan")
        tips.append(f"  -  {desc}\n", style="dim")
    console.print(Panel(tips, border_style="magenta", padding=(0, 2)))

def print_status_bar(version: str = "2.0.0") -> None:
    try:
        hostname = socket.gethostname()
    except Exception:
        hostname = "localhost"
    bar = Text()
    bar.append("  ~/.prompt_archive", style="dim")
    bar.append("  |  ", style="bright_black")
    bar.append(hostname, style="dim")
    bar.append("  |  ", style="bright_black")
    bar.append(platform.system(), style="dim")
    bar.append("  |  ", style="bright_black")
    bar.append(f"prompt-archive v{version}", style="magenta")
    bar.append(f"  |  {datetime.now().strftime('%H:%M')}", style="dim")
    console.print(bar)
    console.print()

def print_command_header(title: str, subtitle: str = "") -> None:
    content = Text()
    content.append("  > ", style="magenta bold")
    content.append(title, style="bold white")
    if subtitle:
        content.append(f"\n    {subtitle}", style="dim")
    console.print(Panel(content, border_style="magenta", padding=(0, 1)))
    console.print()

def step_ok(label: str, detail: str = "") -> None:
    console.print(f"  [bright_green]✓[/bright_green]  {label}" + (f"  [dim]{detail}[/dim]" if detail else ""))

def step_warn(label: str, detail: str = "") -> None:
    console.print(f"  [yellow]⚠[/yellow]  {label}" + (f"  [dim]{detail}[/dim]" if detail else ""))

def step_error(label: str, detail: str = "") -> None:
    console.print(f"  [bold red]✗[/bold red]  {label}" + (f"  [dim]{detail}[/dim]" if detail else ""))

def step_info(label: str, detail: str = "") -> None:
    console.print(f"  [cyan]→[/cyan]  {label}" + (f"  [dim]{detail}[/dim]" if detail else ""))

def divider(label: str = "") -> None:
    if label:
        console.rule(f"[dim]{label}[/dim]", style="bright_black")
    else:
        console.rule(style="bright_black")
    console.print()

def make_prompt_list_table(prompts: list) -> Table:
    """Table for vault list output."""
    table = Table(
        title=Text("Your Prompts", style="bold magenta"),
        show_header=True,
        header_style="bold cyan",
        border_style="bright_black",
        padding=(0, 2),
    )
    table.add_column("Name", style="white", no_wrap=True)
    table.add_column("Tags", style="dim")
    table.add_column("Uses", justify="right", style="bright_green")
    table.add_column("Version", justify="right", style="dim")
    table.add_column("Updated", style="dim")
    for p in prompts:
        table.add_row(
            p.get("name", ""),
            ", ".join(p.get("tags", [])),
            str(p.get("uses", 0)),
            str(p.get("version", 1)),
            p.get("updated", "")[:10],
        )
    return table

def make_log_table(entries: list) -> Table:
    """Version history table for vault log."""
    table = Table(
        title=Text("Version History", style="bold magenta"),
        show_header=True,
        header_style="bold cyan",
        border_style="bright_black",
        padding=(0, 2),
    )
    table.add_column("Version", justify="right", style="bright_green")
    table.add_column("Commit", style="dim")
    table.add_column("Message", style="white")
    table.add_column("Date", style="dim")
    for e in entries:
        table.add_row(
            str(e.get("version", "")),
            e.get("hash", "")[:7],
            e.get("message", ""),
            e.get("date", "")[:16],
        )
    return table

def print_prompt_preview(name: str, content: str, meta: dict) -> None:
    """Render a single prompt in a styled panel."""
    import html
    from rich.markup import escape
    
    header = Text()
    header.append(name, style="bold white")
    header.append(f"  v{meta.get('version', 1)}", style="dim")
    if meta.get("tags"):
        header.append(f"  [{', '.join(meta['tags'])}]", style="magenta")
    
    # Process content: unescape HTML and escape Rich tags
    clean_content = html.unescape(content)
    preview_text = clean_content[:600] + ("\n[dim]…[/dim]" if len(clean_content) > 600 else "")
    
    console.print(Panel(
        Text.from_markup(f"[dim]{header}[/dim]\n\n{escape(preview_text)}"),
        border_style="magenta",
        padding=(1, 2),
    ))
