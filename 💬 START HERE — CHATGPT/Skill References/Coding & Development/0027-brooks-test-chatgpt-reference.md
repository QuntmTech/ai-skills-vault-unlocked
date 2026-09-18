# ChatGPT reference — Brooks Test

Readable guidance, not a native skill installation. No live ChatGPT test is claimed. Supporting scripts and assets are not embedded in this document. Provider-specific commands may require adaptation; do not assume tools are available.

## Requirements to review

- Claude upload description will be shortened; full text retained
- Agent tools mentioned

[Preserved source and supporting files](../../../%F0%9F%94%A7%20ADVANCED/skills/cc-switch/managed/brooks-test/SKILL.md)

---

# Reference copy — brooks-test

This is a reading/copy-paste aid, not an installed skill. It does not include supporting files or grant access to tools. Review the ZIP and audit report before using this workflow.

---
name: brooks-test
description: Test quality review drawing on twelve classic engineering books — with
  primary focus on xUnit Test Patterns, The Art of Unit Testing, How Google Tests
  Software, and Working Effectively with Legacy...
---
## Full original description

Test quality review drawing on twelve classic engineering books — with primary focus on xUnit Test Patterns, The Art of Unit Testing, How Google Tests Software, and Working Effectively with Legacy Code — that diagnoses structural problems in an existing test suite: brittleness, mock abuse, coverage illusions, slow execution, poor readability. Triggers when: user asks about test quality, shares test files for review, or expresses frustration: "tests keep breaking whenever I change anything", "our tests take forever", "I can't understand what this test is doing", "tests pass but bugs still reach production", "we have too many mocks". Do NOT trigger for: writing new tests from scratch (use the regular test-writing workflow) or testing framework/syntax questions — this skill reviews an existing suite for structural quality problems, not individual test authoring.


# Brooks-Lint — Test Quality Review

## Setup

1. Read `../_shared/common.md` for the Iron Law, Project Config, Report Template, and Health Score rules
2. Read `../_shared/source-coverage.md` for book-level coverage, exceptions, and tradeoffs
3. Read `../_shared/test-decay-risks.md` for test-space symptom definitions and source attributions
4. Read `test-guide.md` in this directory for the test quality review framework

## Process

**If the user has not shared test files or pointed to a test directory:** apply Auto
Scope Detection from `../_shared/common.md` to determine the review scope before proceeding.

1. Build the test suite map (guide's "Before You Start" section)
2. Scan for each test decay risk in the order specified (Steps 1–4 of the guide)
3. Apply the Iron Law and output using the Report Template (Step 5 of the guide)

**Mode line in report:** `Test Quality Review`
