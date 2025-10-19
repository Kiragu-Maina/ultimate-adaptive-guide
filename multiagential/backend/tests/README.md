# Backend Testing

This directory contains comprehensive unit and integration tests for the Adaptive Learning Platform backend.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py          # Shared pytest fixtures
├── test_agents.py       # Unit tests for all 8 agents
└── test_endpoints.py    # Integration tests for API endpoints
```

## Running Tests

### Inside Docker Container

```bash
# Install test dependencies (if not already installed)
docker compose exec backend pip install pytest pytest-asyncio pytest-cov pytest-mock

# Run all tests
docker compose exec backend pytest

# Run with coverage report
docker compose exec backend pytest --cov=. --cov-report=html

# Run only unit tests
docker compose exec backend pytest -m unit

# Run only integration tests
docker compose exec backend pytest -m integration

# Run specific test file
docker compose exec backend pytest tests/test_agents.py

# Run specific test class
docker compose exec backend pytest tests/test_agents.py::TestLearnerProfilerAgent

# Run specific test
docker compose exec backend pytest tests/test_agents.py::TestLearnerProfilerAgent::test_create_learner_profile

# Verbose output
docker compose exec backend pytest -v

# Stop on first failure
docker compose exec backend pytest -x
```

### On Host Machine (if dependencies installed)

```bash
cd backend
pytest
```

## Test Coverage

### Unit Tests (test_agents.py)

Tests for all 8 adaptive learning agents:

1. **Learner Profiler Agent** - Profile creation from onboarding data
2. **Journey Architect Agent** - Learning journey creation and adjustment
3. **Performance Analyzer Agent** - Performance analysis from quiz history
4. **Content Personalizer Agent** - Adaptive content generation
5. **Quiz Generator Agent** - Difficulty-appropriate quiz creation
6. **Diagram Generator Agent** - Mermaid diagram generation
7. **Recommendation Agent** - Personalized recommendations
8. **Feedback Agent** - Sentiment analysis and motivational feedback

### Integration Tests (test_endpoints.py)

Tests for all API endpoints:

- **GET /** - Health check
- **GET /health/cache** - Redis cache health
- **POST /adaptive/onboarding** - User onboarding workflow
- **GET /adaptive/content** - Adaptive content delivery
- **GET /adaptive/journey** - Learning journey retrieval
- **GET /adaptive/recommendations** - Personalized recommendations
- **GET /adaptive/performance** - Performance analytics
- **GET /adaptive/agent-decisions** - Agent decision history

## Test Markers

Tests are marked for selective execution:

- `@pytest.mark.unit` - Unit tests for agents
- `@pytest.mark.integration` - Integration tests for endpoints
- `@pytest.mark.slow` - Tests that take longer to run

## Mocking Strategy

All tests use mocked LLM API calls to:
- Avoid actual API costs
- Ensure tests run quickly
- Make tests deterministic and reliable

Key mocked components:
- `openai.OpenAI` client
- Database operations (`db_postgres`)
- Redis cache operations

## Coverage Goals

- **Target**: 80%+ code coverage
- **Current**: Run `pytest --cov` to see current coverage
- Coverage report generated in `htmlcov/index.html`

## Continuous Integration

Tests should be run:
- Before committing code
- In CI/CD pipeline
- Before deploying to production

## Troubleshooting

### Import Errors

If you get import errors, ensure you're running tests from the backend directory:
```bash
cd /app  # Inside Docker container
pytest
```

### API Key Errors

Tests use mocked API calls and set `OPENROUTER_API_KEY=test-key-12345` automatically.
If you see API key errors, check `conftest.py` is properly setting environment variables.

### Database Errors

Integration tests mock all database operations. If you see database errors:
1. Check mock configurations in `conftest.py`
2. Ensure database patches are applied correctly

## Adding New Tests

### Unit Test Template

```python
@pytest.mark.unit
class TestNewAgent:
    @patch("new_agent.client")
    def test_agent_function(self, mock_client):
        # Arrange
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "expected output"
        mock_client.chat.completions.create.return_value = mock_response

        # Act
        result = agent_function(input_data)

        # Assert
        assert "expected_key" in result
```

### Integration Test Template

```python
@pytest.mark.integration
class TestNewEndpoint:
    @patch("module.dependency")
    def test_endpoint(self, mock_dep, client):
        # Arrange
        mock_dep.return_value = expected_value

        # Act
        response = client.get("/new-endpoint")

        # Assert
        assert response.status_code == 200
        assert "expected_key" in response.json()
```

## Best Practices

1. **Mock External Dependencies** - Never make actual API calls in tests
2. **Test Happy & Error Paths** - Test both success and failure scenarios
3. **Keep Tests Fast** - Use mocks to avoid slow operations
4. **Descriptive Names** - Test names should describe what they test
5. **Arrange-Act-Assert** - Follow AAA pattern for clarity
6. **Independent Tests** - Tests should not depend on each other
7. **Clean Up** - Use fixtures for setup/teardown

## Test Results Interpretation

```
===== test session starts =====
collected 45 items

tests/test_agents.py::TestLearnerProfilerAgent::test_create_learner_profile PASSED [ 2%]
...

===== 45 passed in 2.34s =====
```

- **PASSED** ✅ - Test succeeded
- **FAILED** ❌ - Test failed (check error message)
- **SKIPPED** ⏭️ - Test was skipped
- **XFAIL** ⚠️ - Expected failure (known issue)

## Maintenance

- Update tests when agents/endpoints change
- Add tests for new features
- Keep test coverage above 80%
- Review and update mocks as APIs evolve
