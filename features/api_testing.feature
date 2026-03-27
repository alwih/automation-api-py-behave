Feature: JSONPlaceholder API Testing
  As a tester
  I want to test basic API operations
  So that I can verify the API works correctly

  Scenario: GET - Retrieve a single post
    Given the API is ready
    When I send a GET request to "/posts/1"
    Then the response status code should be 200
    And the response should contain "userId"
    And the response should contain "title"

  Scenario: POST - Create a new post
    Given the API is ready
    When I send a POST request to "/posts"
    Then the response status code should be 201
    And the response should contain "id"

  Scenario: PUT - Update an existing post
    Given the API is ready
    When I send a PUT request to "/posts/1"
    Then the response status code should be 200
    And the response field "title" should be "Updated Post"

  Scenario: PATCH - Partially update a post
    Given the API is ready
    When I send a PATCH request to "/posts/1"
    Then the response status code should be 200
    And the response field "title" should be "Patched Title"
