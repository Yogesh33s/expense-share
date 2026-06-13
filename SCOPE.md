# SCOPE: Database Schema and Anomaly Log

## Database Schema Design

### Overview
The shared expenses application uses a relational database to store information about users, groups, expenses, splits, and payments. The schema is designed to handle:
- Dynamic group membership (users joining/leaving over time)
- Multiple split types (equal, unequal, percentage, share)
- Currency conversion (INR/USD)
- Anomaly detection and reporting
- Audit trails for data changes

### Tables

#### 1. users
Stores information about each person in the system.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| name | VARCHAR(100) | NOT NULL, UNIQUE | User's name (normalized) |
| email | VARCHAR(255) | UNIQUE | User's email (for login) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | When user was added |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last update timestamp |

#### 2. groups
Represents a shared expense group (e.g., flatmates sharing a household).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| name | VARCHAR(100) | NOT NULL | Group name (e.g., "Flatmates") |
| description | TEXT | | Group description |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | When group was created |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last update timestamp |

#### 3. group_membership
Tracks when users join and leave groups (many-to-many with temporal aspect).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| group_id | INTEGER | NOT NULL, FOREIGN KEY (groups.id) | Reference to group |
| user_id | INTEGER | NOT NULL, FOREIGN KEY (users.id) | Reference to user |
| joined_at | DATE | NOT NULL | When user joined the group |
| left_at | DATE | NULL | When user left the group (NULL = still member) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | When record was created |

**Constraints:**
- UNIQUE(group_id, user_id, joined_at) - prevents duplicate membership periods
- CHECK(left_is_null OR left_at > joined_at) - ensures valid date ranges

#### 4. expenses
Stores expense records from the CSV and manual entries.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| group_id | INTEGER | NOT NULL, FOREIGN KEY (groups.id) | Associated group |
| paid_by_user_id | INTEGER | NOT NULL, FOREIGN KEY (users.id) | User who paid the expense |
| description | VARCHAR(255) | NOT NULL | Expense description |
| amount | DECIMAL(15, 4) | NOT NULL | Amount paid (positive for expenses, negative for refunds) |
| currency | VARCHAR(3) | NOT NULL, DEFAULT 'INR' | Currency code (INR, USD, etc.) |
| exchange_rate | DECIMAL(10, 4) | NOT NULL, DEFAULT 1.0 | Rate to convert to base currency (INR) |
| amount_base_currency | DECIMAL(15, 4) | NOT NULL | Amount in base currency (INR) |
| date | DATE | NOT NULL | Date of expense |
| split_type | VARCHAR(20) | NOT NULL | How expense is split (equal, unequal, percentage, share) |
| notes | TEXT | | Additional notes |
| is_settlement | BOOLEAN | NOT NULL, DEFAULT 0 | Whether this is a settlement/payment (not a real expense) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | When record was created |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last update timestamp |

**Constraints:**
- CHECK(amount != 0) - zero amounts are anomalies but stored as-is
- CHECK(currency IN ('INR', 'USD')) - or more flexible validation
- CHECK(split_type IN ('equal', 'unequal', 'percentage', 'share'))

#### 5. expense_splits
Stores how each expense is split among users.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| expense_id | INTEGER | NOT NULL, FOREIGN KEY (expenses.id) | Associated expense |
| user_id | INTEGER | NOT NULL, FOREIGN KEY (users.id) | User who owes/is credited |
| share_amount | DECIMAL(15, 4) | NOT NULL | Amount user owes (positive) or is credited (negative) |
| share_percentage | DECIMAL(5, 2) | NULL | Percentage if split_type is percentage |
| share_count | DECIMAL(10, 4) | NULL | Share count if split_type is share |
| calculated_amount | DECIMAL(15, 4) | NOT NULL | Final calculated amount after validation |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | When record was created |

**Constraints:**
- FOREIGN KEY (expense_id, user_id) references appropriate tables
- For equal splits: share_percentage and share_count are NULL
- For unequal splits: share_amount is pre-calculated and stored
- For percentage splits: share_percentage stored, share_amount calculated
- For share splits: share_count stored, share_amount calculated

#### 6. payments
Stores explicit payment/settlement transactions between users.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| group_id | INTEGER | NOT NULL, FOREIGN KEY (groups.id) | Associated group |
| from_user_id | INTEGER | NOT NULL, FOREIGN KEY (users.id) | User paying |
| to_user_id | INTEGER | NOT NULL, FOREIGN KEY (users.id) | User receiving payment |
| amount | DECIMAL(15, 4) | NOT NULL | Amount transferred |
| currency | VARCHAR(3) | NOT NULL, DEFAULT 'INR' | Currency code |
| exchange_rate | DECIMAL(10, 4) | NOT NULL, DEFAULT 1.0 | Rate to convert to base currency |
| amount_base_currency | DECIMAL(15, 4) | NOT NULL | Amount in base currency (INR) |
| date | DATE | NOT NULL | Date of payment |
| description | VARCHAR(255) | NULL | Payment description (e.g., "Rent payment") |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | When record was created |

**Constraints:**
- CHECK(from_user_id != to_user_id) - cannot pay yourself
- CHECK(amount > 0) - payment amounts must be positive

#### 7. import_logs
Tracks CSV import sessions for audit and reporting.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| filename | VARCHAR(255) | NOT NULL | Name of imported file |
| import_started_at | TIMESTAMP | NOT NULL | When import started |
| import_ended_at | TIMESTAMP | NULL | When import ended |
| total_rows | INTEGER | NOT NULL | Total rows in CSV (excluding header) |
| processed_rows | INTEGER | NOT NULL | Rows successfully processed |
| skipped_rows | INTEGER | NOT NULL | Rows skipped due to errors |
| status | VARCHAR(20) | NOT NULL | Status: pending, processing, completed, failed |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | When log was created |

#### 8. import_anomalies
Stores anomalies detected during CSV import.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| import_log_id | INTEGER | NOT NULL, FOREIGN KEY (import_logs.id) | Associated import log |
| row_number | INTEGER | NOT NULL | CSV row number where anomaly occurred (1-based, excluding header) |
| anomaly_type | VARCHAR(50) | NOT NULL | Type of anomaly (see list below) |
| description | TEXT | NOT NULL | Human-readable description |
| severity | VARCHAR(20) | NOT NULL | Severity: info, warning, error, critical |
| original_data | TEXT | NOT NULL | Original CSV row data (JSON format) |
| suggested_fix | TEXT | NULL | Suggested correction (if applicable) |
| was_applied | BOOLEAN | NOT NULL, DEFAULT 0 | Whether the suggested fix was applied |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | When anomaly was logged |

### Anomaly Types
Based on analysis of expenses_export.csv:
- duplicate_entry
- negative_amount (refund)
- zero_amount
- missing_paid_by
- empty_currency
- inconsistent_date_format
- inconsistent_participant_name
- split_type_inconsistency
- malformed_split_details
- settlement_logged_as_expense
- external_person_in_split
- ambiguous_date
- whitespace_issue
- split_details_mismatch
- invalid_equal_split_single_person

### Indexes
For performance optimization:

1. **users**: 
   - INDEX(name) for lookups by name
   - INDEX(email) for login

2. **groups**:
   - INDEX(name) for group lookups

3. **group_membership**:
   - INDEX(group_id, user_id) for membership checks
   - INDEX(user_id, joined_at, left_at) for temporal queries
   - INDEX(group_id, joined_at, left_at) for getting members at a point in time

4. **expenses**:
   - INDEX(group_id, date) for grouping and time-based queries
   - INDEX(paid_by_user_id) for user's expenses
   - INDEX(date) for date-based filtering
   - INDEX(is_settlement) for separating settlements from expenses

5. **expense_splits**:
   - INDEX(expense_id) for fetching splits for an expense
   - INDEX(user_id) for calculating user balances
   - INDEX(expense_id, user_id) for specific lookups

6. **payments**:
   - INDEX(group_id, date) for group payment history
   - INDEX(from_user_id) and INDEX(to_user_id) for user payment flows
   - INDEX(date) for temporal queries

7. **import_logs**:
   - INDEX(created_at) for import history
   - INDEX(status) for monitoring imports

8. **import_anomalies**:
   - INDEX(import_log_id) for import-specific anomalies
   - INDEX(anomaly_type) for anomaly type filtering
   - INDEX(severity) for filtering by severity

### Entity Relationship Description

The database follows a relational model with the following key relationships:

1. **Users ↔ Groups**: Many-to-many through group_membership (with temporal aspect)
   - A user can belong to multiple groups over time
   - A group can have multiple users over time
   - Membership has start and end dates

2. **Groups → Expenses**: One-to-many
   - Each expense belongs to exactly one group
   - A group can have multiple expenses

3. **Users → Expenses**: One-to-many (via paid_by)
   - Each expense is paid by exactly one user
   - A user can pay multiple expenses

4. **Expenses → ExpenseSplits**: One-to-many
   - Each expense is split among one or more users
   - Each split belongs to exactly one expense
   - The sum of all splits should equal the expense amount (within rounding)

5. **Users → ExpenseSplits**: One-to-many
   - Each split is associated with exactly one user
   - A user can have splits across multiple expenses

6. **Groups → Payments**: One-to-many
   - Each payment belongs to exactly one group
   - A group can have multiple payments

7. **Users → Payments**: One-to-many (both from_user_id and to_user_id)
   - Each payment has exactly one sender and one receiver
   - Users can send and receive multiple payments

8. **ImportLogs → ImportAnomalies**: One-to-many
   - Each import session can have multiple anomalies
   - Each anomaly belongs to exactly one import session

### Constraints and Business Rules

1. **Temporal Membership Constraints**:
   - A user cannot have overlapping membership periods in the same group
   - left_at must be after joined_at when not null

2. **Expense Validation**:
   - For non-settlement expenses: at least 2 users involved in split
   - Settlement expenses (is_settlement=1) have special handling
   - Amount must not be zero (zero amounts are flagged as anomalies)

3. **Split Consistency**:
   - For equal splits: all users get equal share
   - For percentage splits: sum of percentages should be 100%
   - For share splits: total shares determine individual amounts
   - For unequal splits: explicit amounts are provided

4. **Currency Handling**:
   - All amounts stored in base currency (INR) for consistency
   - Exchange rates stored per transaction for historical accuracy
   - Original currency and amount preserved for audit

5. **Data Integrity**:
   - Foreign key constraints prevent orphaned records
   - Check constraints validate business rules
   - Unique constraints prevent duplicates where appropriate

### Design Decisions

1. **Base Currency**: Using INR as base currency for all internal calculations
   - Simplifies balance calculations and reporting
   - Exchange rates stored per transaction for historical accuracy

2. **Temporal Membership**: Using joined_at/left_at in group_membership table
   - Accurately reflects when users were responsible for expenses
   - Enables historical reporting ("what was owed in March?")
   - Handles complex scenarios like partial month membership

3. **Separate Settlements Table**: Keeping payments separate from expenses
   - Prevents artificial inflation of expense totals
   - Makes it easier to distinguish between actual spending and money transfers
   - Aligns with user expectations (settlements are not expenses)

4. **Flexible Split Storage**: Storing multiple split-related columns
   - Allows efficient querying without complex calculations
   - Preserves original intent from CSV (percentage, share, etc.)
   - Enables different UI representations

5. **Comprehensive Audit Trail**: Import logs and anomalies tables
   - Full traceability of data import process
   - Enables reporting on data quality issues
   - Supports user review and override of anomaly handling

### ERD Description (Textual)

```
Users 1<->* GroupMembership *<-1 Groups
Groups 1<->* Expenses
Users 1<->* Expenses (paid_by)
Expenses 1<->* ExpenseSplits
Users 1<->* ExpenseSplits (user)
Groups 1<->* Payments
Users 1<->* Payments (from_user)
Users 1<->* Payments (to_user)
ImportLogs 1<->* ImportAnomalies
```

This schema design satisfies all requirements from the assignment:
- Supports dynamic group membership with timestamps
- Handles all split types from the CSV (equal, unequal, percentage, share)
- Tracks both expenses and settlements separately
- Provides foundation for balance calculations and reporting
- Includes comprehensive anomaly detection and logging
- Uses only relational database principles