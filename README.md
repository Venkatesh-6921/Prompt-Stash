# PromptVault CLI

**PromptVault CLI** is a terminal-based, version-controlled prompt manager designed for AI power users. It allows you to save, version-control, search, and quickly copy prompt templates right from your terminal.

![PromptVault CLI Demo](https://raw.githubusercontent.com/Venkatesh-6921/PromptVault-cli/main/docs/demo.png) *(Add a screenshot here later)*

## Features

- **Store & Retrieve**: Save prompts as Markdown with YAML frontmatter. Retrieve them instantly to your clipboard using fuzzy search.
- **Version Control**: Every save, rename, or deletion automatically triggers a Git commit behind the scenes using `GitPython`.
- **Searchable**: Search for prompts by name, content, or tag via a SQLite Full-Text Search index.
- **GitHub Sync**: Instantly push and pull your vaults to a remote GitHub repository.
- **Beautiful UI**: Enjoy a rich, interactive terminal experience powered by `click` and `rich`.

---

## Installation 

The best way to install PromptVault and guarantee that the `vault` command is available in your terminal is by using [`pipx`](https://pipx.pypa.io/stable/) (which installs Python CLI tools in isolated environments).

### Option 1: Using pipx (Recommended)
```bash
# If you don't have pipx, install it first: pip install pipx
pipx install promptvault-cli
```

### Option 2: Using pip
```bash
pip install promptvault-cli
```
> **Note**: If you use `pip`, the `vault` command might show up as `"command not found"` if your Python `Scripts` directory is not in your system's `PATH`. If that happens, either add the Scripts folder to your PATH, or use `pipx`.

---

## Getting Started

Save your first prompt. This will automatically set up your vault in `~/.promptvault/` and open your default system editor.

```bash
vault save "code-reviewer"
```

### Copying Prompts

When you need to use a prompt, just copy it to your clipboard:

```bash
vault use "code-reviewer"
```

If you don't remember the exact name, you can search for it:

```bash
vault search refactor
```

### All Commands

```bash
vault save [NAME]       # Save or edit a prompt
vault use [NAME]        # Copy content to clipboard
vault list              # Browse all saved prompts
vault search [QUERY]    # Search by name, tags, or content
vault log [NAME]        # See the Git version history for a prompt
vault diff [NAME]       # Compare versions
vault rollback [NAME]   # Revert a prompt to an older version
vault push              # Back up your vault to GitHub
vault pull              # Pull your vault from GitHub
```

## Storage & Configuration

- **Data**: All your prompts are saved in `~/.promptvault/prompts/` as standard Markdown files.
- **Metadata**: A fast SQLite search index is maintained at `~/.promptvault/vault.db`.
- **Config**: Edit `~/.promptvault/config.toml` to change your default GitHub repository or editor settings.

## License

This project is licensed under the MIT License.
