# Everything Claude Code - Universal Agent Rules

# File: .agentrules

# This file provides unified rules for all AI coding agents (Claude Code, Codex, OpenCode, etc.)

## Core Principles (Universal)

- Agent-First: Delegate to specialized agents for domain tasks
- Test-Driven: Write tests before implementation, 80%+ coverage required
- Security-First: Never compromise on security; validate all inputs
- Immutability: Always create new objects, never mutate existing ones
- Plan Before Execute: Plan complex features before writing code

## Development Workflow (Universal)

1. Plan First - Use planner agent to create implementation plan
2. TDD Approach - Use tdd-guide agent, write tests first (RED → GREEN → REFACTOR)
3. Code Review - Use code-reviewer agent immediately after writing code
4. Commit & Push - Follow conventional commits format

## Coding Standards (Universal)

- Immutability: ALWAYS create new objects, NEVER mutate existing ones
- File Organization: Many small files (200-400 lines) over few large files
- Error Handling: Handle errors at every level with user-friendly messages
- Input Validation: Validate all user input at system boundaries
- No Hardcoded Values: Use constants or configuration

## Security Requirements (Universal)

- No hardcoded secrets (API keys, passwords, tokens)
- All user inputs validated and sanitized
- SQL injection prevention (parameterized queries)
- XSS prevention (sanitized HTML)
- CSRF protection enabled
- Authentication/authorization verified
- Rate limiting on all endpoints
- Error messages don't leak sensitive data

## Testing Requirements (Universal)

- Minimum coverage: 80%
- Unit tests: Individual functions, utilities, components
- Integration tests: API endpoints, database operations
- E2E tests: Critical user flows
- TDD workflow: RED (test fails) → GREEN (test passes) → REFACTOR

## Git Workflow (Universal)

- Conventional commits: `<type>: <description>`
- Types: feat, fix, refactor, docs, test, chore, perf, ci
- PR workflow: Analyze full commit history → draft comprehensive summary

## Architecture Patterns (Universal)

- API response format: Consistent envelope with success/data/error/pagination
- Repository pattern: Encapsulate data access behind standard interface
- Skeleton projects: Search for battle-tested templates, evaluate with agents

## Performance (Universal)

- Avoid last 20% of context window for large refactoring
- Use build-error-resolver agent for build failures
- Monitor and optimize resource usage

## Available Agents (Universal)

- planner: Implementation planning for complex features
- architect: System design and scalability decisions
- tdd-guide: Test-driven development workflow
- code-reviewer: Code quality and maintainability review
- security-reviewer: Vulnerability detection
- build-error-resolver: Fix build/type errors
- e2e-runner: End-to-end Playwright testing
- refactor-cleaner: Dead code cleanup
- doc-updater: Documentation updates
- cpp-reviewer: C++ code review
- cpp-build-resolver: C++ build errors
- docs-lookup: Documentation lookup via Context7
- go-reviewer: Go code review
- go-build-resolver: Go build errors
- kotlin-reviewer: Kotlin code review
- kotlin-build-resolver: Kotlin/Gradle build errors
- database-reviewer: PostgreSQL/Supabase optimization
- python-reviewer: Python code review
- java-reviewer: Java and Spring Boot code review
- java-build-resolver: Java/Maven/Gradle build errors
- loop-operator: Autonomous loop execution
- harness-optimizer: Harness config tuning
- rust-reviewer: Rust code review
- rust-build-resolver: Rust build errors
- pytorch-build-resolver: PyTorch runtime/CUDA/training errors
- typescript-reviewer: TypeScript/JavaScript review

## Agent Orchestration (Universal)

Use agents proactively without user prompt:

- Complex feature requests → planner
- Code just written/modified → code-reviewer
- Bug fix or new feature → tdd-guide
- Architectural decision → architect
- Security-sensitive code → security-reviewer
- Autonomous loops / loop monitoring → loop-operator
- Harness config reliability and cost → harness-optimizer

Use parallel execution for independent operations — launch multiple agents simultaneously.

## Skills Integration (Universal)

Use these skills when applicable:

- api-design: REST API design patterns
- backend-patterns: API design, database, caching for Node.js/Express/Next.js
- frontend-patterns: React/Next.js state management, performance
- security-review: Authentication, input validation, secrets management
- tdd-workflow: Test-driven development with 80%+ coverage
- documentation-lookup: Up-to-date docs via Context7 MCP
- e2e-testing: Playwright E2E testing patterns
- database-migrations: Migration patterns across frameworks

## Platform-Specific Configuration

### Claude Code (.claudercules)

- Uses .claude/ directory structure
- Supports hooks, rules, skills, commands
- Agent orchestration via AGENTS.md

### Codex (.codexrules)

- Uses .codex/ directory with config.toml
- Auto-loads skills from .agents/skills/
- MCP servers: GitHub, Context7, Exa, Memory, Playwright, Sequential Thinking
- Model recommendations: GPT 5.4 for most tasks

### OpenCode (.opencoderules)

- Uses .opencode/ directory structure
- Commands in .opencode/commands/
- Tools in .opencode/tools/
- Prompts in .opencode/prompts/

### Cursor (.cursorrules)

- Uses .cursor/ directory structure
- Rules with YAML frontmatter (description, globs, alwaysApply)
- Hooks with adapter pattern for Claude Code compatibility

## ECC Guardrails (from repository history)

- Commit Workflow: Prefer conventional commit messaging with prefixes (fix, test, feat, docs)
- Architecture: Preserve hybrid module organization, separate test layout
- Code Style: camelCase file naming, relative imports, mixed exports
- ECC Defaults: Full install profile recommended, validate risky config changes in PRs

## Success Metrics (Universal)

- All tests pass with 80%+ coverage
- No security vulnerabilities
- Code is readable and maintainable
- Performance is acceptable
- User requirements are met

## Quick Reference

- For Cursor: Use .cursorrules
- For Claude Code: Use .claudercules
- For Codex: Use .codexrules
- For OpenCode: Use .opencoderules
- For all others: Use .agentrules (this file)