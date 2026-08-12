Feature: Login
  Existing users sign in with email + password and land on the home page.

  Background:
    Given I am not logged in
    And a registered user with email "user@example.com" and password "correct-horse"

  Scenario: Successful login lands on the home page
    When I visit the "login" page
    And I fill in "login-email" with "user@example.com"
    And I fill in "login-password" with "correct-horse"
    And I click "login-submit"
    Then I should be on the "home" page
    And I should see "main-nav"
    And "nav-user-email" should contain "user@example.com"

  Scenario: Wrong password shows an error and stays on the login page
    When I visit the "login" page
    And I fill in "login-email" with "user@example.com"
    And I fill in "login-password" with "wrong-password"
    And I click "login-submit"
    Then I should see "login-error"
    And "login-error" should contain "Invalid email or password."
    And I should be on the "login" page
