# API Testing Agent

A comprehensive, AI-powered API testing framework that automatically generates and executes test cases for REST APIs using Swagger/OpenAPI specifications. Built with LangGraph for intelligent workflow orchestration and Google's Gemini AI for test case generation.

## 🚀 Features

- **Automatic Test Generation**: Uses AI to generate comprehensive test cases (positive, negative, edge, auth)
- **Swagger/OpenAPI Support**: Parses and processes OpenAPI 2.0 and 3.x specifications
- **Intelligent Execution Planning**: Automatically determines optimal test execution order
- **Database Persistence**: Stores endpoints and test cases in PostgreSQL
- **Comprehensive Reporting**: Generates detailed JSON and text reports
- **Modular Architecture**: Clean, extensible codebase ready for scaling
- **LangGraph Integration**: Stateful workflow management with conditional routing

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [Architecture](#architecture)
- [Extending the Framework](#extending-the-framework)
- [API Reference](#api-reference)
- [Contributing](#contributing)

## 🛠 Installation

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Google AI API key (for Gemini)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SMART_API_TESTER
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL database**
   ```sql
   CREATE DATABASE SWAGGER_API;
   CREATE USER postgres WITH PASSWORD '9496';
   GRANT ALL PRIVILEGES ON DATABASE SWAGGER_API TO postgres;
   ```

4. **Configure environment**
   - Update `config/settings.py` with your database credentials
   - Set your Google AI API key in the configuration
   - Update the Swagger file path to point to your API specification

## 🚀 Quick Start

### Basic Usage

```python
from agents import get_api_testing_agent, create_initial_state

# Get the agent
agent = get_api_testing_agent()

# Create initial state
initial_state = create_initial_state()

# Run the complete workflow
final_state = agent.run(initial_state)

# Print results
agent.print_workflow_summary()
```

### Command Line Usage

```bash
python main.py
```

### Custom Configuration

```python
from main import run_with_custom_config

# Run with custom settings
exit_code = run_with_custom_config(
    swagger_file_path="/path/to/your/swagger.json",
    base_url="https://api.example.com",
    database_config={
        "host": "localhost",
        "database": "my_api_db",
        "user": "myuser",
        "password": "mypassword"
    }
)
```

## ⚙️ Configuration

The framework uses a centralized configuration system in `config/settings.py`:

### Database Configuration
```python
@dataclass
class DatabaseConfig:
    host: str = "localhost"
    database: str = "SWAGGER_API"
    user: str = "postgres"
    password: str = "9496"
    port: int = 5432
```

### API Configuration
```python
@dataclass
class APIConfig:
    base_url: str = "http://localhost:3000"
    timeout: int = 30
    max_retries: int = 3
```

### LLM Configuration
```python
@dataclass
class LLMConfig:
    api_key: str = "your-gemini-api-key"
    model: str = "gemini-2.5-flash"
    max_tokens: int = 4000
```

## 📖 Usage

### 1. Basic Workflow

The agent follows this workflow:

1. **Database Initialization**: Creates required tables
2. **Swagger Parsing**: Extracts endpoints from OpenAPI spec
3. **Endpoint Storage**: Saves endpoints to database
4. **Test Generation**: AI generates comprehensive test cases
5. **Validation**: Validates generated test cases
6. **Persistence**: Stores test cases in database
7. **Execution Planning**: Determines optimal test order
8. **Test Execution**: Runs all test cases
9. **Report Generation**: Creates detailed reports

### 2. Programmatic Usage

```python
from agents import APITestingAgent, create_initial_state
from config import update_config

# Update configuration
update_config(
    swagger_file_path="/path/to/swagger.json",
    api={"base_url": "https://api.example.com"}
)

# Create agent
agent = APITestingAgent()

# Run workflow
initial_state = create_initial_state()
final_state = agent.run(initial_state)

# Access results
execution_logs = agent.get_execution_logs()
test_results = agent.get_test_results()
errors = agent.get_errors()
```

### 3. Monitoring Progress

```python
# Get workflow status
status = agent.get_workflow_status()
print(f"Completion: {status['completion_percentage']:.1f}%")
print(f"Current Step: {status['current_step']}")

# Visualize workflow
print(agent.visualize_workflow())
```

## 🏗 Architecture

The framework is organized into modular packages:

```
SMART_API_TESTER/
├── agents/                 # LangGraph agent and workflow
│   ├── api_testing_agent.py
│   ├── state.py
│   └── workflow_nodes.py
├── config/                 # Configuration management
│   └── settings.py
├── database/               # Database operations
│   ├── connection.py
│   └── models.py
├── generators/             # Test case generation
│   └── test_case_generator.py
├── parsers/                # Swagger/OpenAPI parsing
│   └── swagger_parser.py
├── reporters/              # Test reporting
│   └── test_reporter.py
├── runners/                # Test execution
│   ├── api_client.py
│   └── test_executor.py
├── utils/                  # Utilities
│   └── logger.py
├── main.py                 # Entry point
└── requirements.txt
```

### Key Components

- **APITestingAgent**: Main orchestrator using LangGraph
- **WorkflowNodes**: Individual processing steps
- **StateManager**: Manages workflow state
- **SwaggerParser**: Parses OpenAPI specifications
- **TestCaseGenerator**: AI-powered test generation
- **TestExecutor**: Executes test cases
- **TestReporter**: Generates reports

## 🔧 Extending the Framework

### Adding New Test Strategies

1. **Create a new generator class**:
```python
from generators.test_case_generator import TestCaseGenerator

class CustomTestCaseGenerator(TestCaseGenerator):
    def generate_custom_test_cases(self, endpoints):
        # Your custom logic here
        pass
```

2. **Register in workflow**:
```python
# In agents/workflow_nodes.py
def custom_generation_node(self, state: AgentState) -> AgentState:
    generator = CustomTestCaseGenerator()
    # Your logic here
    return state
```

### Adding Authentication Support

1. **Extend API client**:
```python
from runners.api_client import APIClient

class AuthenticatedAPIClient(APIClient):
    def __init__(self, auth_token=None):
        super().__init__()
        self.auth_token = auth_token
    
    def make_request(self, method, url, **kwargs):
        if self.auth_token:
            kwargs.setdefault('headers', {})['Authorization'] = f'Bearer {self.auth_token}'
        return super().make_request(method, url, **kwargs)
```

### Adding UI Integration

The framework is designed to easily integrate with web UIs:

```python
# FastAPI integration example
from fastapi import FastAPI
from agents import get_api_testing_agent

app = FastAPI()
agent = get_api_testing_agent()

@app.post("/run-tests")
async def run_tests(swagger_file: str, base_url: str):
    # Update config and run tests
    # Return results as JSON
    pass

@app.get("/status")
async def get_status():
    return agent.get_workflow_status()
```

### Adding New Report Formats

```python
from reporters.test_reporter import TestReporter

class HTMLTestReporter(TestReporter):
    def generate_html_report(self, output_path: str = None) -> str:
        # Generate HTML report
        pass
```

## 📚 API Reference

### Core Classes

#### `APITestingAgent`
Main agent class for orchestrating the testing workflow.

**Methods:**
- `run(initial_state)`: Execute the complete workflow
- `get_workflow_status()`: Get current workflow status
- `get_execution_logs()`: Get test execution logs
- `get_test_results()`: Get test results
- `print_workflow_summary()`: Print summary to console

#### `SwaggerParser`
Parses Swagger/OpenAPI specification files.

**Methods:**
- `parse_swagger_file(file_path)`: Parse a Swagger file
- `extract_endpoints(swagger_data)`: Extract endpoints from data

#### `TestCaseGenerator`
Generates test cases using AI.

**Methods:**
- `generate_test_cases(endpoints)`: Generate test cases for endpoints
- `validate_test_cases(test_cases)`: Validate generated test cases

#### `TestExecutor`
Executes test cases against APIs.

**Methods:**
- `execute_test_case(test_case)`: Execute a single test case
- `execute_test_suite(execution_order)`: Execute complete test suite

### Configuration

#### `AppConfig`
Main configuration class containing all settings.

**Attributes:**
- `database`: Database configuration
- `api`: API configuration  
- `llm`: LLM configuration
- `swagger_file_path`: Path to Swagger file

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/new-feature`
3. **Make your changes**: Follow the existing code style
4. **Add tests**: Ensure your changes are tested
5. **Submit a pull request**: Describe your changes clearly

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest

# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

### Code Style

- Follow PEP 8 guidelines
- Use type hints
- Add docstrings for all public methods
- Keep functions small and focused
- Use meaningful variable names

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

1. Check the [Issues](https://github.com/your-repo/issues) page
2. Create a new issue with detailed information
3. Include your configuration and error logs

## 🔮 Future Enhancements

- [ ] Web UI with FastAPI
- [ ] Support for GraphQL APIs
- [ ] Integration with CI/CD pipelines
- [ ] Performance testing capabilities
- [ ] Custom assertion frameworks
- [ ] Test data management
- [ ] Parallel test execution
- [ ] API mocking support

---

**Built with ❤️ using LangGraph and Google Gemini AI**
