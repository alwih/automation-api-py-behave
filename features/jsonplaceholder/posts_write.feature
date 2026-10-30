@jsonplaceholder @regression
Feature: Writing posts
  As an API consumer
  I want to create, update and delete posts
  So that I know how the posts endpoints handle writes

  JSONPlaceholder fakes writes: the responses look real, but nothing is stored.

  Background:
    Given the API is ready

  @smoke @positive
  Scenario: Create a post
    When I send a POST request to "/posts" with:
      | field  | value                |
      | title  | Weekly release notes |
      | body   | Bug fixes and polish |
      | userId | 1                    |
    Then the response status code should be 201
    And the response should echo the request body
    And the response field "id" should be an integer
    And the response field "id" should be greater than 100

  @edge
  Scenario: Non-ASCII text survives a create round-trip
    When I send a POST request to "/posts" with:
      | field  | value         |
      | title  | Café ☕ 日本語 |
      | body   | Ünïcödé body  |
      | userId | 1             |
    Then the response status code should be 201
    And the response field "title" should be "Café ☕ 日本語"
    And the response should echo the request body

  @positive
  Scenario: Replace a post with PUT
    When I send a PUT request to "/posts/1" with:
      | field  | value           |
      | id     | 1               |
      | title  | Rewritten title |
      | body   | Rewritten body  |
      | userId | 1               |
    Then the response status code should be 200
    And the response should echo the request body

  @positive
  Scenario: PATCH changes only the fields that are sent
    Given I send a GET request to "/posts/1"
    And I remember the response body
    When I send a PATCH request to "/posts/1" with:
      | field | value         |
      | title | Patched title |
    Then the response status code should be 200
    And the response should echo the request body
    And the response fields "id, userId, body" should match the remembered body

  @edge
  Scenario: PUT with a partial body replaces the whole post
    PUT is a full replace, so fields left out of the request are dropped
    instead of being kept from the stored post.

    When I send a PUT request to "/posts/1" with:
      | field | value        |
      | title | Only a title |
    Then the response status code should be 200
    And the response should echo the request body
    And the response should not contain "body"
    And the response should not contain "userId"
