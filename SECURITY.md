# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | ✅ Yes    |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT** open a public issue
2. Send an email to the repository owner (see profile)
3. Include a clear description of the vulnerability
4. Include steps to reproduce if possible
5. We will respond within 48 hours

## Security Considerations

This bot runs locally on your machine. Keep in mind:

- **API Keys**: Never commit your `.env` file. It's in `.gitignore` by default.
- **WhatsApp Session**: The `.wwebjs_auth/` folder contains your WhatsApp session. Never share it.
- **run_command tool**: The bot can execute system commands. A blocklist prevents dangerous commands, but use caution when extending it.
- **File access**: The `file_read` tool has path restrictions. Be careful when modifying these.
- **Network exposure**: The `/link` command creates a temporary public tunnel. Only use it when needed and close it after.

## Best Practices

- Keep your dependencies updated: `npm update` and `pip install --upgrade -r requirements.txt`
- Use a dedicated WhatsApp number for the bot if possible
- Review `config.json` to ensure monitoring services don't expose sensitive endpoints
- Run the bot with minimal system privileges
