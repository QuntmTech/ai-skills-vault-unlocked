# ChatGPT reference — Next Upgrade

Readable guidance, not a native skill installation. No live ChatGPT test is claimed. Supporting scripts and assets are not embedded in this document. Provider-specific commands may require adaptation; do not assume tools are available.

## Requirements to review

- Agent tools mentioned
- Plugin source — verify required plugin capabilities in Claude

[Preserved source and supporting files](../../../../%F0%9F%94%A7%20ADVANCED/skills/codex/plugins/vercel-plugin%20%E2%80%94%20next-upgrade%20%E2%80%94%20Copy%202/SKILL.md)

---

# Reference copy — next-upgrade

This is a reading/copy-paste aid, not an installed skill. It does not include supporting files or grant access to tools. Review the ZIP and audit report before using this workflow.

---
name: next-upgrade
description: Upgrade Next.js to the latest version following official migration guides
  and codemods
argument-hint: '[target-version]'
---

# Upgrade Next.js

Upgrade the current project to the latest Next.js version following official migration guides.

## Instructions

1. **Detect current version**: Read `package.json` to identify the current Next.js version and related dependencies (React, React DOM, etc.)

2. **Fetch the latest upgrade guide**: Use WebFetch to get the official upgrade documentation:
   - Codemods: https://nextjs.org/docs/app/guides/upgrading/codemods
   - Version-specific guides (adjust version as needed):
     - https://nextjs.org/docs/app/guides/upgrading/version-16 
     - https://nextjs.org/docs/app/guides/upgrading/version-15
     - https://nextjs.org/docs/app/guides/upgrading/version-14

3. **Determine upgrade path**: Based on current version, identify which migration steps apply. For major version jumps, upgrade incrementally (e.g., 13 → 14 → 15).

4. **Run codemods first**: Next.js provides codemods to automate breaking changes:
   ```bash
   npx @next/codemod@latest <transform> <path>
   ```
   Common transforms:
   - `next-async-request-api` - Updates async Request APIs (v15)
   - `next-request-geo-ip` - Migrates geo/ip properties (v15)
   - `next-dynamic-access-named-export` - Transforms dynamic imports (v15)

5. **Update dependencies**: Upgrade Next.js and peer dependencies together:
   ```bash
   npm install next@latest react@latest react-dom@latest
   ```

6. **Review breaking changes**: Check the upgrade guide for manual changes needed:
   - API changes (e.g., async params in v15)
   - Configuration changes in `next.config.js`
   - Deprecated features being removed

7. **Update TypeScript types** (if applicable):
   ```bash
   npm install @types/react@latest @types/react-dom@latest
   ```

8. **Test the upgrade**:
   - Run `npm run build` to check for build errors
   - Run `npm run dev` and test key functionality
