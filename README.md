# Python API Automation Testing

A simple, beginner-friendly API automation project using **Behave (BDD)** and **requests**, with **miniconda** for package management.

It tests the posts endpoints of the [JSONPlaceholder](https://jsonplaceholder.typicode.com/) public API: reading posts with positive, negative and edge-case scenarios, plus basic smoke checks for POST, PUT and PATCH.

## Project Structure

```
automation_py_api/
├── features/
│   ├── jsonplaceholder/
│   │   └── posts_read.feature     # GET scenarios for posts and comments
│   ├── api_testing.feature        # Smoke scenarios for POST, PUT, PATCH
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

| Tag | Meaning |
|---|---|
| `@smoke` | Fast check that each HTTP method works |
| `@regression` | Full coverage of an area |
| `@positive` / `@negative` / `@edge` | Scenario intent: happy path, expected errors, boundaries |
| `@jsonplaceholder` | Scenarios that hit JSONPlaceholder |

```bash
# Quick check of each HTTP method
behave --tags=@smoke

# Only the error cases
behave --tags=@negative

# Everything except edge cases
behave --tags="not @edge"

# A single feature file
behave features/jsonplaceholder/posts_read.feature

# Show scenarios skipped by a tag filter (hidden by default in behave.ini)
behave --tags=@smoke --show-skipped
```

## What Gets Tested

**Reading posts** ([posts_read.feature](features/jsonplaceholder/posts_read.feature)) - 17 scenarios, counting each Examples row:

| Type | Request | Checks |
|---|---|---|
| Positive | `GET /posts/1` | 200, JSON content type, `id` is 1, `userId` is an integer, `title` and `body` are non-empty strings |
| Positive | `GET /posts` | 100 posts, each with `userId`, `id`, `title`, `body` |
| Positive | `GET /posts?userId=1`, `5`, `10` | 10 posts, all from that user |
| Positive | `GET /posts/1/comments` | 5 comments, all for post 1, every email contains `@` |
| Positive | `/posts/1/comments` vs `/comments?postId=1` | Both routes return the same body |
| Negative | `GET /posts/0`, `101`, `9999`, `abc` | 404 with an empty object |
| Negative | `GET /users/11` | 404 with an empty object |
| Edge | `GET /posts/1`, `/posts/100` | First and last ids return 200 |
| Edge | `GET /posts?userId=999` | 200 with an empty list, not a 404 |
| Edge | `GET /posts?_page=2&_limit=5` | Ids 6-10 and header `X-Total-Count: 100` |
| Edge | `GET /posts?_page=999&_limit=10` | 200 with an empty list |

**Writing posts** ([api_testing.feature](features/api_testing.feature)) - 3 `@smoke` scenarios:

1. **POST** `/posts` - Creates a new post and verifies an ID is returned
2. **PUT** `/posts/1` - Updates an entire post and verifies the title changed
3. **PATCH** `/posts/1` - Partially updates a post (title only) and verifies the change

Every scenario shares a `Background` step that sets the base URL.

## Modifying Test Data

All test data is centralized in [test_data.py](test_data.py):

- `BASE_URL` - The API endpoint
- `REQUEST_TIMEOUT` - Seconds to wait for each request before failing (default `10`)
- `POST_PAYLOAD` - Data sent in POST requests
- `PUT_PAYLOAD` - Data sent in PUT requests
- `PATCH_PAYLOAD` - Data sent in PATCH requests

Edit this file to test different data without touching the feature files or step definitions.

The read scenarios keep their inputs in the feature file instead. To try another id or user, add a row to the matching `Examples:` table in [posts_read.feature](features/jsonplaceholder/posts_read.feature); the `note` column says why the row is there and shows up in the scenario name.

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

**`Expected a non-empty list but got: []`?**
- "Every item in the response..." steps refuse to pass on an empty list, so a filter that matches nothing is reported instead of passing silently. Check the query string in the scenario.

## Next Steps

- Expand write coverage (data tables, PUT vs PATCH semantics, known issues)
- Extract a reusable API client and assertion helpers
- Move configuration (URLs, credentials) to environment variables
- Add JSON Schema contract checks and pytest unit tests for helpers
- Add Allure/JUnit reporting and a GitHub Actions pipeline

## Learning Resources

- [Behave Documentation](https://behave.readthedocs.io/)
- [Behave Configuration Files](https://behave.readthedocs.io/en/latest/behave/#configuration-files)
- [Behave Tag Expressions](https://behave.readthedocs.io/en/latest/tag_expressions/)
- [Behave Gherkin: Background, Scenario Outlines, Tags](https://behave.readthedocs.io/en/latest/gherkin/)
- [Requests Sessions and Timeouts](https://requests.readthedocs.io/en/latest/user/advanced/#session-objects)
- [Requests Library](https://requests.readthedocs.io/)
- [JSONPlaceholder API Guide](https://jsonplaceholder.typicode.com/guide/)
