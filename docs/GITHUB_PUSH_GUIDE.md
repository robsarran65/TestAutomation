# GitHub Publishing Guide

## Goal

Publish the project to GitHub so it can be reviewed, versioned, and deployed from a proper repository.

## Prerequisites

- Git installed on the machine
- A GitHub account
- A new remote repository created on GitHub
- Authentication configured for GitHub (SSH or personal access token)

## 1. Check Git availability

Run:

```bash
git --version
```

If Git is not installed, install it from the official Git website and reopen the terminal.

## 2. Initialize the repository

From the project root:

```bash
cd "C:\Users\Public\streamlit-automation-poc"
git init
```

## 3. Add files

```bash
git add .
```

## 4. Commit the project

```bash
git commit -m "Initial productionization pass for AI-powered test automation platform"
```

## 5. Create and connect the GitHub repository

Create a new repository on GitHub without initializing it with a README, since the project already has files.

Then connect it with:

```bash
git branch -M main
git remote add origin git@github.com:<your-user>/<your-repo-name>.git
```

If using HTTPS instead of SSH:

```bash
git remote add origin https://github.com/<your-user>/<your-repo-name>.git
```

## 6. Push the code

```bash
git push -u origin main
```

## 7. Configure branch protection

In GitHub, enable:

- main branch protection
- required pull request reviews
- status checks from CI
- no direct force push to main

## 8. Set repository settings

Recommended settings:

- description: AI-powered testing platform for web and API quality automation
- website: optional project landing page
- topics: ai, testing, automation, api, qa, selenium, streamlit
- add a license if desired

## 9. Enable GitHub Actions

The repository includes a simple CI workflow in [.github/workflows/ci.yml](.github/workflows/ci.yml). Once pushed to GitHub, the workflow will run automatically on pushes and pull requests.

## Notes

This workspace cannot complete the actual `git push` step because the machine currently reports that `git` is not installed or not available in the active terminal environment. Once Git is available, these commands are sufficient to publish the project.
