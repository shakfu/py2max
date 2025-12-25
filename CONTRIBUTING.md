# Contributing to py2max

Thank you for your interest in contributing to py2max! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

- Be respectful and inclusive in all interactions
- Focus on constructive feedback
- Help create a welcoming environment for all contributors

## Getting Started

### Development Setup

1. **Clone the repository**:

   ```bash
   git clone https://github.com/shakfu/py2max.git
   cd py2max
   ```

2. **Install uv** (if not already installed):

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Set up development environment**:

   ```bash
   uv sync
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

4. **Verify installation**:

   ```bash
   make test
   ```

## Development Workflow

### Before You Start

1. **Check existing issues** to see if your feature/bug is already being worked on
2. **Open an issue** to discuss major changes before implementing them
3. **Fork the repository** and create a feature branch

### Making Changes

1. **Create a feature branch**:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards (see below)

3. **Run quality checks**:

   ```bash
   make quality  # Runs linting and type checking
   ```

4. **Run tests**:

   ```bash
   make test  # Run all tests
   make coverage  # Generate coverage report
   ```

5. **Commit your changes**:

   ```bash
   git add .
   git commit -m "Add concise commit message"
   ```

## Coding Standards

### Code Style

- **Linter**: We use `ruff` for linting
- **Auto-fix**: Run `make lint-fix` to automatically fix issues
- **Line length**: Maximum 100 characters (configured in `pyproject.toml`)

### Type Hints

- **Required**: All function signatures must have type hints
- **Type checker**: We use `mypy` for static type checking
- **Run**: `make typecheck` or `mypy py2max`

### Testing

- **Coverage requirement**: Maintain > 80% test coverage (current: 82%)
- **Test framework**: pytest
- **Test location**: `tests/` directory
- **Naming**: Test files must start with `test_`

#### Writing Tests

```python
"""tests/test_my_feature.py"""

from py2max import Patcher

def test_my_feature():
    """Test description."""
    p = Patcher('test.maxpat')
    # ... test code ...
    assert expected == actual
```

#### Running Tests

```bash
# Run all tests
make test

# Run specific test file
uv run pytest tests/test_my_feature.py

# Run with verbose output
uv run pytest -v

# Generate coverage report
make coverage
```

### Documentation

- **Docstrings**: All public classes, methods, and functions must have docstrings
- **Format**: Google-style docstrings
- **Examples**: Include usage examples in docstrings

#### Docstring Example

```python
def add_textbox(self, text: str, maxclass: Optional[str] = None) -> Box:
    """Add a text-based Max object to the patch.

    Creates a Max object from a text specification (e.g., 'cycle~ 440').

    Args:
        text: Max object specification (e.g., 'cycle~ 440', 'gain~').
        maxclass: Override the automatically determined maxclass.

    Returns:
        The created Box object.

    Example:
        >>> p = Patcher('patch.maxpat')
        >>> osc = p.add_textbox('cycle~ 440')
        >>> gain = p.add_textbox('gain~')
        >>> p.add_line(osc, gain)
    """
    # ... implementation ...
```

## Pull Request Process

### Checklist

Before submitting a pull request, ensure:

- [ ] Code follows project style guidelines
- [ ] All tests pass (`make test`)
- [ ] Type checking passes (`make typecheck`)
- [ ] Linting passes (`make lint`)
- [ ] Test coverage remains > 80% (`make coverage`)
- [ ] Documentation is updated (if applicable)
- [ ] CHANGELOG.md is updated (for user-facing changes)
- [ ] Commit messages are clear and descriptive

### Submitting

1. **Push your branch**:

   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a pull request** on GitHub with:
   - Clear title describing the change
   - Description explaining:
     - What changed
     - Why it changed
     - How to test it
   - Link to related issues

3. **Respond to feedback** from reviewers

4. **Ensure CI passes** - All GitHub Actions checks must pass

## Commit Message Guidelines

### Format

```text
<type>: <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```text
feat: add find_by_text method for searching boxes

Adds case-insensitive text search across all boxes in a patcher.
Includes comprehensive test coverage.

Closes #123
```

```text
fix: resolve type error in db.py

Fixed incompatible types in db_path assignment by adding Union type.
```

## Project Structure

```text
py2max/
├── py2max/                # Main package
│   ├── core.py           # Core classes (Patcher, Box, Patchline)
│   ├── layout.py         # Layout managers
│   ├── maxref.py         # Max object reference system
│   ├── db.py             # SQLite database for maxref
│   ├── svg.py            # SVG export
│   ├── server.py         # Interactive WebSocket server
│   ├── cli.py            # Command-line interface
│   └── ...
├── tests/                 # Test suite
├── docs/                  # Documentation
├── .github/workflows/     # CI/CD configuration
├── Makefile              # Development commands
└── pyproject.toml        # Project configuration
```

## Common Tasks

### Running Quality Checks

```bash
# Run all quality checks
make quality

# Individual checks
make lint          # Code linting
make lint-fix      # Auto-fix lint issues
make typecheck     # Type checking
```

### Building Documentation

```bash
# Build Sphinx documentation
make docs

# Serve documentation
make docs-serve
# Then open docs/build/index.html
```

### Building Package

```bash
# Build wheel
make build

# Creates dist/py2max-*.whl
```

## Getting Help

- **Issues**: Open an issue on GitHub for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check the [docs](docs/) directory

## License

By contributing to py2max, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be recognized in:

- CHANGELOG.md (for significant contributions)
- GitHub contributors page
- Project documentation (for major features)

## Questions?

If you have questions about contributing, please:

1. Check existing issues and documentation
2. Open a GitHub Discussion
3. Reach out to maintainers

Thank you for contributing to py2max!
