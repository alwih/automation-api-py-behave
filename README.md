# Python API Automation Testing

A simple, beginner-friendly API automation project using **Behave (BDD)** and **requests**, with **miniconda** for package management.

It tests the posts endpoints of the [JSONPlaceholder](https://jsonplaceholder.typicode.com/) public API (read, create, update, delete) with positive, negative and edge-case scenarios, and records the API's known bugs as scenarios that are skipped by default.

## Project Structure

```
automation_py_api/
├── features/
│   ├── jsonplaceholder/
│   │   ├── posts_read.feature     # GET scenarios for posts and comments
│   │   └── posts_write.feature    # POST, PUT, PATCH, DELETE scenarios
│   ├── environment.py             # Hooks: opens/closes an HTTP session per scenario
│   └── steps/
│       └── api_steps.py           # Python step definitions
├── test_data.py                   # Base URL and request timeout
├── behave.ini                     # Behave defaults (paths, format, default tag filter)
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
| `@smoke` | Fast health check: one read, one write |
| `@regression` | Full coverage of an area |
| `@positive` / `@negative` / `@edge` | Scenario intent: happy path, expected errors, boundaries |
| `@known_issue` | Asserts the correct behavior for a known API bug, so it fails today |
| `@wip` | Work in progress |
| `@jsonplaceholder` | Scenarios that hit JSONPlaceholder |

Plain `behave` skips `@known_issue` and `@wip` (set by `default_tags` in `behave.ini`). A `--tags` option on the command line **replaces** that default instead of adding to it, so add `{config.tags}` to keep the known issues out:

```bash
# Quick health check
behave --tags=@smoke

# Full regression, still skipping known issues and work in progress
behave --tags="@regression and {config.tags}"

# Run only the known issues; they fail with the actual behavior described in each scenario
behave --tags=@known_issue

# Only the error cases
behave --tags=@negative

# Everything except edge cases
behave --tags="not @edge and {config.tags}"

# A single feature file
behave features/jsonplaceholder/posts_write.feature

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

**Writing posts** ([posts_write.feature](features/jsonplaceholder/posts_write.feature)) - 8 scenarios. JSONPlaceholder fakes writes, so the checks cover what the response says, not what is stored:

| Type | Request | Checks |
|---|---|---|
| Positive | `POST /posts` | 201, echoes every field sent, new `id` is an integer above 100 |
| Positive | `PUT /posts/1` with every field | 200, echoes every field sent |
| Positive | `GET /posts/1`, then `PATCH /posts/1` with a new title | 200, title changed, `id`, `userId`, `body` unchanged from the GET |
| Positive | `DELETE /posts/1` | 200 with an empty object |
| Edge | `POST /posts` with title `Café ☕ 日本語` | Text sent as raw UTF-8 comes back unchanged |
| Edge | `PUT /posts/1` with only a title | `body` and `userId` are gone (PUT replaces, PATCH merges) |
| Known issue | `PUT` / `PATCH /posts/9999` | Should be 404. Actual: PUT returns 500 with an HTML stack trace, PATCH returns 200 |

Every scenario shares a `Background` step that sets the base URL.

## Modifying Test Data

[test_data.py](test_data.py) holds the shared settings:

- `BASE_URL` - The API endpoint
- `REQUEST_TIMEOUT` - Seconds to wait for each request before failing (default `10`)

Request bodies live next to the scenario that sends them, as a data table:

```gherkin
When I send a POST request to "/posts" with:
  | field  | value                |
  | title  | Weekly release notes |
  | userId | 1                    |
```

Values are read as JSON when they parse, so `1` is sent as a number and `true` as a boolean; anything else, like `Weekly release notes`, is sent as a string. Wrap a value in double quotes (`"1"`) to send it as a string.

The read scenarios keep their inputs in the feature file too. To try another id or user, add a row to the matching `Examples:` table in [posts_read.feature](features/jsonplaceholder/posts_read.feature); the `note` column says why the row is there and shows up in the scenario name.

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

**`behave --tags=@regression` fails on `/posts/9999`?**
- Those are `@known_issue` scenarios. Command-line tags replace the default filter, so use `behave --tags="@regression and {config.tags}"`.

**`Expected a non-empty list but got: []`?**
- "Every item in the response..." steps refuse to pass on an empty list, so a filter that matches nothing is reported instead of passing silently. Check the query string in the scenario.

## Next Steps

- Extract a reusable API client and assertion helpers
- Move configuration (URLs, credentials) to environment variables
- Add JSON Schema contract checks and pytest unit tests for helpers
- Add Allure/JUnit reporting and a GitHub Actions pipeline

## Learning Resources

- [Behave Documentation](https://behave.readthedocs.io/)
- [Behave Configuration Files](https://behave.readthedocs.io/en/latest/behave/#configuration-files)
- [Behave Tag Expressions](https://behave.readthedocs.io/en/latest/tag_expressions/)
- [Behave Gherkin: Background, Scenario Outlines, Tags](https://behave.readthedocs.io/en/latest/gherkin/)
- [Behave Step Data (tables)](https://behave.readthedocs.io/en/latest/gherkin/#step-data)
- [MDN: PUT](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/PUT) and [PATCH](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/PATCH)
- [Requests Sessions and Timeouts](https://requests.readthedocs.io/en/latest/user/advanced/#session-objects)
- [Requests Library](https://requests.readthedocs.io/)
- [JSONPlaceholder API Guide](https://jsonplaceholder.typicode.com/guide/)
