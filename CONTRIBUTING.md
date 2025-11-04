# Contributing to EKG System

Thank you for your interest in contributing to the EKG System project! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/ekg-system.git`
3. Create a virtual environment: `python -m venv venv`
4. Activate the virtual environment:
   - Linux/Mac: `source venv/bin/activate`
   - Windows: `venv\Scripts\activate`
5. Install dependencies: `pip install -e .`
6. Install development dependencies: `pip install pytest pytest-cov`

## Development Process

1. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following the coding standards below

3. Add tests for any new functionality

4. Run the test suite to ensure everything works:
   ```bash
   python -m unittest discover tests
   ```

5. Commit your changes with a clear commit message:
   ```bash
   git commit -m "Add feature: brief description"
   ```

6. Push to your fork and submit a pull request

## Coding Standards

- Follow PEP 8 style guide for Python code
- Use descriptive variable and function names
- Add docstrings to all functions and classes
- Keep functions focused and concise
- Comment complex algorithms or non-obvious code

### Docstring Format

Use Google-style docstrings:

```python
def function_name(param1: type, param2: type) -> return_type:
    """
    Brief description of function.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ExceptionType: When this exception occurs
    """
    pass
```

## Testing

- Write unit tests for all new functionality
- Aim for high test coverage
- Test edge cases and error conditions
- Use meaningful test names that describe what is being tested

Example test:

```python
def test_detect_r_peaks_returns_correct_count(self):
    """Test that R-peak detection returns expected number of peaks."""
    # Test implementation
```

## Pull Request Guidelines

- Provide a clear description of the changes
- Reference any related issues
- Include screenshots for UI changes
- Ensure all tests pass
- Update documentation as needed
- Keep pull requests focused on a single feature or fix

## Code Review Process

- All submissions require review
- Address reviewer comments promptly
- Be respectful and constructive in discussions
- Reviewers will check:
  - Code quality and style
  - Test coverage
  - Documentation
  - Performance implications

## Areas for Contribution

### High Priority
- Additional arrhythmia detection algorithms
- Support for more data formats
- Performance optimizations
- Enhanced visualization options
- Mobile/web interface

### Medium Priority
- Additional export formats
- Cloud storage integration
- Machine learning models for classification
- Real-time monitoring dashboard
- Multi-channel EKG support

### Documentation
- Tutorials and examples
- API documentation improvements
- Translation to other languages
- Video demonstrations

### Testing
- Integration tests
- Performance benchmarks
- Stress testing
- Documentation of test data

## Bug Reports

When reporting bugs, please include:

- Operating system and version
- Python version
- EKG System version
- Complete error message and stack trace
- Steps to reproduce the issue
- Expected vs actual behavior
- Sample data if applicable

## Feature Requests

When requesting features, please:

- Check if the feature already exists or is planned
- Provide a clear use case
- Describe expected behavior
- Consider implementation complexity
- Be open to discussion and alternatives

## Questions and Support

- Check existing issues and documentation first
- Use GitHub Discussions for questions
- Be specific and provide context
- Include relevant code snippets or data

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Respect different viewpoints
- Report unacceptable behavior to project maintainers

Thank you for contributing to EKG System!
