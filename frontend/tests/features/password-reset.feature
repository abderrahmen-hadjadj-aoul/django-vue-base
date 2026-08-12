Feature: Password reset
  Users can request a reset link and set a new password from the emailed link.

  Scenario: Requesting a reset link shows a confirmation message
    Given a registered user with email "user@example.com" and password "correct-horse"
    When I visit the "forgot password" page
    And I fill in "forgot-email" with "user@example.com"
    And I click "forgot-submit"
    Then I should see "forgot-message"
    And "forgot-message" should contain "reset link has been sent"

  Scenario: Opening a valid reset link lets me set a new password
    Given a registered user with email "user@example.com" and password "correct-horse"
    When I open the password reset link for "user@example.com"
    And I fill in "reset-password" with "brand-new-password"
    And I click "reset-submit"
    Then I should see "reset-message"
    And "reset-message" should contain "Password has been reset."

  Scenario: A reset link missing its token is rejected
    When I visit the "reset password" page
    Then I should see "reset-missing-token"
