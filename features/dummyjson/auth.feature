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
    And the response should not contain "password"
    And the response should match the "auth_login" schema

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

  @negative
  Scenario Outline: Wrong credentials get the same message either way (<case>)
    A wrong password and an unknown user get the same answer, so the
    response doesn't reveal which usernames exist.

    When I log in as the configured user with:
      | field   | value   |
      | <field> | <value> |
    Then the response status code should be 400
    And the response field "message" should be "Invalid credentials"
    And the response should match the "error" schema

    Examples:
      | case           | field    | value            |
      | wrong password | password | not-the-password |
      | unknown user   | username | no-such-user-xyz |

  @negative
  Scenario: Logging in without a password is rejected
    When I send a POST request to "/auth/login" with:
      | field    | value   |
      | username | someone |
    Then the response status code should be 400
    And the response field "message" should be "Username and password required"
    And the response should match the "error" schema

  @negative
  Scenario: Logging in with an empty body is rejected
    When I send a POST request to "/auth/login" with:
      | field | value |
    Then the response status code should be 400
    And the response field "message" should be "Username and password required"
    And the response should match the "error" schema

  @negative
  Scenario: The profile endpoint requires a token
    When I send a GET request to "/auth/me"
    Then the response status code should be 401
    And the response field "message" should be "Access Token is required"
    And the response should match the "error" schema

  @negative
  Scenario: The profile endpoint rejects a non-bearer token
    Given I set the header "Authorization" to "Basic abc"
    When I send a GET request to "/auth/me"
    Then the response status code should be 401
    And the response field "message" should be "Invalid/Expired Token!"
    And the response should match the "error" schema

  @negative
  Scenario: Refreshing without a refresh token is rejected
    When I send a POST request to "/auth/refresh" with:
      | field | value |
    Then the response status code should be 401
    And the response field "message" should be "Refresh token required"
    And the response should match the "error" schema

  @negative
  Scenario: Refreshing with an invalid refresh token is rejected
    When I send a POST request to "/auth/refresh" with:
      | field        | value |
      | refreshToken | abc   |
    Then the response status code should be 403
    And the response field "message" should be "Invalid refresh token"
    And the response should match the "error" schema

  @negative
  Scenario: A protected product route requires a token
    When I send a GET request to "/auth/products/1"
    Then the response status code should be 401
    And the response field "message" should be "Access Token is required"
    And the response should match the "error" schema

  @edge
  Scenario: Usernames are matched without regard to case
    When I log in as the configured user with the username in upper case
    Then the response status code should be 200
    And the response field "username" should be "{username}"

  @known_issue @security
  Scenario: A malformed bearer token is rejected with 401
    Actual: DummyJSON answers 500 with {"message": "invalid token"}.

    Given I set the header "Authorization" to "Bearer not.a.jwt"
    When I send a GET request to "/auth/me"
    Then the response status code should be 401

  @known_issue @security
  Scenario: A token with a tampered signature is rejected with 401
    Actual: DummyJSON answers 500 with {"message": "invalid signature"}.

    Given I am logged in
    And I save a copy of "access_token" with a tampered signature as "tampered_token"
    And I set the header "Authorization" to "Bearer {tampered_token}"
    When I send a GET request to "/auth/me"
    Then the response status code should be 401

  @known_issue @security
  Scenario: The profile response does not expose the password
    Actual: /auth/me returns the user's password in plain text.

    Given I am logged in
    When I send a GET request to "/auth/me"
    Then the response status code should be 200
    And the response should not contain "password"
