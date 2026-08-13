Feature: Home dashboard
  The protected home view reports backend health and manages items.

  Background:
    Given I am logged in as "user@example.com"

  Scenario: A healthy backend shows an "ok" badge
    Given the backend health is "ok"
    When I visit the "home" page
    Then "health-status" should contain "ok"

  Scenario: Empty state when there are no items
    When I visit the "home" page
    Then I should see "item-empty"
    And I should see 0 items

  Scenario: Pre-existing items are listed
    Given an item named "Buy milk" already exists
    When I visit the "home" page
    Then I should see 1 item
    And the item list should contain "Buy milk"

  Scenario: Another user's items are not visible
    Given an item named "Buy milk" already exists
    And an item named "Their secret" owned by "someone-else@example.com" already exists
    When I visit the "home" page
    Then I should see 1 item
    And the item list should contain "Buy milk"

  Scenario: Adding an item appends it to the list
    When I visit the "home" page
    And I fill in "item-name" with "Write tests"
    And I click "item-add"
    Then I should see 1 item
    And the item list should contain "Write tests"
