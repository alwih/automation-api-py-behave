from scripts.junit_summary import summarize

AUTH = """<testsuite name="dummyjson.auth.Authentication" tests="4" errors="1" failures="1" skipped="0" time="2.34">
<testcase name="Log in" status="passed" time="0.5"><system-out>ok</system-out></testcase>
<testcase name="Bad token | rejected" status="failed" time="0.3"><failure message="Expected 401&#10;but got 500" type="AssertionError">

Failing step: Then the response status code should be 401 ... failed in 0.000s
Location: features/dummyjson/auth.feature:149
ASSERT FAILED: Expected 401 but got 500
</failure></testcase>
<testcase name="Broken step" status="error" time="0.1"><error message="boom" type="RuntimeError">Traceback</error></testcase>
<testcase name="Left out by tags" status="skipped" time="0"/>
</testsuite>"""

POSTS = """<testsuite name="jsonplaceholder.posts_read.Reading posts" tests="2" errors="0" failures="0" skipped="0" time="0.16">
<testcase name="Get a post" status="passed" time="0.06"/>
<testcase name="List posts" status="passed" time="0.05"/>
</testsuite>"""

# What behave writes when the @authenticated login fails in a feature hook
HOOK_FAILED = """<testsuite name="dummyjson.auth.Authentication" tests="2" errors="0" failures="0" skipped="0" time="0.0">
<testcase name="Log in" status="untested" time="0"/>
<testcase name="Profile" status="untested" time="0"/>
</testsuite>"""


def write(directory, **suites):
    for name, xml in suites.items():
        (directory / f"TESTS-{name}.xml").write_text(xml)
    return directory


def test_counts_each_feature_and_the_total(tmp_path):
    summary = summarize(write(tmp_path, auth=AUTH, posts=POSTS))
    assert summary.startswith("### Scenarios: 3 passed, 2 failed\n")
    assert "| `dummyjson.auth.Authentication` | 1 | 2 | 0 | 2.3 s |" in summary
    assert "| `jsonplaceholder.posts_read.Reading posts` | 2 | 0 | 0 | 0.2 s |" in summary
    assert "| **Total** | **3** | **2** | **0** | **2.5 s** |" in summary


def test_failed_scenarios_show_their_location_and_a_one_line_message(tmp_path):
    summary = summarize(write(tmp_path, auth=AUTH))
    assert "| Bad token \\| rejected | `features/dummyjson/auth.feature:149` | Expected 401 but got 500 |" in summary
    assert "| Broken step | | boom |" in summary
    assert "Left out by tags" not in summary


def test_long_messages_are_cut(tmp_path):
    summary = summarize(write(tmp_path, auth=AUTH.replace('message="boom"', f'message="{"x" * 500}"')))
    assert f"| {'x' * 200}... |" in summary


def test_scenarios_stopped_by_a_hook_are_not_counted_as_passed(tmp_path):
    summary = summarize(write(tmp_path, auth=HOOK_FAILED))
    assert summary.startswith("### Scenarios: 0 passed, 0 failed, 2 not run\n")
    assert "| `dummyjson.auth.Authentication` | 0 | 0 | 2 | 0.0 s |" in summary
    assert "stopped by a failing hook" in summary


def test_a_clean_run_has_no_failure_table(tmp_path):
    summary = summarize(write(tmp_path, posts=POSTS))
    assert "Failed scenarios" not in summary
    assert "not run" not in summary.splitlines()[0]


def test_a_run_without_results_says_so(tmp_path):
    assert summarize(tmp_path) == f"No JUnit results in `{tmp_path}`: the run stopped before any scenario.\n"
