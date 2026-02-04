#!/usr/bin/env bash
set -euo pipefail

# Customize the CDS context framework with your project name.
# Replaces [PROJECT_NAME] and [DATE] placeholders in CLAUDE.md and .context/ files.
#
# Usage: ./scripts/customize.sh <project-name>
# Run from your project root.

PROJECT_NAME="${1:-}"

if [ -z "$PROJECT_NAME" ]; then
    echo "Usage: $0 <project-name>"
    echo ""
    echo "  Replaces [PROJECT_NAME] and [DATE] placeholders in CLAUDE.md"
    echo "  and all .context/*.md files."
    exit 1
fi

# Determine project root (one level up from scripts/)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

TODAY=$(date +%Y-%m-%d)

echo "Customizing context for: $PROJECT_NAME"

# Files to process (only those that contain [PROJECT_NAME] or [DATE])
FILES=(
    "$PROJECT_ROOT/CLAUDE.md"
    "$PROJECT_ROOT/.context/MASTER_PLAN.md"
    "$PROJECT_ROOT/.context/CURRENT_STATUS.md"
    "$PROJECT_ROOT/.context/ARCHITECTURE.md"
    "$PROJECT_ROOT/.context/SETUP.md"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        sed "s/\[PROJECT_NAME\]/$PROJECT_NAME/g; s/\[DATE\]/$TODAY/g" "$file" > "$file.tmp"
        mv "$file.tmp" "$file"
        echo "  Updated: $(basename "$file")"
    fi
done

echo ""
echo "Done! Placeholders replaced."
echo ""
echo "Next steps:"
echo "  1. Edit CLAUDE.md - fill in [ONE_SENTENCE_DESCRIPTION] and Current Focus"
echo "  2. Edit .context/MASTER_PLAN.md - define your implementation roadmap"
echo "  3. Edit .context/CONVENTIONS.md - document your coding standards"
echo "  4. Commit everything: git add CLAUDE.md .context/ && git commit -m 'Add context framework'"
