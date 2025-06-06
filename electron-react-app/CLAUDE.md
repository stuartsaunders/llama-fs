# CLAUDE.md

This file provides guidance to Claude Code when working with this Electron-React
application.

## Development Commands

```bash
# Install dependencies
npm install

# Start development server (NOW WORKING)
npm start

# Build for production
npm run build

# Package for distribution (creates .app, .dmg, .zip)
npm run package

# Lint code
npm run lint

# Run tests
npm test
```

## Git Commit Rules

**CRITICAL: Never use HEREDOC for commit messages** - it causes ANSI color code
pollution.

See `../COMMIT_RULES.md` for complete guidelines.

## Known Issues (RESOLVED)

### ✅ Webpack Configuration Issues - FIXED

All webpack ESM/CommonJS compatibility issues have been resolved:

- ✅ Development server (`npm start`) works correctly
- ✅ Production builds (`npm run build`) work correctly
- ✅ Packaging (`npm run package`) works correctly
- ✅ TypeScript compilation errors resolved
- ✅ Module resolution conflicts fixed

## Troubleshooting

### If `npm run package` fails with postinstall errors:

1. Edit `release/app/package.json` and change postinstall script to
   `"echo 'Skipping rebuild during packaging'"`
2. Run `npm run package`
3. Restore original postinstall script:
   `"npm run rebuild && npm run link-modules"`

### If builds fail with module resolution errors:

- Ensure imports in `.erb/configs/` use proper extensions (.ts for TypeScript,
  .js for JavaScript)
- JSON imports must use `import pkg from './path.json' with { type: 'json' }`
