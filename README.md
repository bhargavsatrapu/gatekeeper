# 🚀 GATEKEEPER - Comprehensive API Testing Framework

GATEKEEPER is a powerful API testing framework that allows you to upload Swagger/OpenAPI specifications, automatically generate test cases, execute tests, and generate comprehensive reports.

## ✨ Features

- **Swagger/OpenAPI Ingestion**: Upload and parse Swagger JSON/YAML files
- **Automatic Test Case Generation**: Generate positive and negative test cases for each API
- **Custom Test Cases**: Create custom test cases with specific requirements
- **Request Body Management**: Store and validate request bodies for POST/PUT requests
- **Test Execution**: Execute tests against your APIs and collect results
- **Comprehensive Reporting**: Generate detailed HTML reports with pass/fail statistics
- **Modern Web Interface**: Beautiful, responsive UI for managing the entire testing workflow

## 🏗️ Architecture

The framework consists of several key components:

- **Database Layer**: PostgreSQL with tables for APIs, test cases, test results, and test runs
- **Backend API**: FastAPI-based REST API for all testing operations
- **Frontend Interface**: Modern HTML/CSS/JavaScript UI for user interaction
- **Test Execution Engine**: Automated test runner with configurable timeouts and error handling

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+
- PostgreSQL database
- Modern web browser

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd gatekeeper

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (optional)
export DB_NAME=gatekeeper
export DB_USER=postgres
export DB_PASSWORD=your_password
export DB_HOST=localhost
export DB_PORT=5432
export API_BASE_URL=http://your-api-base-url.com
```

### 3. Database Setup

Ensure PostgreSQL is running and create a database:

```sql
CREATE DATABASE gatekeeper;
```

### 4. Run the Application

```bash
# Start the FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Access the Interface

Open your browser and navigate to:
- **Main Interface**: http://localhost:8000/ui/
- **Testing Interface**: http://localhost:8000/ui/testing.html

## 📖 Usage Guide

### Step 1: Upload and Ingest Swagger Specification

1. Go to the main interface at `/ui/`
2. Upload your Swagger JSON or YAML file
3. Click "Ingest to DB" to parse and store the API specifications

### Step 2: Generate Test Cases

1. Navigate to the testing interface at `/ui/testing.html`
2. Go to the "Test Cases" tab
3. Click "Generate Test Cases" for specific APIs or use "Auto-generate" for all
4. The system will create:
   - **Positive test cases**: Valid requests with expected success responses
   - **Negative test cases**: Invalid requests, missing fields, unauthorized access

### Step 3: Customize Test Cases (Optional)

1. In the "Test Cases" tab, click "Create Custom Test Case"
2. Select an API and define:
   - Test case name and description
   - Test type (positive/negative)
   - Expected status code
   - Custom request body (for POST/PUT requests)

### Step 4: Execute Tests

1. Go to the "Test Runs" tab
2. Create a new test run with a name and description
3. Click "Execute Tests" to run all test cases
4. Monitor the execution progress and results

### Step 5: View Results and Generate Reports

1. Navigate to the "Results" tab
2. View detailed test results including:
   - Pass/fail statistics
   - Response times
   - Error messages
   - Response bodies
3. Generate comprehensive HTML reports for test runs

## 🔧 API Endpoints

### Testing Endpoints

- `POST /testing/apis/{api_id}/request-bodies` - Add request body for an API
- `GET /testing/apis/{api_id}/request-bodies` - Get request bodies for an API
- `POST /testing/apis/{api_id}/test-cases` - Create custom test case
- `GET /testing/apis/{api_id}/test-cases` - Get test cases for an API
- `POST /testing/apis/{api_id}/generate-test-cases` - Auto-generate test cases
- `POST /testing/test-runs` - Create test run
- `POST /testing/test-runs/{test_run_id}/execute` - Execute test run
- `GET /testing/test-runs` - List all test runs
- `GET /testing/test-results` - Get test results
- `GET /testing/reports/{test_run_id}` - Generate HTML report

### File Management Endpoints

- `POST /upload` - Upload Swagger file
- `GET /files` - List uploaded files
- `POST /files/{filename}/ingest` - Ingest file to database
- `GET /apis` - List ingested APIs

## 🗄️ Database Schema

The framework creates the following tables:

- **api_specs**: Stores parsed API specifications
- **test_cases**: Contains test case definitions
- **request_bodies**: Stores user-provided request bodies
- **test_results**: Records test execution results
- **test_runs**: Manages test execution sessions

## ⚙️ Configuration

### Environment Variables

- `DB_NAME`: Database name (default: gatekeeper)
- `DB_USER`: Database user (default: postgres)
- `DB_PASSWORD`: Database password (default: 0000)
- `DB_HOST`: Database host (default: localhost)
- `DB_PORT`: Database port (default: 5432)
- `API_BASE_URL`: Base URL for API testing (default: http://localhost:8000)
- `SCREENSHOT_DIR`: Directory for screenshots (default: screenshots)
- `MAX_TEST_TIMEOUT`: Maximum test execution timeout in seconds (default: 30)
- `ENABLE_SCREENSHOTS`: Enable screenshot capture (default: true)

## 🧪 Test Case Types

### Positive Test Cases
- Valid request data
- Expected success responses (200, 201, 204)
- Proper authentication and authorization

### Negative Test Cases
- Invalid request data
- Missing required fields
- Unauthorized access attempts
- Expected error responses (400, 401, 403, 500)

## 📊 Reporting Features

- **Summary Statistics**: Total tests, passed, failed, errors
- **Detailed Results**: Individual test case results with response data
- **Performance Metrics**: Response times and execution duration
- **Error Details**: Complete error messages and stack traces
- **HTML Reports**: Professional, printable test reports

## 🔒 Security Considerations

- Database connections use connection pooling
- Input validation on all endpoints
- SQL injection protection through parameterized queries
- File upload restrictions and validation

## 🚧 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Verify PostgreSQL is running
   - Check database credentials in environment variables
   - Ensure database exists

2. **Test Execution Fails**
   - Verify API_BASE_URL is correct
   - Check network connectivity to target APIs
   - Review API authentication requirements

3. **Test Cases Not Generated**
   - Ensure Swagger file is properly ingested
   - Check API specifications for valid paths and methods
   - Verify database tables are created

### Debug Mode

Enable debug logging by setting the log level:

```bash
export LOG_LEVEL=DEBUG
uvicorn app.main:app --reload --log-level debug
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation at `/docs` when the server is running

---

**GATEKEEPER** - Empowering developers with comprehensive API testing capabilities! 🚀

