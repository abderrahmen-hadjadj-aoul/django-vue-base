Feature: Account — change password
  Signed-in users can see their identity and change their password.

  Background:
    Given I am logged in as "user@example.com"

  Scenario: The signed-in email is shown
    When I visit the "account" page
    Then "account-email" should contain "user@example.com"

  Scenario: Changing the password shows a success message
    When I visit the "account" page
    And I fill in my current password
    And I fill in "account-new-password" with "brand-new-password"
    And I click "account-submit"
    Then I should see "account-message"
    And "account-message" should contain "Password updated."
