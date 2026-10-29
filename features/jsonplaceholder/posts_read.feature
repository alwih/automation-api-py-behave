@jsonplaceholder @regression
Feature: Reading posts
  As an API consumer
  I want to read posts and their comments
  So that I can trust what the posts endpoints return

  Background:
    Given the API is ready

  @smoke @positive
  Scenario: Get a single post by id
    When I send a GET request to "/posts/1"
    Then the response status code should be 200
    And the response header "Content-Type" should contain "application/json"
    And the response field "id" should be 1
    And the response field "userId" should be an integer
    And the response field "title" should be a non-empty string
    And the response field "body" should be a non-empty string

  @positive
  Scenario: List all posts
    When I send a GET request to "/posts"
    Then the response status code should be 200
    And the response body should be a list of 100 items
    And every item in the response should have the fields "userId, id, title, body"

  @positive
  Scenario Outline: Filter posts by author <user_id> (<note>)
    When I send a GET request to "/posts?userId=<user_id>"
    Then the response status code should be 200
    And the response body should be a list of 10 items
    And every item in the response should have "userId" equal to <user_id>

    Examples:
      | user_id | note        |
      | 1       | first user  |
      | 5       | middle user |
      | 10      | last user   |

  @positive
  Scenario: Get the comments of a post
    When I send a GET request to "/posts/1/comments"
    Then the response status code should be 200
    And the response body should be a list of 5 items
    And every item in the response should have "postId" equal to 1
    And every item in the response should have "email" containing "@"

  @positive
  Scenario: Nested comments route matches the postId filter
    Given I send a GET request to "/comments?postId=1"
    And I remember the response body
    When I send a GET request to "/posts/1/comments"
    Then the response status code should be 200
    And the response body should equal the remembered body
