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

  @positive
  Scenario: Paginate products with limit and skip
    When I send a GET request to "/products?limit=5&skip=10"
    Then the response status code should be 200
    And the "id" values in the "products" list should be 11, 12, 13, 14, 15
    And the response field "skip" should be 10
    And the response field "limit" should be 5
    And the response field "total" should be greater than 0

  @positive
  Scenario Outline: Sort products by price in <direction> order
    When I send a GET request to "/products?sortBy=price&order=<order>"
    Then the response status code should be 200
    And the "products" list should be sorted by "price" in <direction> order

    Examples:
      | order | direction  |
      | asc   | ascending  |
      | desc  | descending |

  @positive
  Scenario: Select only some product fields
    When I send a GET request to "/products?select=title,price"
    Then the response status code should be 200
    And every item in the "products" list should have exactly the fields "id, title, price"

  @negative
  Scenario Outline: A limit of <limit> is rejected (<note>)
    When I send a GET request to "/products?limit=<limit>"
    Then the response status code should be 400
    And the response field "message" should be "Invalid 'limit' - should be a positive number"

    Examples:
      | limit | note         |
      | -1    | negative     |
      | abc   | not a number |

  @negative
  Scenario: An unknown sort order is rejected
    When I send a GET request to "/products?sortBy=price&order=sideways"
    Then the response status code should be 400
    And the response field "message" should be "Invalid 'order' - should be either 'asc' or 'desc'"

  @edge
  Scenario: A limit of 0 returns every product
    When I send a GET request to "/products?limit=0"
    Then the response status code should be 200
    And the response field "limit" should equal the response field "total"
    And the "products" list should have as many items as the response field "total"

  @edge
  Scenario: Skipping past the end returns an empty page
    When I send a GET request to "/products?skip=1000"
    Then the response status code should be 200
    And the "products" list should be empty
    And the response field "limit" should be 0

  @positive
  Scenario: Search finds products by title or description
    The search also matches descriptions, so checking titles alone would fail.

    When I send a GET request to "/products/search?q=phone"
    Then the response status code should be 200
    And the response field "total" should be greater than 0
    And every item in the "products" list should contain "phone" in any of "title, description", ignoring case

  @positive
  Scenario: Filter products by category
    When I send a GET request to "/products/category/smartphones"
    Then the response status code should be 200
    And every item in the "products" list should have "category" equal to "smartphones"

  @edge
  Scenario: Search ignores the case of the query
    Given I send a GET request to "/products/search?q=phone"
    And I remember the response body
    When I send a GET request to "/products/search?q=PHONE"
    Then the response status code should be 200
    And the response body should equal the remembered body

  @edge
  Scenario: A search with no matches returns an empty result
    When I send a GET request to "/products/search?q=zzqqxx"
    Then the response status code should be 200
    And the "products" list should be empty
    And the response field "total" should be 0

  @edge
  Scenario: An unknown category returns an empty list, not a 404
    When I send a GET request to "/products/category/flying-cars"
    Then the response status code should be 200
    And the "products" list should be empty
