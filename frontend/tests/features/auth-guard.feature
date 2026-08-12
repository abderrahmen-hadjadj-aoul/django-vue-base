Feature: Route authentication guard
  Protected routes require a session; the auth pages are off-limits once
  you're signed in.

  Scenario: Anonymous visitor is redirected away from the home page
    Given I am not logged in
    When I visit the "home" page
    Then I should be on the "login" page
    And I should not see "main-nav"

  Scenario: Anonymous visitor is redirected away from the account page
    Given I am not logged in
    When I visit the "account" page
    Then I should be on the "login" page

  Scenario: Authenticated user is bounced off the login page
    Given I am logged in as "user@example.com"
    When I visit the "login" page
    Then I should be on the "home" page
