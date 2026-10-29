# Python API Automation Testing

A simple, beginner-friendly API automation project using **Behave (BDD)** and **requests**, with **miniconda** for package management.

This project tests 4 basic HTTP methods (GET, POST, PUT, PATCH) against the [JSONPlaceholder](https://jsonplaceholder.typicode.com/) public API.

## Project Structure

```
automation_py_api/
├── features/
│   ├── api_testing.feature        # BDD test scenarios in plain English
│   ├── environment.py             # Hooks: opens/closes an HTTP session per scenario
│   └── steps/
│       └── api_steps.py           # Python step definitions
├── test_data.py                   # Test data (URL, timeout, payloads)
├── behave.ini                     # Behave defaults (feature paths, output format)
├── environment.yml                # Conda environment (Python 3.11 + requirements)
├── requirements.txt               # Python dependencies (pinned)
├── .gitignore                     # Files kept out of version control
└── README.md                      # This file
```

Every scenario gets its own `requests.Session` (created in `before_scenario`, closed in `after_scenario`) with an `Accept: application/json` header, and every request uses an explicit timeout so a slow API fails the test instead of hanging the run.

## Prerequisites

- **Python 3.10+** (via miniconda or anaconda; `environment.yml` uses 3.11)
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
# Clone the repository and move into it
git clone https://github.com/alwih/automation-api-py-behave.git
cd automation-api-py-behave

# Create the 'api_automation' environment (Python 3.11 + requirements.txt)
conda env create -f environment.yml

# Activate the environment
conda activate api_automation
```

### 3. Install Dependencies

`environment.yml` already installs everything in `requirements.txt`. When the pinned versions change, update the existing environment instead of recreating it:

```bash
conda env update -f environment.yml --prune
```

Not using conda? Any Python 3.10+ virtual environment works:

```bash
python -m venv .venv
source .venv/bin/activate
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

Run from the repository root. `behave.ini` points behave at `features/` and uses the `pretty` formatter, so plain `behave` needs no extra arguments.

### Run by Tag

```bash
# Quick check of each HTTP method
behave --tags=@smoke

# Show scenarios skipped by a tag filter (hidden by default in behave.ini)
behave --tags=@smoke --show-skipped
```

## What Gets Tested

The test suite covers 4 HTTP operations:

1. **GET** `/posts/1` - Retrieves a single post and verifies it contains userId and title
2. **POST** `/posts` - Creates a new post and verifies an ID is returned
3. **PUT** `/posts/1` - Updates an entire post and verifies the title changed
4. **PATCH** `/posts/1` - Partially updates a post (title only) and verifies the change

All four scenarios are tagged `@smoke` and share a `Background` step that sets the base URL.

## Modifying Test Data

All test data is centralized in [test_data.py](test_data.py):

- `BASE_URL` - The API endpoint
- `REQUEST_TIMEOUT` - Seconds to wait for each request before failing (default `10`)
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

**`ModuleNotFoundError: No module named 'test_data'`?**
- Run `behave` from the repository root, not from inside `features/`

**Dependency install fails on an older environment?**
- `requests` 2.34 needs Python 3.10+. Recreate the environment:
```bash
conda env remove -n api_automation
conda env create -f environment.yml
```

**Tests failing?**
- Verify internet connection
- Check if https://jsonplaceholder.typicode.com/ is accessible in your browser
- `ConnectTimeout` / `ReadTimeout` errors mean the API didn't answer within `REQUEST_TIMEOUT`; raise it in `test_data.py` on a slow network

## Next Steps

- Expand coverage with negative and edge-case scenarios
- Extract a reusable API client and assertion helpers
- Move configuration (URLs, credentials) to environment variables
- Add JSON Schema contract checks and pytest unit tests for helpers
- Add Allure/JUnit reporting and a GitHub Actions pipeline

## Learning Resources

- [Behave Documentation](https://behave.readthedocs.io/)
- [Behave Configuration Files](https://behave.readthedocs.io/en/latest/behave/#configuration-files)
- [Behave Tag Expressions](https://behave.readthedocs.io/en/latest/tag_expressions/)
- [Requests Sessions and Timeouts](https://requests.readthedocs.io/en/latest/user/advanced/#session-objects)
- [Requests Library](https://requests.readthedocs.io/)
- [JSONPlaceholder API Guide](https://jsonplaceholder.typicode.com/guide/)
