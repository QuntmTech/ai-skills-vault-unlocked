# ChatGPT reference — Vercel Agent

Readable guidance, not a native skill installation. No live ChatGPT test is claimed. Supporting scripts and assets are not embedded in this document. Provider-specific commands may require adaptation; do not assume tools are available.

## Requirements to review

- Claude upload description will be shortened; full text retained
- Plugin source — verify required plugin capabilities in Claude

[Preserved source and supporting files](../../../../%F0%9F%94%A7%20ADVANCED/skills/codex/plugins/vercel-plugin%20%E2%80%94%20vercel-agent/SKILL.md)

---

# Reference copy — vercel-agent

This is a reading/copy-paste aid, not an installed skill. It does not include supporting files or grant access to tools. Review the ZIP and audit report before using this workflow.

---
name: vercel-agent
description: Vercel Agent guidance — AI-powered code review, incident investigation,
  and SDK installation. Automates PR analysis and anomaly debugging. Use when configuring
  or understanding Vercel's AI...
metadata:
  priority: 4
  docs:
  - https://vercel.com/docs
  - https://sdk.vercel.ai/docs
  sitemap: https://vercel.com/sitemap/docs.xml
  pathPatterns:
  - .github/workflows/vercel*.yml
  - .github/workflows/vercel*.yaml
  - .github/workflows/deploy*.yml
  - .github/workflows/deploy*.yaml
  - .github/workflows/preview*.yml
  - .github/workflows/preview*.yaml
  bashPatterns:
  - \bvercel\s+agent\b
retrieval:
  aliases:
  - ai code review
  - incident debugger
  - vercel ai tools
  - pr analyzer
  intents:
  - set up vercel agent
  - automate code review
  - investigate incident
  - configure ai tools
  entities:
  - Vercel Agent
  - code review
  - incident investigation
  - SDK
chainTo:
- pattern: uses:\s*vercel/|vercel-action|VERCEL_TOKEN.*github
  targetSkill: deployments-cicd
  message: GitHub Actions with Vercel detected — loading CI/CD guidance for deployment
    workflows, preview URLs, and production promotions.
---
## Full original description

Vercel Agent guidance — AI-powered code review, incident investigation, and SDK installation. Automates PR analysis and anomaly debugging. Use when configuring or understanding Vercel's AI development tools.


# Vercel Agent

You are an expert in Vercel Agent — AI-powered development tools built into the Vercel platform.

## What It Is

Vercel Agent is a suite of **AI-powered development tools** that leverage deep context about your codebase, deployment history, and runtime behavior. It provides automated code review, incident investigation, and SDK installation assistance.

## Capabilities

### Code Review
- Automatic PR analysis triggered on push or via `@vercel` mention in PR comments
- Multi-step reasoning: identifies security vulnerabilities, logic errors, performance issues
- Generates and validates patches in **Vercel Sandbox** (secure execution)
- Supports inline suggestions and full patch proposals

### Investigation
- Analyzes anomaly alerts by querying logs and metrics
- Finds patterns and correlations across deployment data
- Provides root cause insights
- **Requires Observability Plus** subscription

### Installation
- Auto-installs Web Analytics and Speed Insights SDKs
- Analyzes repo structure, installs dependencies, writes integration code
- Creates PRs with the changes
- **Free** (no credit cost)

## Pricing

- $0.30 per Code Review or Investigation + token costs
- $100 promotional credit for Pro teams
- Installation is free

## Configuration

Vercel Agent is configured at `https://vercel.com/{team}/{project}/settings` → **AI** section. No npm package required — it is a platform-level service.

## When to Use

- Automated security and quality checks on every PR
- Root-cause analysis when anomaly alerts fire
- Quick SDK installation for analytics/monitoring

## References

- 📖 docs: https://vercel.com/docs/agent
