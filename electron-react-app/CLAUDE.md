# CLAUDE.md

This file provides guidance to Claude Code when working with this Electron-React application.

## Development Commands

```bash
# Install dependencies
npm install

# Build for production (RECOMMENDED for development)
npm run build

# Run built application for testing
npx electron ./release/app/dist/main/main.js

# Package for distribution (creates .app, .dmg, .zip)
npm run package

# Start development server (CURRENTLY NOT WORKING due to DLL issues)
# npm start

# Lint code
npm run lint

# Run tests
npm test
```

## Known Issues

### Webpack Configuration Issues (RESOLVED)
The webpack configurations had ESM/CommonJS compatibility issues that have been resolved.

**Status:**
- ✅ Production builds work: `npm run build` compiles successfully
- ✅ Packaging works: `npm run package` creates distributable files
- ✅ Built application runs correctly
- ❌ Development server still has DLL circular dependency issues

**Current Development Workflow:**
1. Make code changes
2. Run `npm run build` to compile
3. Test with `npx electron ./release/app/dist/main/main.js`

**Packaging Success:**
- Creates both ARM64 and x64 builds for macOS
- Generates DMG files for distribution
- Key fix: ESM module resolution in webpack configurations

## Troubleshooting

### If `npm run package` fails with postinstall errors:
1. Edit `release/app/package.json` and change postinstall script to `"echo 'Skipping rebuild during packaging'"`
2. Run `npm run package`
3. Restore original postinstall script: `"npm run rebuild && npm run link-modules"`

### If builds fail with module resolution errors:
- Ensure imports in `.erb/configs/` use proper extensions (.ts for TypeScript, .js for JavaScript)
- JSON imports must use `import pkg from './path.json' with { type: 'json' }`