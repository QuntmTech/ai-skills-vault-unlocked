# Publishing checklist

- [ ] `python3 scripts/build_repository.py --check` passes.
- [ ] `git diff --check` passes.
- [ ] No `.env`, credential, key, cookie, or local-user-path files are present.
- [ ] `metadata/license-audit.json` has been reviewed.
- [ ] The maintainer has chosen a license for original repository material.
- [ ] Third-party items have explicit redistribution permission or compatible
      licenses.
- [ ] The GitHub repository is created with the intended visibility.
- [ ] Secret scanning and push protection are enabled where available.
- [ ] Branch protection and pull-request review rules are configured.
- [ ] The clone and single-skill installation instructions are tested.

