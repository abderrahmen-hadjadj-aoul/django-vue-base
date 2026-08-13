Feature: Registration
  New users create an account and are signed in immediately.

  Background:
    Given I am not logged in

  Scenario: New user creates an account and is logged in
    When I visit the "register" page
    And I fill in "register-email" with "new@example.com"
    And I fill in "register-password" with "s3cret-password"
    And I click "register-submit"
    Then I should be on the "home" page
    And "nav-user-email" should contain "new@example.com"

  Scenario: The dev-only "Create random account" button signs up a random yopmail user
    When I visit the "register" page
    Then I should see "register-random"
    When I click "register-random"
    Then I should be on the "home" page
    And "nav-user-email" should contain "@yopmail.com"

  Scenario: Registering an already-taken email shows an error
    Given a registered user with email "taken@example.com" and password "whatever"
    When I visit the "register" page
    And I fill in "register-email" with "taken@example.com"
    And I fill in "register-password" with "another-pass"
    And I click "register-submit"
    Then I should see "register-error"
    And I should be on the "register" page
