# Commit Message Rules

## CRITICAL: Avoid HEREDOC for Commit Messages

**NEVER use HEREDOC syntax for commit messages**. It causes ANSI color code pollution in git history.

### ❌ WRONG - Do NOT use:
```bash
git commit -m "$(cat <<'EOF'
commit message here
EOF
)"
```

### ✅ CORRECT - Always use simple string literals:
```bash
git commit -m "🔧 fix(component): brief description

- Detailed point 1
- Detailed point 2
- Detailed point 3

Explanation of why this change was needed.

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

## Commit Message Format

Use conventional commits with gitmoji:

```
<gitmoji> <type>(<scope>): <description>

<body>

<footer>
```

### Examples:
- `🔧 fix(webpack): resolve ESM compatibility issues`
- `✨ feat(ui): add clickable sidebar navigation`
- `🛡️ feat(privacy): implement opt-in analytics`
- `📝 docs: update API documentation`

## Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Tests
- `chore`: Maintenance

## Gitmoji Reference:
- 🔧 `:wrench:` - Configuration/build changes
- ✨ `:sparkles:` - New features
- 🛡️ `:shield:` - Security/privacy improvements
- 🐛 `:bug:` - Bug fixes
- 📝 `:memo:` - Documentation
- 🎨 `:art:` - Code style/structure
- ⚡ `:zap:` - Performance improvements
- 🚀 `:rocket:` - Deploy/release related

## Pre-commit Checklist:
1. ✅ Use simple string literals for commit messages
2. ✅ Include gitmoji and conventional commit format
3. ✅ Add Claude Code footer
4. ✅ Keep lines under 72 characters when possible
5. ✅ Test message with `git log --oneline` to verify clean output