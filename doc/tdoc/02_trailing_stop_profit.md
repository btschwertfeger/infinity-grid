# Trailing Stop Profit Concept

Concept: Optional Custom Trailing Stop Profit

Scenario:

Amount per grid: 100 €
Interval: 2 %

```
When a buy order at 100 € is executed
  Then place a sell order O1 at 104 € (2x interval)

  When the price falls to or below 100 €
    Then do nothing

  When the price reaches 103 € (1.5x interval)
    Then remember to sell at 102 € in case the price drops (1x interval from buy price)
    And cancel the sell order O1 at 104 €
    And place a sell order O2 at 105 € (buy price * 2.5x interval)

    When the price falls to or below 102 €
      Then cancel O2
      And create limit sell order at 102 €
      END

    When the price rises to 104 € (2x interval of buy price)
      Then remember to sell at 103 € in case the price drops (1.5x interval from buy price)
      And cancel the sell order O2
      And place a sell order O3 at 106 € (current price * 3x interval)

      When the price rises to 105 € (2.5x interval of buy price)
        Then remember to sell at 104 € in case the price drops (2x interval from buy price)
        And cancel the sell order O2
        And place a sell order O4 at 107 € (buy price * 3.5x interval)

        When the price falls to 104 € (2x interval of buy price)
          Then cancel the sell order O4
          And place a limit sell order at 104 €
          END
      END
    END
  END
```
