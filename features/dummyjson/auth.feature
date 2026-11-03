@dummyjson @auth @regression @authenticated
Feature: Authentication
  As a DummyJSON client
  I want to log in and call protected endpoints with a bearer token
  So that only authenticated requests reach user data

  Scenarios log in as DUMMYJSON_USERNAME / DUMMYJSON_PASSWORD (see .env.example).
  Requests keep no cookies, so only the Authorization header can authenticate them.

  Background:
    Given the DummyJSON API is available

  @smoke @positive
  Scenario: Log in with valid credentials
    When I log in as the configured user
    Then the response status code should be 200
    And the response field "accessToken" should be a JWT
    And the response field "refreshToken" should be a JWT
    And the response field "username" should be "{username}"
    And the response field "id" should be an integer
    And the response should not contain "password"

  @positive
  Scenario Outline: The access token lasts <minutes> minutes when asked to
    When I log in as the configured user with:
      | field         | value     |
      | expiresInMins | <minutes> |
    Then the response status code should be 200
    And the "accessToken" JWT should expire <minutes> minutes after it was issued

    Examples:
      | minutes |
      | 1       |
      | 30      |

  @positive
  Scenario: The profile endpoint returns the logged-in user
    Given I am logged in
    When I send a GET request to "/auth/me"
    Then the response status code should be 200
    And the response field "id" should equal the saved "user_id"

  @positive
  Scenario: A protected product route accepts the bearer token
    Given I am logged in
    When I send a GET request to "/auth/products/1"
    Then the response status code should be 200
    And the response field "id" should be 1

  @positive
  Scenario: Refreshing returns new tokens that work
    Given I am logged in
    When I send a POST request to "/auth/refresh" with:
      | field        | value           |
      | refreshToken | {refresh_token} |
    Then the response status code should be 200
    And the response field "accessToken" should be a JWT
    And the response field "refreshToken" should be a JWT
    When I use the access token from the response
    And I send a GET request to "/auth/me"
    Then the response status code should be 200
    And the response field "id" should equal the saved "user_id"
