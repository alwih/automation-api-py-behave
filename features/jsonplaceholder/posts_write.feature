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
