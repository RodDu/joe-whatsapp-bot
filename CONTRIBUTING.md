# Contributing to Joe WhatsApp Bot

First off, thanks for taking the time to contribute! 🎉

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates.

When creating a bug report, include:
- **OS and version** (Windows 11, Ubuntu 24.04, macOS 15, etc.)
- **Node.js version** (`node --version`)
- **Python version** (`python --version`)
- **Steps to reproduce** the issue
- **Expected behavior** vs. **actual behavior**
- **Relevant logs** from `bot.log` (remove any personal data first!)

### Suggesting Features

Feature requests are welcome! Open an issue with:
- A clear description of the feature
- Why it would be useful
- How you envision it working

### Pull Requests

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Test locally (start the bot, send messages, verify commands work)
5. Commit with a clear message: `git commit -m "Add: my new feature"`
6. Push: `git push origin feature/my-feature`
7. Open a Pull Request

### Adding New Tools

The tool system is designed to be extensible:

1. Create a new file in `tools/` (e.g., `tools/weather.py`)
2. Implement your async tool function
3. Add the tool declaration in `tools/registry.py`
4. Register the tool in `tools/executor.py`
5. Test it via the CLI: `python voice_router.py -t "test your tool"`

### Adding New AI Providers

To add a new AI provider (e.g., OpenAI, Anthropic):

1. Add the API key variable to `.env.example`
2. Add a new `_execute_<provider>_agent()` function in `voice_router.py`
3. Add a new agent `type` in `config.example.json`
4. Update the agent executor dispatcher

## Code Style

- **JavaScript**: Use `const`/`let`, async/await, clear variable names
- **Python**: Follow PEP 8, use async/await, type hints where helpful
- **Comments**: English, concise, explain *why* not *what*
- **Encoding**: Always use `encoding="utf-8"` on file/subprocess operations

## Commit Messages

Use clear, descriptive commit messages:
- `Add: new weather tool`
- `Fix: voice message conversion on Linux`
- `Docs: update README with new commands`
- `Refactor: simplify agent routing logic`

## Questions?

Open an issue with the `question` label — we're happy to help!
