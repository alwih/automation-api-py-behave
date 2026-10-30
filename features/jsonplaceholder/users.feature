@jsonplaceholder @regression
Feature: Reading users
  As an API consumer
  I want to read users, including their nested address and company
  So that I can rely on the shape of a user record

  Background:
    Given the API is ready

  @positive
  Scenario: Get a user with nested address and company
    When I send a GET request to "/users/1"
    Then the response status code should be 200
    And the response field "id" should be 1
    And the response field "address.city" should be "Gwenborough"
    And the response field "address.geo.lat" should be "-37.3159"
    And the response field "address.geo.lng" should be "81.1496"
    And the response field "company.name" should be a non-empty string

  @positive
  Scenario: Every user has a location and a company
    When I send a GET request to "/users"
    Then the response status code should be 200
    And the response body should be a list of 10 items
    And every item in the response should have the fields "address.geo.lat, address.geo.lng, company.name"

  @negative
  Scenario: Requesting a user beyond the last one returns 404
    When I send a GET request to "/users/11"
    Then the response status code should be 404
    And the response body should be an empty object
