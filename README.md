# Python API Automation Testing

A simple, beginner-friendly API automation project using **Behave (BDD)** and **requests**, with **miniconda** for package management.

This project tests 4 basic HTTP methods (GET, POST, PUT, PATCH) against the [JSONPlaceholder](https://jsonplaceholder.typicode.com/) public API.

## Project Structure

```
automation_py_api/
├── features/
│   ├── api_testing.feature        # BDD test scenarios in plain English
│   └── steps/
│       └── api_steps.py           # Python step definitions
├── test_data.py                   # Test data (URLs, payloads)
├── requirements.txt               # Python dependencies
├── .gitignore                     # Files kept out of version control
└── README.md                      # This file
```

## Prerequisites

- **Python 3.8+** (via miniconda or anaconda)
- **Git** (to clone the repository)
- **Internet connection** (to call the public API)

## Setup Instructions

### 1. Install Miniconda (if not already installed)

Download and install from: https://docs.conda.io/en/latest/miniconda.html

Or on macOS with Homebrew:
```bash
brew install --cask miniconda
```

### 2. Create a Conda Environment

```bash
# Create a new environment named 'api_automation' with Python 3.11
conda create -n api_automation python=3.11 -y

# Activate the environment
conda activate api_automation
```

### 3. Install Dependencies

```bash
# Clone the repository and move into it
git clone https://github.com/alwih/automation-api-py-behave.git
cd automation-api-py-behave

# Install required packages
pip install -r requirements.txt
```

## Running the Tests

### Run All Tests with Behave

```bash
# Make sure your environment is active
conda activate api_automation

# Run all scenarios
behave

# Run with verbose output
behave -v

# Run with detailed step output
behave --no-capture
```

## What Gets Tested

The test suite covers 4 HTTP operations:

1. **GET** `/posts/1` - Retrieves a single post and verifies it contains userId and title
2. **POST** `/posts` - Creates a new post and verifies an ID is returned
3. **PUT** `/posts/1` - Updates an entire post and verifies the title changed
4. **PATCH** `/posts/1` - Partially updates a post (title only) and verifies the change

## Modifying Test Data

All test data is centralized in [test_data.py](test_data.py):

- `BASE_URL` - The API endpoint
- `POST_PAYLOAD` - Data sent in POST requests
- `PUT_PAYLOAD` - Data sent in PUT requests
- `PATCH_PAYLOAD` - Data sent in PATCH requests

Edit this file to test different data without touching the feature files or step definitions.

## Troubleshooting

**Environment not found?**
```bash
conda env list  # Check if api_automation exists
```

**Import errors?**
```bash
conda activate api_automation
pip install -r requirements.txt --force-reinstall
```

**Tests failing?**
- Verify internet connection
- Check if https://jsonplaceholder.typicode.com/ is accessible in your browser

## Next Steps

- Add a behave config and hooks (shared HTTP session, request timeouts)
- Expand coverage with negative and edge-case scenarios
- Extract a reusable API client and assertion helpers
- Move configuration (URLs, credentials) to environment variables
- Add JSON Schema contract checks and pytest unit tests for helpers
- Add Allure/JUnit reporting and a GitHub Actions pipeline

## Learning Resources

- [Behave Documentation](https://behave.readthedocs.io/)
- [Requests Library](https://requests.readthedocs.io/)
- [JSONPlaceholder API Guide](https://jsonplaceholder.typicode.com/guide/)
