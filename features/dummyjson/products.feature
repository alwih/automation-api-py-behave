@dummyjson @regression
Feature: Products
  As a shop client
  I want to look up, browse, search and change products
  So that I can rely on the DummyJSON product catalogue

  Background:
    Given the DummyJSON API is available

  @smoke @positive
  Scenario: Get a single product by id
    When I send a GET request to "/products/1"
    Then the response status code should be 200
    And the response header "Content-Type" should contain "application/json"
    And the response should contain the fields "id, title, price, category, stock, rating"
    And the response field "id" should be 1
    And the response field "price" should be greater than 0

  @negative
  Scenario Outline: Requesting product <id> returns 404 (<note>)
    When I send a GET request to "/products/<id>"
    Then the response status code should be 404
    And the response field "message" should be "Product with id '<id>' not found"

    Examples:
      | id  | note               |
      | 0   | below the first id |
      | abc | non-numeric id     |

  @negative
  Scenario: Requesting the id right after the last product returns 404
    The catalogue can grow, so the boundary comes from the current total
    instead of a hard-coded id.

    Given I send a GET request to "/products?limit=1&select=id"
    And I save the response field "total" plus 1 as "next_id"
    When I send a GET request to "/products/{next_id}"
    Then the response status code should be 404
    And the response field "message" should be "Product with id '{next_id}' not found"
