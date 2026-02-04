# Prompt: Code Review

Read for context before reviewing:
1. `.context/CONVENTIONS.md` - coding standards
2. `.context/ARCHITECTURE.md` - system design

## Instructions

Review the following code against our project standards.

```[language]
[paste code here]
```

Check for:
1. Follows naming conventions from CONVENTIONS.md?
2. Has appropriate type annotations?
3. Error handling follows our patterns?
4. Security issues (injection, data exposure, etc.)?
5. Performance concerns?
6. Test coverage adequate?
7. Consistent with ARCHITECTURE.md patterns?

Provide:
- Issues found (with severity: critical/warning/nit)
- Suggested fixes
- Any positive observations
