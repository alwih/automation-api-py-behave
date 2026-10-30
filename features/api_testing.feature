@smoke
Feature: JSONPlaceholder API Testing
  As a tester
  I want to test basic API operations
  So that I can verify the API works correctly

  Background:
    Given the API is ready

  Scenario: PUT - Update an existing post
    When I send a PUT request to "/posts/1"
    Then the response status code should be 200
    And the response field "title" should be "Updated Post"

  Scenario: PATCH - Partially update a post
    When I send a PATCH request to "/posts/1"
    Then the response status code should be 200
    And the response field "title" should be "Patched Title"
