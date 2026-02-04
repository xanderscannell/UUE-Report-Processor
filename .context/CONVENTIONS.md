# Project Conventions

## Language and Runtime

- **Language**: [Python/TypeScript/etc]
- **Version**: [e.g., Python 3.11+, Node 20+]
- **Package manager**: [pip/npm/pnpm/etc]

## Code Style

- **Formatter**: [Black/Prettier/etc]
- **Linter**: [Ruff/ESLint/etc]
- **Type checker**: [mypy/TypeScript strict/etc]

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Classes | PascalCase | `DataProcessor` |
| Functions | [snake_case/camelCase] | `process_data` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRIES` |
| Private members | _leading_underscore | `_internal_cache` |
| Files | [snake_case/kebab-case] | `data_processor.py` |

## File Organization

```
src/
  [module_name]/
    __init__.py       # Public exports
    core.py           # Main logic
    types.py          # Type definitions
    utils.py          # Module-specific helpers
tests/
  test_[module_name].py
```

## Error Handling

<!-- Describe your project's error handling pattern -->
```
[Example code showing the expected error handling pattern]
```

## Testing

- **Framework**: [pytest/jest/etc]
- **Coverage target**: [X]%
- **Test naming**: `test_[function]_[scenario]_[expected_result]`
- **Run tests**: `[command to run tests]`

## Git Conventions

- **Commit format**: `<type>(<scope>): <description>`
- **Types**: feat, fix, docs, test, refactor, perf, chore
- **Branch naming**: `feature/description`, `fix/description`

## Import Order

<!-- Describe your expected import ordering -->
1. Standard library
2. Third-party packages
3. Local modules
