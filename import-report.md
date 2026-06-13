# Import Report
**Generated:** 2026-06-13T20:07:01.100398

## Summary
- **Total Rows Processed:** 42
- **Valid Rows:** 41
- **Invalid Rows:** 1
- **Success Rate:** 97.62%

## Anomaly Summary
### By Severity
- **Critical:** 1
- **Error:** 1
- **Warning:** 3
- **Info:** 1

### By Type
- invalid_date_format: 1
- missing_paid_by: 1
- negative_amount_refund: 1
- percentage_sum_not_100: 2
- zero_amount: 1
- **Total Anomalies:** 6

## Detailed Anomalies
| Row | Type | Severity | Description | Original Value | Suggested Fix | Field |
|-----|------|----------|-------------|----------------|---------------|-------|
| 13 | missing_paid_by | critical | Paid by field is empty |  |  | paid_by |
| 15 | percentage_sum_not_100 | warning | Percentage sum is 110.0%, expected 100% | Aisha 30%; Rohan 30%; Priya 30%; Meera 20% | Adjust percentages to sum to 100% | split_details |
| 26 | negative_amount_refund | info | Expense amount is negative (refund) | -30.0 |  | amount |
| 27 | invalid_date_format | error | Could not parse date | Mar 14 |  | date |
| 31 | zero_amount | warning | Expense amount is zero | 0.0 |  | amount |
| 32 | percentage_sum_not_100 | warning | Percentage sum is 110.0%, expected 100% | Aisha 30%; Rohan 30%; Priya 30%; Meera 20% | Adjust percentages to sum to 100% | split_details |

## Rows with Issues
6 rows had issues:
- **Row 13:**
  - missing_paid_by (critical): Paid by field is empty
- **Row 15:**
  - percentage_sum_not_100 (warning): Percentage sum is 110.0%, expected 100%
- **Row 26:**
  - negative_amount_refund (info): Expense amount is negative (refund)
- **Row 27:**
  - invalid_date_format (error): Could not parse date
- **Row 31:**
  - zero_amount (warning): Expense amount is zero
- **Row 32:**
  - percentage_sum_not_100 (warning): Percentage sum is 110.0%, expected 100%

## Import Statistics
- **Processing Duration Ms:** 0
- **Parser Version:** 1.0
- **Validation Rules Applied:** 9
- **Base Currency:** INR
