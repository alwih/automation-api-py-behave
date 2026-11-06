# Run from the repository root with the api_automation environment active.
# The behave targets clear reports/ first, so the reports show only the current make run.

RESULTS := reports/allure-results
HTML_REPORT := reports/allure-report
# Pretty console output, plus Allure results and JUnit XML (reports/junit, set in behave.ini)
REPORTING := -f allure -o $(RESULTS) -f pretty --junit

.PHONY: unit smoke regression known-issues tagged report clean

unit:
	pytest

smoke: clean
	behave $(REPORTING) --tags="@smoke and {config.tags}"

regression: clean
	behave $(REPORTING) --tags="@regression and {config.tags}"

# Fails while the bugs are still there: each scenario asserts the correct behaviour
known-issues: clean
	behave $(REPORTING) --tags=@known_issue

# Any tag expression, read from TAGS: make tagged TAGS="@dummyjson and {config.tags}"
tagged: clean
	behave $(REPORTING) --tags="$${TAGS:?set it, e.g. make tagged TAGS=@dummyjson}"

# Needs the Allure command-line tool; "allure open" serves the report until Ctrl+C
report:
	allure generate $(RESULTS) -o $(HTML_REPORT) --clean
	allure open $(HTML_REPORT)

clean:
	rm -rf reports
