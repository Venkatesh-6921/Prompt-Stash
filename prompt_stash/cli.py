"""
Prompt Stash CLI — Gemini CLI-style terminal experience.
"""
from __future__ import annotations

import click
from prompt_stash import __version__
from prompt_stash.utils.display import (
    console,
    print_logo,
    print_tips,
    print_status_bar,
    print_command_header,
    step_ok,
    step_warn,
    step_error,
    step_info,
    divider,
    make_prompt_list_table,
    make_log_table,
    print_prompt_preview,
)


def _get_vault():
    from prompt_stash.config import VaultConfig
    from prompt_stash.vault import PromptVault
    config = VaultConfig.load()
    return PromptVault(config), config


# ── Root group ────────────────────────────────────────────────────────────────

@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="Prompt Stash")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """\b
    Prompt Stash — Git-backed, searchable prompt library in your terminal.

    \b
    Commands:
      stash save       Save a new prompt
      stash use        Copy a prompt to clipboard
      stash search     Search prompts by name, tag, or content
      stash list       Browse all prompts
      stash log        Version history for a prompt
      stash push       Back up archive to GitHub
    """
    if ctx.invoked_subcommand is None:
        print_logo()
        print_tips()
        print_status_bar(version=__version__)


# ── save ──────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("name")
@click.option("--tags", "-t", default="", help="Comma-separated tags")
@click.option("--model", "-m", default="claude", help="Target AI model")
@click.option("--description", "-d", default="", help="Short description")
def save(name: str, tags: str, model: str, description: str) -> None:
    """Save a new prompt (opens your editor)."""
    vault, config = _get_vault()
    print_command_header("stash save", f"Creating prompt: {name}")
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    content = click.edit("", extension=".md")
    if not content or not content.strip():
        step_warn("No content entered — prompt not saved.")
        return

    from prompt_stash.vault import PromptVault
    result = vault.save(name=name, content=content.strip(), tags=tag_list,
                        model=model, description=description)
    console.print()
    step_ok(f"Saved  [bold]{name}[/bold]", f"v{result.get('version', 1)}")
    step_info("Run  stash use " + name + "  to copy to clipboard.")
    console.print()


# ── use ───────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("name")
@click.option("--print", "print_only", is_flag=True, default=False,
              help="Print to stdout instead of copying")
def use(name: str, print_only: bool) -> None:
    """Copy a prompt to clipboard — ready to paste into any AI."""
    vault, _ = _get_vault()
    print_command_header("stash use", f"Fetching: {name}")

    prompt = vault.get(name)
    if not prompt:
        step_error(f"Prompt '{name}' not found.", "Run  stash list  to see all prompts.")
        return

    if print_only:
        console.print(prompt["content"])
    else:
        from prompt_stash.utils.clipboard import copy_to_clipboard
        copy_to_clipboard(prompt["content"])
        step_ok(f"Copied  [bold]{name}[/bold]  to clipboard!")

    print_prompt_preview(name, prompt["content"], prompt)
    console.print()


# ── search ────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("query", nargs=-1)
@click.option("--tag", "-t", default=None, help="Filter by tag")
def search(query: tuple, tag: str | None) -> None:
    """Search prompts by name, tag, or content."""
    vault, _ = _get_vault()
    search_str = " ".join(query)
    print_command_header("stash search", f"Query: {search_str}" + (f"  tag: {tag}" if tag else ""))

    results = vault.search(query=search_str, tag=tag)
    if not results:
        step_warn(f"No prompts found for '{search_str}'.")
        return

    console.print(make_prompt_list_table(results))
    console.print()
    console.print(f"  [dim]{len(results)} result(s)  —  run[/dim]  [cyan]stash use <name>[/cyan]  [dim]to copy one.[/dim]")
    console.print()


# ── list ──────────────────────────────────────────────────────────────────────

@cli.command("list")
@click.option("--tag", "-t", default=None, help="Filter by tag")
@click.option("--model", "-m", default=None, help="Filter by model")
def list_prompts(tag: str | None, model: str | None) -> None:
    """Browse all saved prompts."""
    vault, _ = _get_vault()
    print_command_header("stash list", "All prompts" + (f"  tag: {tag}" if tag else ""))

    prompts = vault.list(tag=tag, model=model)
    if not prompts:
        step_warn("No prompts saved yet.", "Run  stash save \"name\"  to create your first.")
        return

    console.print(make_prompt_list_table(prompts))
    console.print()
    console.print(f"  [dim]{len(prompts)} prompt(s)[/dim]")
    console.print()


# ── log ───────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("name")
def log(name: str) -> None:
    """Show version history for a prompt."""
    vault, _ = _get_vault()
    print_command_header("stash log", f"Version history: {name}")

    from prompt_stash.versioning import PromptVersioning
    v = PromptVersioning(vault.config)
    entries = v.log(name)
    if not entries:
        step_warn(f"No history found for '{name}'.")
        return
    console.print(make_log_table(entries))
    console.print()


# ── diff ──────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("name")
@click.option("--from-version", "v_from", default=None, help="From version (default: previous)")
@click.option("--to-version", "v_to", default=None, help="To version (default: current)")
def diff(name: str, v_from: str | None, v_to: str | None) -> None:
    """Show diff between two versions of a prompt."""
    vault, _ = _get_vault()
    label = f"v{v_from} → v{v_to}" if v_from and v_to else "previous → current"
    print_command_header("stash diff", f"{name}  ·  {label}")
    from prompt_stash.versioning import PromptVersioning
    v = PromptVersioning(vault.config)
    v.diff(name, v_from, v_to)
    console.print()


# ── rollback ──────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("name")
@click.argument("version", type=int)
def rollback(name: str, version: int) -> None:
    """Roll back a prompt to a previous version."""
    vault, _ = _get_vault()
    print_command_header("stash rollback", f"{name}  →  v{version}")
    if not click.confirm(f"  Roll back '{name}' to v{version}?"):
        step_warn("Cancelled.")
        return
    from prompt_stash.versioning import PromptVersioning
    v = PromptVersioning(vault.config)
    v.rollback(name, version)
    step_ok(f"Rolled back  [bold]{name}[/bold]  to v{version}.")
    console.print()


# ── push / pull ───────────────────────────────────────────────────────────────

@cli.command()
def push() -> None:
    """Push vault to GitHub."""
    vault, config = _get_vault()
    print_command_header("stash push", "Syncing to GitHub...")
    
    if not config.github_repo:
        step_warn("No GitHub repo configured.")
        repo_url = click.prompt("  ?  Enter GitHub repository URL (e.g. https://github.com/user/prompts.git)")
        if repo_url:
            config.set_github_repo(repo_url)
            step_ok("GitHub repo saved to config.")
        else:
            step_error("GitHub repo is required for push.")
            return

    from prompt_stash.sync import VaultSync
    success = VaultSync(config).push()
    if success:
        step_ok("Pushed!", config.github_repo)
    else:
        if click.confirm("\n Would you like to re-enter your GitHub repository URL?"):
            repo_url = click.prompt("  ?  Enter GitHub repository URL")
            if repo_url:
                config.set_github_repo(repo_url)
                step_ok("New GitHub repo saved. Run 'stash push' again to sync.")
    console.print()


@cli.command()
@click.argument("source", required=False)
def pull(source: str | None) -> None:
    """Pull vault from GitHub."""
    vault, config = _get_vault()
    
    if not source and not config.github_repo:
        print_command_header("stash pull", "Setup Remote")
        step_warn("No GitHub repo configured.")
        repo_url = click.prompt("  ?  Enter GitHub repository URL to pull from")
        if repo_url:
            config.set_github_repo(repo_url)
            step_ok("GitHub repo saved to config.")
            source = repo_url
        else:
            step_error("GitHub repo URL is required to pull.")
            return

    print_command_header("stash pull", source or config.github_repo or "GitHub")
    from prompt_stash.sync import VaultSync
    success = VaultSync(config).pull(source)
    if success:
        step_ok("Pulled and merged.")
    else:
        if click.confirm("\n Would you like to re-enter your GitHub repository URL?"):
            repo_url = click.prompt("  ?  Enter GitHub repository URL")
            if repo_url:
                config.set_github_repo(repo_url)
                step_ok("New GitHub repo saved. Run 'stash pull' again to sync.")
    console.print()


# ── tag ───────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("name")
@click.argument("tags", nargs=-1)
def tag(name: str, tags: tuple) -> None:
    """Add tags to a prompt."""
    vault, _ = _get_vault()
    print_command_header("stash tag", f"{name}  +  {', '.join(tags)}")
    vault.add_tags(name, list(tags))
    step_ok(f"Tags added to  [bold]{name}[/bold]:", ", ".join(tags))
    console.print()


# ── delete ────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("name")
@click.option("--yes", "-y", is_flag=True, default=False, help="Skip confirmation")
def delete(name: str, yes: bool) -> None:
    """Delete a prompt from the vault."""
    vault, _ = _get_vault()
    print_command_header("stash delete", name)
    if not yes and not click.confirm(f"  Delete '{name}'? This cannot be undone."):
        step_warn("Cancelled.")
        return
    vault.delete(name)
    step_ok(f"Deleted  [bold]{name}[/bold].")
    console.print()


# ── rename ────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("old_name")
@click.argument("new_name")
def rename(old_name: str, new_name: str) -> None:
    """Rename a prompt."""
    vault, _ = _get_vault()
    print_command_header("stash rename", f"{old_name}  →  {new_name}")
    vault.rename(old_name, new_name)
    step_ok(f"Renamed  [bold]{old_name}[/bold]  →  [bold]{new_name}[/bold].")
    console.print()


# ── export / import ───────────────────────────────────────────────────────────

@cli.command("export")
@click.argument("output", type=click.Path())
@click.option("--format", "fmt", default="json", type=click.Choice(["json", "md"]))
def export_prompts(output: str, fmt: str) -> None:
    """Export all prompts to a file."""
    vault, _ = _get_vault()
    print_command_header("stash export", f"Format: {fmt}  →  {output}")
    vault.export(output, fmt)
    step_ok(f"Exported to  [bold]{output}[/bold].")
    console.print()


@cli.command("import")
@click.argument("source", type=click.Path(exists=True))
def import_prompts(source: str) -> None:
    """Import prompts from a JSON or markdown file."""
    vault, _ = _get_vault()
    print_command_header("stash import", source)
    count = vault.import_from(source)
    step_ok(f"Imported  [bright_green]{count}[/bright_green]  prompts.")
    console.print()


# ── entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    cli()

if __name__ == "__main__":
    main()
