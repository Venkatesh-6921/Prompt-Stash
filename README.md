# Prompt Archive

**Prompt Archive** is a terminal-based, version-controlled prompt manager designed for AI power users. Save, version-control, search, and quickly copy prompt templates right from your terminal.

![Prompt Archive Demo](https://raw.githubusercontent.com/Venkatesh-6921/Prompt-Archive/main/docs/demo.png) *(Add a screenshot here later)*

## Features

- **Store & Retrieve**: Save prompts as Markdown with YAML frontmatter. Retrieve them instantly to your clipboard using fuzzy search.
- **Version Control**: Every save, rename, or deletion automatically triggers a Git commit behind the scenes using `GitPython`.
- **Searchable**: Search for prompts by name, content, or tag via a SQLite Full-Text Search index.
- **GitHub Sync**: Instantly push and pull your vaults to a remote GitHub repository.
- **Beautiful UI**: Enjoy a rich, interactive terminal experience powered by `click` and `rich`.

---

## Installation 

The best way to install Prompt Archive and guarantee that the `arc` command is available in your terminal is by using [`pipx`](https://pipx.pypa.io/stable/).

### Option 1: Using pipx (Recommended)
```bash
# If you don't have pipx, install it first: pip install pipx
pipx install prompt-archive
```

### Option 2: Using pip
```bash
pip install prompt-archive
```
> **Note**: If you use `pip`, the `arc` command might show up as `"command not found"` if your Python `Scripts` directory is not in your system's `PATH`. If that happens, either add the Scripts folder to your PATH, or use `pipx`.

---

## Getting Started

Save your first prompt. This will automatically set up your archive in `~/.promptvault/` and open your default system editor.

```bash
arc save "code-reviewer"
```

### Copying Prompts

When you need to use a prompt, just copy it to your clipboard:

```bash
arc use "code-reviewer"
```

If you don't remember the exact name, you can search for it:

```bash
arc search refactor
```

### All Commands

```bash
arc save [NAME]       # Save or edit a prompt
arc use [NAME]        # Copy content to clipboard
arc list              # Browse all saved prompts
arc search [QUERY]    # Search by name, tags, or content
arc log [NAME]        # See the Git version history for a prompt
arc diff [NAME]       # Compare versions
arc rollback [NAME]   # Revert a prompt to an older version
arc push              # Back up your archive to GitHub
arc pull              # Pull your archive from GitHub
```

## Storage & Configuration

- **Data**: All your prompts are saved in `~/.promptvault/prompts/` as standard Markdown files.
- **Metadata**: A fast SQLite search index is maintained at `~/.promptvault/vault.db`.
- **Config**: Edit `~/.promptvault/config.toml` to change your default GitHub repository or editor settings.

## License

This project is licensed under the MIT License.
