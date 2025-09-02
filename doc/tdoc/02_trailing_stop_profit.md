# Trailing Stop Profit Concept

Concept: Optional Custom Trailing Stop Profit

In order to increase profits by letting them run beyond the defined interval, we
could implement a custom trailing stop profit mechanism.

This mechanism ensures that the profit made by a trade is at least based on the
defined interval or better. This "_or better_" can be realized by letting
profits run $x$% beyond the defined interval and then lock in profits, in case
the price come back down.

## Parameters

- Amount per grid: 100 €
- Interval: 2 %
- TSTP: 1 %

## Gherkin Specification

```gherkin
Feature: Trailing Stop Profit
  As a trader
  I want to implement a trailing stop profit mechanism
  So that I can maximize profits when the price trends upward

  Background:
    Given the grid amount is 100 €
    And the interval is 2 %

  Scenario: Managing buy order with trailing stop profit
    When a buy order at 100 € is executed
    Then a sell order O1 is placed at 104 € (interval + 2x TSTP)

    Scenario: Price falls to or below buy price
      Given a buy order at 100 € was executed
      And a sell order O1 exists at 104 €
      When the price falls to or below 100 €
      Then no action is taken

    Scenario: Price reaches 103 € (interval + TSTP)
      Given a buy order at 100 € was executed
      And a sell order O1 exists at 104 €
      When the price reaches 103 € (interval + TSTP)
      Then the system remembers to sell at 102 € in case the price drops
      And the sell order O1 at 104 € is canceled
      And a new sell order O2 is placed at 105 € (interval + 3x TSTP)

      Scenario: Price falls after reaching 103 € (interval + TSTP)
        Given the price reached 103 €
        And a sell order O2 exists at 105 €
        When the price falls to or below 102 €
        Then the sell order O2 is canceled
        And a limit sell order is created at 102 €

      Scenario: Price rises to 104 € (interval + 2x TSTP)
        Given the price reached 103 €
        And a sell order O2 exists at 105 €
        When the price rises to 104 € (interval + 2TSTP)
        Then the system remembers to sell at 103 € in case the price drops
        And the sell order O2 is canceled
        And a new sell order O3 is placed at 106 € (interval + 4x TSTP)

        Scenario: Price rises to 106 € (interval + 4 TSTP)
          Given the price reached 104 €
          And a sell order O3 exists at 106 €
          When the price rises to 105 € (interval + 3 TSTP)
          Then the system remembers to sell at 104 € in case the price drops
          And the sell order O3 is canceled
          And a new sell order O4 is placed at 107 € (interval + 4x TSTP)

          Scenario: Price falls after reaching 105 € (interval + 3x TSTP)
            Given the price reached 105 €
            And a sell order O4 exists at 107 €
            When the price falls to 104 € (interval + 2x TSTP)
            Then the sell order O4 is canceled
            And a limit sell order is created at 104 €
```
