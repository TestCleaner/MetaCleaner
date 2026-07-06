#!/usr/bin/env bash
# Install MetaCleaner caller workflow across all repositories in a GitHub organization.
#
# Usage:
#   ./scripts/install-org-workflow.sh YOUR_ORG [MetaCleaner] [--dry-run]
#
# Requirements: gh CLI authenticated with repo admin access.
#
# Creates a branch and pull request in each repository (except MetaCleaner itself).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
TEMPLATE="${ROOT_DIR}/templates/caller-workflow.yml"

ORG="${1:-}"
METACLEANER="${2:-MetaCleaner}"
DRY_RUN=false
BRANCH="chore/add-metacleaner-workflow"

if [[ "${3:-}" == "--dry-run" ]] || [[ "${2:-}" == "--dry-run" ]]; then
  DRY_RUN=true
  if [[ "${2:-}" == "--dry-run" ]]; then
    METACLEANER="MetaCleaner"
  fi
fi

if [[ -z "$ORG" ]]; then
  echo "Usage: $0 YOUR_ORG [MetaCleaner] [--dry-run]" >&2
  exit 2
fi

if [[ ! -f "$TEMPLATE" ]]; then
  echo "Template not found: $TEMPLATE" >&2
  exit 2
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "Error: gh CLI is required. Install: https://cli.github.com/" >&2
  exit 2
fi

WORKFLOW_CONTENT="$(sed "s|@ORG@|${ORG}|g; s|@METACLEANER@|${METACLEANER}|g" "$TEMPLATE")"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

echo "Organization: ${ORG}"
echo "MetaCleaner repo: ${ORG}/${METACLEANER}"
echo "Dry run: ${DRY_RUN}"
echo ""

mapfile -t REPOS < <(gh repo list "$ORG" --limit 1000 --json name -q '.[].name')

for repo in "${REPOS[@]}"; do
  if [[ "$repo" == "$METACLEANER" ]]; then
    echo "Skip: ${repo} (MetaCleaner itself)"
    continue
  fi

  TARGET="${ORG}/${repo}"
  echo "→ ${TARGET}"

  if $DRY_RUN; then
    continue
  fi

  REPO_DIR="${WORK_DIR}/${repo}"
  rm -rf "$REPO_DIR"

  if ! gh repo clone "$TARGET" "$REPO_DIR" -- --depth 1 2>/dev/null; then
    echo "  Failed to clone, skipping."
    continue
  fi

  cd "$REPO_DIR"
  git checkout -b "$BRANCH" 2>/dev/null || git checkout "$BRANCH"

  mkdir -p .github/workflows
  printf '%s\n' "$WORKFLOW_CONTENT" > .github/workflows/optimize-media.yml

  git add .github/workflows/optimize-media.yml
  if git diff --cached --quiet; then
    echo "  Workflow already up to date, skipping."
    continue
  fi

  git commit -m "chore: add MetaCleaner media optimization workflow"

  if git push -u origin "$BRANCH" --force 2>/dev/null; then
    EXISTING_PR="$(gh pr list --head "$BRANCH" --json number -q '.[0].number' 2>/dev/null || true)"
    if [[ -n "$EXISTING_PR" ]]; then
      echo "  PR already exists: #${EXISTING_PR}"
    else
      gh pr create \
        --title "Add MetaCleaner media optimization workflow" \
        --body "Adds automatic media metadata cleanup and compression on pull requests via [@${ORG}/${METACLEANER}](https://github.com/${ORG}/${METACLEANER}). Developers do not need to install anything locally." \
        || echo "  Failed to create PR."
    fi
  else
    echo "  Failed to push branch."
  fi
done

echo ""
echo "Done."
