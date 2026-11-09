# Contributing to Polymock

## Claude Code plugin

Install uv 0.12.23 or newer and make sure `uv` is on Claude Code's `PATH`.
Run Claude Code from the project you want to seed.

```sh
claude plugin marketplace add nainkunal933/polymock
claude plugin install polymock@polymock-marketplace
```

To check local changes, run `claude plugin validate .` and
`claude --plugin-dir .` from the Polymock checkout. Confirm the server is
connected with `/mcp`. From a separate project, pass the absolute path to
the Polymock checkout to `--plugin-dir`.

Bump `.claude-plugin/plugin.json`'s version when shipping plugin updates.
For the official directory, submit the repository root as a **Plugin bundle**
through the [Claude developer portal](https://claude.ai/directory/manage).

## Automated native builds

The **Test builds** workflow checks all four native builds on PR updates. The
**Build executables** workflow runs on pushes to `main` and publishes releases
after all builds succeed. Both workflows upload an archive containing the
executable, the README, and the license:

| Artifact | Target |
| --- | --- |
| `polymock-linux-x86_64` | Linux x86_64, glibc 2.35 or newer (Ubuntu 22.04 baseline) |
| `polymock-windows-x86_64` | Windows x86_64 |
| `polymock-macos-arm64` | macOS 15 or newer, Apple Silicon |
| `polymock-macos-x86_64` | macOS 15 or newer, Intel |

Download an artifact from a successful workflow run and extract both the
GitHub artifact wrapper and the archive inside it. Windows uses ZIP; Linux
and macOS use tar.gz to retain executable permissions. These are portable
executables, not OS installer packages. Workflow artifacts expire after 30 days.

## Releases

Before merging a PR, apply a release label:

| Label | Version bump |
| --- | --- |
| `release:patch` | Bug fixes |
| `release:minor` | New features |
| `release:major` | Breaking changes |

Unlabeled PRs default to patch. When multiple unreleased PRs are included, the
largest bump wins. After all builds succeed on `main`, CI creates the Git tag and
release automatically. Download binaries from **GitHub Releases**.

The same archives are also published to **GitHub Packages** in GHCR, before the
GitHub Release is created. Install ORAS, then download a platform archive with:

```sh
oras pull ghcr.io/OWNER/REPOSITORY:v0.1.1-windows-x86_64
```

Replace `OWNER/REPOSITORY` with the lowercase repository path and use the desired
release version and target from the table above. Extract the downloaded archive
before running the executable. These are OCI artifacts, not Docker images.

After the first publication, set the GHCR package visibility to **Public**
in GitHub package settings to allow anonymous downloads.
