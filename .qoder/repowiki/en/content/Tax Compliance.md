# Tax Compliance

<cite>
**Referenced Files in This Document**
- [tax.py](file://app/models/tax.py)
- [seed_data.py](file://app/seed/seed_data.py)
- [payroll.py](file://app/models/payroll.py)
- [employee.py](file://app/models/employee.py)
- [database.py](file://app/database.py)
- [base.py](file://app/models/base.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Conclusion](#conclusion)
10. [Appendices](#appendices)

## Introduction
This document explains the tax compliance subsystem for Indonesian payroll, focusing on:
- PPh Pasal 17 progressive tax calculation
- PTKP (Personal Tax Deduction) management
- Tax bracket configuration aligned with UU HPP 2024
- Tax setting administration
- Integration with payroll processing, employee tax obligations, and monthly tax reporting
- Regulatory compliance and update mechanisms

The system models company-level tax settings, PTKP thresholds, and PPh Pasal 17 tax brackets. It seeds default values for 2024 regulations and supports both PASAL_17 and TER tax calculation methods.

## Project Structure
The tax compliance domain is primarily implemented in the models layer with supporting seed data and database configuration:
- Models define tax-related entities and constraints
- Seed scripts initialize default tax configurations for the current regulation year
- Database configuration enables SQLite with foreign key enforcement

```mermaid
graph TB
subgraph "Models"
TS["TaxSetting<br/>tax_settings"]
PT["PtkpValue<br/>ptkp_values"]
BR["TaxBracketPasal17<br/>tax_brackets_pasal_17"]
TB["TerBracket<br/>ter_brackets"]
end
subgraph "Payroll Integration"
PR["PayrollRun<br/>payroll_runs"]
PS["Payslip<br/>payslips"]
end
subgraph "Employee Data"
E["Employee<br/>employees"]
end
subgraph "Seed & DB"
SD["seed_data.py"]
DB["database.py"]
BM["base.py"]
end
TS --> BR
TS --> TB
PT --> E
PR --> PS
PS --> TS
SD --> TS
SD --> PT
SD --> BR
DB --> BM
```

**Diagram sources**
- [tax.py:19-114](file://app/models/tax.py#L19-L114)
- [payroll.py:19-124](file://app/models/payroll.py#L19-L124)
- [employee.py:76-132](file://app/models/employee.py#L76-L132)
- [seed_data.py:27-63](file://app/seed/seed_data.py#L27-L63)
- [database.py:17-63](file://app/database.py#L17-L63)
- [base.py:18-57](file://app/models/base.py#L18-L57)

**Section sources**
- [tax.py:1-115](file://app/models/tax.py#L1-L115)
- [payroll.py:1-124](file://app/models/payroll.py#L1-L124)
- [employee.py:1-132](file://app/models/employee.py#L1-L132)
- [seed_data.py:1-448](file://app/seed/seed_data.py#L1-L448)
- [database.py:1-63](file://app/database.py#L1-L63)
- [base.py:1-57](file://app/models/base.py#L1-L57)

## Core Components
- TaxSetting: Stores company-level tax method selection (PASAL_17 or TER) and activation status.
- PtkpValue: Defines PTKP thresholds per employee status (TK/0, TK/1, etc.) with monthly and annual amounts, regulation year, and effective dates.
- TaxBracketPasal17: Progressive tax brackets for PPh Pasal 17 with ordered ranges and rates, including an unbounded upper bound for the top bracket.
- TerBracket: Simplified TER brackets categorized by A/B/C with income ranges and rates.
- PayrollRun and Payslip: Integrate tax computation into monthly payroll runs and individual payslips, capturing computed tax and totals.
- Employee: Holds employee PTKP status and personal identifiers used in tax computations.

Key constraints and indexes ensure data integrity and efficient lookups:
- Enumerated method values and statuses
- Unique constraints for active configurations per company and date
- Indexed active rows for fast retrieval

**Section sources**
- [tax.py:19-114](file://app/models/tax.py#L19-L114)
- [payroll.py:19-124](file://app/models/payroll.py#L19-L124)
- [employee.py:76-132](file://app/models/employee.py#L76-L132)

## Architecture Overview
The tax compliance architecture separates configuration from computation:
- Configuration layer: TaxSetting, PtkpValue, TaxBracketPasal17, TerBracket
- Computation layer: Not present in code; tax calculation logic is externalized (see Implementation Notes)
- Integration layer: PayrollRun and Payslip persist computed tax and totals
- Data lifecycle: Seed scripts populate default configurations; runtime queries select active configurations by company and effective date

```mermaid
sequenceDiagram
participant Admin as "Admin/User"
participant DB as "Database"
participant Seed as "Seed Script"
participant Payroll as "Payroll Engine"
participant Emp as "Employee"
Admin->>DB : Configure TaxSetting (method, active)
Admin->>DB : Configure PtkpValue (status, amounts, dates)
Admin->>DB : Configure TaxBracketPasal17 (ranges, rates, dates)
Seed->>DB : Seed default TaxSetting (PASAL_17)
Seed->>DB : Seed default PtkpValue (2024)
Seed->>DB : Seed default TaxBrackets (2024)
Emp->>DB : Retrieve PTKP status
Payroll->>DB : Query active TaxSetting
Payroll->>DB : Query active PtkpValue for status
Payroll->>DB : Query active TaxBracketPasal17 for period
Payroll->>Payroll : Compute tax (progressive)
Payroll->>DB : Persist PayrollRun and Payslip with tax
```

**Diagram sources**
- [seed_data.py:412-430](file://app/seed/seed_data.py#L412-L430)
- [seed_data.py:224-260](file://app/seed/seed_data.py#L224-L260)
- [seed_data.py:263-296](file://app/seed/seed_data.py#L263-L296)
- [tax.py:19-114](file://app/models/tax.py#L19-L114)
- [payroll.py:19-124](file://app/models/payroll.py#L19-L124)
- [employee.py:76-132](file://app/models/employee.py#L76-L132)

## Detailed Component Analysis

### PPh Pasal 17 Progressive Tax Calculation
The system stores progressive tax brackets and selects the applicable bracket based on taxable income. The algorithm proceeds as follows:
- Determine the employee’s monthly taxable income after allowances and PTKP deduction
- Select active PPh Pasal 17 brackets effective during the payroll period
- Apply the progressive formula: cumulative tax from lower brackets plus marginal tax on the portion exceeding the lowest threshold of the selected bracket

```mermaid
flowchart TD
Start(["Compute PPh Pasal 17"]) --> Income["Calculate Monthly Taxable Income"]
Income --> LoadBrackets["Load Active PPh Pasal 17 Brackets"]
LoadBrackets --> FindBracket{"Find Bracket Containing Income"}
FindBracket --> |Not Found| Error["No Matching Bracket"]
FindBracket --> |Found| Calc["Compute Tax = Base Tax + (Income - Min) * Rate"]
Calc --> Round["Round to Currency Unit"]
Round --> End(["Return Tax Amount"])
Error --> End
```

**Diagram sources**
- [tax.py:63-85](file://app/models/tax.py#L63-L85)
- [payroll.py:64-102](file://app/models/payroll.py#L64-L102)

**Section sources**
- [tax.py:63-85](file://app/models/tax.py#L63-L85)
- [payroll.py:64-102](file://app/models/payroll.py#L64-L102)

### PTKP Management
PTKP values are stored per employee status and regulation year. The system:
- Maintains monthly and annual PTKP amounts
- Supports effective dates to manage regulatory updates
- Uses employee PTKP status to select the appropriate threshold

```mermaid
classDiagram
class PtkpValue {
+int id
+int company_id
+string ptkp_code
+string description
+numeric annual_amount
+numeric monthly_amount
+int regulation_year
+date effective_date
+date end_date
+boolean is_active
}
class Employee {
+int id
+int company_id
+string ptkp_status
+string npwp
}
Employee --> PtkpValue : "selects by ptkp_status and effective_date"
```

**Diagram sources**
- [tax.py:37-60](file://app/models/tax.py#L37-L60)
- [employee.py:76-132](file://app/models/employee.py#L76-L132)

**Section sources**
- [tax.py:37-60](file://app/models/tax.py#L37-L60)
- [employee.py:76-132](file://app/models/employee.py#L76-L132)

### Tax Bracket Configuration
Brackets are configured with ordered ranges and rates. The seed script initializes 2024 brackets aligned with UU HPP. Effective dates enable phased updates.

```mermaid
erDiagram
TAX_SETTINGS {
int id PK
int company_id
string tax_calculation_method
boolean is_active
}
TAX_BRACKETS_PASAL_17 {
int id PK
int company_id
int bracket_order
numeric income_range_min
numeric income_range_max
numeric tax_rate
int regulation_year
date effective_date
date end_date
boolean is_active
}
TAX_SETTINGS ||--o{ TAX_BRACKETS_PASAL_17 : "company-specific"
```

**Diagram sources**
- [tax.py:19-34](file://app/models/tax.py#L19-L34)
- [tax.py:63-85](file://app/models/tax.py#L63-L85)

**Section sources**
- [tax.py:63-85](file://app/models/tax.py#L63-L85)
- [seed_data.py:263-296](file://app/seed/seed_data.py#L263-L296)

### Tax Setting Administration
TaxSetting defines the company-wide method (PASAL_17 or TER) and activation flag. The seed script sets a default PASAL_17 configuration.

```mermaid
classDiagram
class TaxSetting {
+int id
+int company_id
+string tax_calculation_method
+boolean is_active
}
```

**Diagram sources**
- [tax.py:19-34](file://app/models/tax.py#L19-L34)
- [seed_data.py:412-430](file://app/seed/seed_data.py#L412-L430)

**Section sources**
- [tax.py:19-34](file://app/models/tax.py#L19-L34)
- [seed_data.py:412-430](file://app/seed/seed_data.py#L412-L430)

### Integration with Payroll and Employee Tax Obligations
PayrollRun and Payslip capture computed taxes and totals. The system persists:
- Gross and net salaries
- Tax amounts per payslip
- Period-level aggregates for reporting

```mermaid
sequenceDiagram
participant Run as "PayrollRun"
participant Slip as "Payslip"
participant Emp as "Employee"
participant Tax as "TaxEngine"
Emp->>Run : Participates in payroll period
Run->>Slip : Generates payslip entries
Tax->>Slip : Computes PPh Pasal 17 tax
Slip->>Run : Updates totals (tax, net)
Run->>Run : Aggregates company totals
```

**Diagram sources**
- [payroll.py:19-124](file://app/models/payroll.py#L19-L124)
- [tax.py:19-114](file://app/models/tax.py#L19-L114)

**Section sources**
- [payroll.py:19-124](file://app/models/payroll.py#L19-L124)
- [tax.py:19-114](file://app/models/tax.py#L19-L114)

### Monthly Tax Reporting
Monthly reporting is supported by:
- PayrollRun aggregation fields (total_tax, total_gross, total_net)
- Payslip tax fields for individual transparency
- Status tracking for run lifecycle (DRAFT, PROCESSING, COMPLETED, APPROVED, PAID)

**Section sources**
- [payroll.py:19-61](file://app/models/payroll.py#L19-L61)
- [payroll.py:64-102](file://app/models/payroll.py#L64-L102)

## Dependency Analysis
The models rely on shared mixins for timestamps and soft deletes. Database configuration enforces foreign keys for SQLite compatibility.

```mermaid
graph LR
Base["TimestampMixin<br/>base.py"] --> TS["TaxSetting"]
Base --> PT["PtkpValue"]
Base --> BR["TaxBracketPasal17"]
Base --> TB["TerBracket"]
DB["database.py"] --> Engine["SQLAlchemy Engine"]
Engine --> TS
Engine --> PT
Engine --> BR
Engine --> TB
```

**Diagram sources**
- [base.py:23-57](file://app/models/base.py#L23-L57)
- [database.py:17-63](file://app/database.py#L17-L63)
- [tax.py:16-16](file://app/models/tax.py#L16-L16)

**Section sources**
- [base.py:1-57](file://app/models/base.py#L1-L57)
- [database.py:1-63](file://app/database.py#L1-L63)
- [tax.py:11-16](file://app/models/tax.py#L11-L16)

## Performance Considerations
- Indexes on active configurations and effective dates optimize bracket and PTKP lookups
- Unique constraints prevent duplicate active configurations per company and date
- Use of Decimal types ensures precise monetary calculations
- Consider caching active configurations per company and period to reduce repeated queries

## Troubleshooting Guide
Common issues and resolutions:
- No active tax brackets found: Verify effective dates and is_active flags; ensure seed data was applied for the target regulation year
- Incorrect PTKP amount: Confirm employee ptkp_status matches available PtkpValue entries for the payroll period
- Tax method mismatch: Check TaxSetting for the company; ensure PayrollRun.tax_method aligns with company setting
- Payroll totals inconsistent: Review PayrollRun aggregation fields and ensure all payslips are included in the run

**Section sources**
- [tax.py:29-34](file://app/models/tax.py#L29-L34)
- [tax.py:54-60](file://app/models/tax.py#L54-L60)
- [tax.py:79-85](file://app/models/tax.py#L79-L85)
- [payroll.py:46-61](file://app/models/payroll.py#L46-L61)

## Conclusion
The tax compliance subsystem provides a robust foundation for Indonesian payroll tax management:
- Clear separation of configuration (TaxSetting, PtkpValue, TaxBracketPasal17) and integration (PayrollRun, Payslip)
- Regulatory alignment with UU HPP 2024 through seeded defaults
- Extensible design supporting future regulatory updates via effective dates and unique constraints

## Appendices

### Concrete Examples

- Example: Tax Setting Update
  - Update company-wide method to PASAL_17 or TER
  - Path: [seed_data.py:412-430](file://app/seed/seed_data.py#L412-L430)

- Example: PTKP Configuration
  - Add or modify PTKP values for a new regulation year
  - Path: [seed_data.py:224-260](file://app/seed/seed_data.py#L224-L260)

- Example: Bracket Adjustments
  - Insert new PPh Pasal 17 brackets with ordered ranges and rates
  - Path: [seed_data.py:263-296](file://app/seed/seed_data.py#L263-L296)

- Example: Tax Computation Result
  - After processing, PayrollRun and Payslip reflect computed tax and totals
  - Path: [payroll.py:19-124](file://app/models/payroll.py#L19-L124)

- Example: Regulatory Compliance
  - Effective dates and unique constraints ensure only one active configuration per company and date
  - Paths: [tax.py:54-60](file://app/models/tax.py#L54-L60), [tax.py:79-85](file://app/models/tax.py#L79-L85), [tax.py:104-114](file://app/models/tax.py#L104-L114)