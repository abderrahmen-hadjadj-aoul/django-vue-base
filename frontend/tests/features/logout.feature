Feature: Logout
  Signing out clears the session and returns to the login page.

  Scenario: Logging out returns to the login page
    Given I am logged in as "user@example.com"
    When I visit the "home" page
    And I click "logout-button"
    Then I should be on the "login" page
    And I should not see "main-nav"
