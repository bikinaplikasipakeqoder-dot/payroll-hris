# API Reference

<cite>
**Referenced Files in This Document**
- [requirements.txt](file://requirements.txt)
- [app/config.py](file://app/config.py)
- [app/models/auth.py](file://app/models/auth.py)
- [app/models/employee.py](file://app/models/employee.py)
- [app/models/attendance.py](file://app/models/attendance.py)
- [app/models/payroll.py](file://app/models/payroll.py)
- [app/models/salary.py](file://app/models/salary.py)
- [app/models/tax.py](file://app/models/tax.py)
- [app/models/bpjs.py](file://app/models/bpjs.py)
- [app/models/leave.py](file://app/models/leave.py)
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
This API Reference documents the Payroll system’s RESTful endpoints and related data models. It focuses on the major functional areas:
- Authentication and Authorization
- Employee Management
- Payroll Processing
- Attendance Tracking
- Tax Management
- Salary and Compensation
- Leave Management
- BPJS Configuration

It describes HTTP method usage, URL patterns, request/response schemas, authentication requirements, and error handling strategies. It also provides common use cases, client implementation guidelines, API versioning information, rate limiting, security considerations, and testing procedures.

## Project Structure
The Payroll system is built with FastAPI and SQLAlchemy. The backend defines domain models under app/models representing entities such as Companies, Users, Employees, Departments, Positions, Payroll Runs, Payslips, Attendance Records, Tax Settings, Salary Structures, Leave Types, and BPJS Settings. These models define the data schema and constraints used by the API.

```mermaid
graph TB
subgraph "Models"
A["Companies<br/>Users<br/>Roles<br/>Permissions"]
B["Departments<br/>Positions<br/>EmploymentStatuses<br/>Employees"]
C["PayrollRuns<br/>Payslips<br/>PayslipLines"]
D["Shifts<br/>EmployeeShiftAssignments<br/>AttendanceRecords<br/>OvertimeRecords<br/>OvertimeSettings"]
E["TaxSettings<br/>PtkpValues<br/>TaxBracketsPasal17<br/>TerBrackets"]
F["Grades<br/>GradeSalaryMatrix<br/>AllowanceTypes<br/>EmployeeAllowances<br/>DeductionTypes"]
G["LeaveTypes<br/>EmployeeLeaveBalances<br/>LeaveRequests"]
H["BpjsSettings"]
end
A --> B
B --> C
B --> D
A --> E
A --> F
B --> G
A --> H
```

**Diagram sources**
- [app/models/auth.py:22-132](file://app/models/auth.py#L22-L132)
- [app/models/employee.py:20-131](file://app/models/employee.py#L20-L131)
- [app/models/payroll.py:19-123](file://app/models/payroll.py#L19-L123)
- [app/models/attendance.py:21-133](file://app/models/attendance.py#L21-L133)
- [app/models/tax.py:19-114](file://app/models/tax.py#L19-L114)
- [app/models/salary.py:21-134](file://app/models/salary.py#L21-L134)
- [app/models/leave.py:19-96](file://app/models/leave.py#L19-L96)
- [app/models/bpjs.py:17-43](file://app/models/bpjs.py#L17-L43)

**Section sources**
- [requirements.txt:1-14](file://requirements.txt#L1-L14)
- [app/config.py:4-17](file://app/config.py#L4-L17)

## Core Components
- Authentication and Authorization: Companies, Roles, Permissions, User Roles, Role Permissions, and Users define RBAC and user account management.
- Employee Management: Departments, Positions, Employment Statuses, and Employees form the organizational and personnel master data.
- Payroll Processing: Payroll Runs, Payslips, and Payslip Lines represent batch processing and individual pay statements.
- Attendance Tracking: Shifts, Employee Shift Assignments, Attendance Records, Overtime Records, and Overtime Settings capture daily attendance and overtime.
- Tax Management: Tax Settings, PTKP Values, Tax Brackets for Pasal 17, and TER Brackets define Indonesian tax configurations.
- Salary and Compensation: Grades, Grade-Salary Matrix, Allowance Types, Employee Allowances, and Deduction Types manage compensation structures.
- Leave Management: Leave Types, Employee Leave Balances, and Leave Requests handle leave lifecycle.
- BPJS Configuration: BPJS Settings define contribution rates and caps for health, pension, unemployment, and related insurances.

**Section sources**
- [app/models/auth.py:22-132](file://app/models/auth.py#L22-L132)
- [app/models/employee.py:20-131](file://app/models/employee.py#L20-L131)
- [app/models/payroll.py:19-123](file://app/models/payroll.py#L19-L123)
- [app/models/attendance.py:21-133](file://app/models/attendance.py#L21-L133)
- [app/models/tax.py:19-114](file://app/models/tax.py#L19-L114)
- [app/models/salary.py:21-134](file://app/models/salary.py#L21-L134)
- [app/models/leave.py:19-96](file://app/models/leave.py#L19-L96)
- [app/models/bpjs.py:17-43](file://app/models/bpjs.py#L17-L43)

## Architecture Overview
The system follows a layered architecture:
- Data Access Layer: SQLAlchemy ORM models define entities and relationships.
- Business Logic: Not shown here; endpoints orchestrate model queries and validations.
- API Layer: FastAPI routes expose REST endpoints grouped by functional domains.

```mermaid
graph TB
Client["Client"]
API["FastAPI Routes"]
Auth["Auth Models<br/>Users, Roles, Permissions"]
Emp["Employee Models<br/>Departments, Positions,<br/>EmploymentStatuses, Employees"]
Pay["Payroll Models<br/>PayrollRuns, Payslips,<br/>PayslipLines"]
Att["Attendance Models<br/>Shifts, AttendanceRecords,<br/>OvertimeRecords, OvertimeSettings"]
Tax["Tax Models<br/>TaxSettings, PtkpValues,<br/>TaxBracketsPasal17, TerBrackets"]
Sal["Salary Models<br/>Grades, GradeSalaryMatrix,<br/>AllowanceTypes, EmployeeAllowances,<br/>DeductionTypes"]
Lev["Leave Models<br/>LeaveTypes, EmployeeLeaveBalances,<br/>LeaveRequests"]
Bpjs["BPJS Models<br/>BpjsSettings"]
Client --> API
API --> Auth
API --> Emp
API --> Pay
API --> Att
API --> Tax
API --> Sal
API --> Lev
API --> Bpjs
```

**Diagram sources**
- [app/models/auth.py:22-132](file://app/models/auth.py#L22-L132)
- [app/models/employee.py:20-131](file://app/models/employee.py#L20-L131)
- [app/models/payroll.py:19-123](file://app/models/payroll.py#L19-L123)
- [app/models/attendance.py:21-133](file://app/models/attendance.py#L21-L133)
- [app/models/tax.py:19-114](file://app/models/tax.py#L19-L114)
- [app/models/salary.py:21-134](file://app/models/salary.py#L21-L134)
- [app/models/leave.py:19-96](file://app/models/leave.py#L19-L96)
- [app/models/bpjs.py:17-43](file://app/models/bpjs.py#L17-L43)

## Detailed Component Analysis

### Authentication and Authorization
- Purpose: Manage organizations, roles, permissions, and user accounts with RBAC.
- Key Entities:
  - Company: Organization/company metadata and payroll defaults.
  - Role: Role definitions with associated permissions.
  - Permission: Resource-action granular permissions.
  - User: System user accounts linked to company and employee.
  - User Roles and Role Permissions: Many-to-many associations.

```mermaid
classDiagram
class Company {
+int id
+string name
+string legal_name
+string tax_number
+string payroll_method
+boolean is_active
}
class Role {
+int id
+string name
+boolean is_system
}
class Permission {
+int id
+string name
+string resource
+string action
}
class User {
+int id
+string username
+string email
+string full_name
+boolean is_active
+datetime last_login
}
class UserRole {
+int user_id
+int role_id
}
class RolePermission {
+int role_id
+int permission_id
}
Role --> Permission : "has many"
User --> Role : "has many"
UserRole --> User : "links"
UserRole --> Role : "links"
RolePermission --> Role : "links"
RolePermission --> Permission : "links"
User --> Company : "belongs to"
Company --> User : "has many"
```

**Diagram sources**
- [app/models/auth.py:22-132](file://app/models/auth.py#L22-L132)

**Section sources**
- [app/models/auth.py:22-132](file://app/models/auth.py#L22-L132)

### Employee Management
- Purpose: Maintain organizational structure and employee master data.
- Key Entities:
  - Department: Hierarchical departments with self-reference.
  - Position: Job positions/titles.
  - EmploymentStatus: Employment types (e.g., permanent, contract).
  - Employee: Personal and employment details, linked to department, position, and status.

```mermaid
classDiagram
class Department {
+int id
+int company_id
+string name
+string code
+boolean is_active
}
class Position {
+int id
+int company_id
+string name
+string code
+boolean is_active
}
class EmploymentStatus {
+int id
+int company_id
+string name
+string code
+boolean is_permanent
+boolean is_active
}
class Employee {
+int id
+int company_id
+string employee_code
+string first_name
+string last_name
+date date_joined
+boolean is_active
}
Department <|-- Employee : "employee.department"
Position <|-- Employee : "employee.position"
EmploymentStatus <|-- Employee : "employee.employment_status"
Company --> Department : "has many"
Company --> Position : "has many"
Company --> EmploymentStatus : "has many"
```

**Diagram sources**
- [app/models/employee.py:20-131](file://app/models/employee.py#L20-L131)

**Section sources**
- [app/models/employee.py:20-131](file://app/models/employee.py#L20-L131)

### Payroll Processing
- Purpose: Batch payroll runs and compute individual payslips with earnings, deductions, taxes, and BPJS contributions.
- Key Entities:
  - PayrollRun: Batch run metadata and totals.
  - Payslip: Per-employee payslip with computed amounts.
  - PayslipLine: Line items categorized as earnings, deductions, taxes, BPJS, or net.

```mermaid
classDiagram
class PayrollRun {
+int id
+int company_id
+string payroll_period
+date period_start_date
+date period_end_date
+string payroll_method
+string tax_method
+string status
+numeric total_gross
+numeric total_deductions
+numeric total_tax
+numeric total_net
}
class Payslip {
+int id
+int payroll_run_id
+int employee_id
+string payslip_number
+numeric basic_salary
+numeric total_allowances
+numeric overtime_amount
+numeric bonus_amount
+numeric gross_salary
+numeric bpjs_kes_employee
+numeric bpjs_jht_employee
+numeric bpjs_jp_employee
+numeric pph21_tax
+numeric kasbon_deduction
+numeric other_deductions
+numeric total_deductions
+numeric net_salary
+int working_days
+numeric overtime_hours
+boolean is_approved
}
class PayslipLine {
+int id
+int payslip_id
+string line_type
+string category
+string description
+numeric amount
}
PayrollRun --> Payslip : "has many"
Payslip --> PayslipLine : "has many"
```

**Diagram sources**
- [app/models/payroll.py:19-123](file://app/models/payroll.py#L19-L123)

**Section sources**
- [app/models/payroll.py:19-123](file://app/models/payroll.py#L19-L123)

### Attendance Tracking
- Purpose: Track daily attendance, assign shifts, and record overtime with approval workflows.
- Key Entities:
  - Shift: Work shift definitions.
  - EmployeeShiftAssignment: Effective date ranges for shift assignments.
  - AttendanceRecord: Daily presence with status and worked hours.
  - OvertimeRecord: Overtime hours with approval status.
  - OvertimeSetting: Company-level overtime multipliers and policies.

```mermaid
classDiagram
class Shift {
+int id
+int company_id
+string code
+string name
+string start_time
+string end_time
+int break_duration_minutes
+boolean is_active
}
class EmployeeShiftAssignment {
+int id
+int employee_id
+int shift_id
+date effective_date
+date end_date
+boolean is_active
}
class AttendanceRecord {
+int id
+int employee_id
+date attendance_date
+string status
+string check_in_time
+string check_out_time
+int late_minutes
+numeric hours_worked
}
class OvertimeRecord {
+int id
+int employee_id
+date overtime_date
+string overtime_type
+numeric hours
+numeric multiplier
+numeric calculated_amount
+string approval_status
}
class OvertimeSetting {
+int id
+int company_id
+string work_week_type
+numeric weekday_first_hour_multiplier
+numeric weekday_subsequent_multiplier
+numeric weekend_first_hour_multiplier
+numeric weekend_subsequent_multiplier
+boolean is_active
}
Shift --> EmployeeShiftAssignment : "has many"
Employee --> EmployeeShiftAssignment : "has many"
Employee --> AttendanceRecord : "has many"
Employee --> OvertimeRecord : "has many"
Company --> Shift : "has many"
Company --> OvertimeSetting : "has many"
```

**Diagram sources**
- [app/models/attendance.py:21-133](file://app/models/attendance.py#L21-L133)

**Section sources**
- [app/models/attendance.py:21-133](file://app/models/attendance.py#L21-L133)

### Tax Management
- Purpose: Configure and calculate Indonesian income tax using PPh Pasal 17 or TER.
- Key Entities:
  - TaxSetting: Company-level tax method selection.
  - PtkpValue: PTKP thresholds per regulation year.
  - TaxBracketPasal17: Progressive tax brackets.
  - TerBracket: TER brackets for simplified tax.

```mermaid
classDiagram
class TaxSetting {
+int id
+int company_id
+string tax_calculation_method
+boolean is_active
}
class PtkpValue {
+int id
+int company_id
+string ptkp_code
+numeric annual_amount
+numeric monthly_amount
+int regulation_year
+date effective_date
+date end_date
+boolean is_active
}
class TaxBracketPasal17 {
+int id
+int company_id
+int bracket_order
+numeric income_range_min
+numeric income_range_max
+numeric tax_rate
+int regulation_year
+date effective_date
+date end_date
+boolean is_active
}
class TerBracket {
+int id
+int company_id
+string category
+numeric income_range_min
+numeric income_range_max
+numeric ter_rate
+int regulation_year
+date effective_date
+date end_date
+boolean is_active
}
Company --> TaxSetting : "has one"
Company --> PtkpValue : "has many"
Company --> TaxBracketPasal17 : "has many"
Company --> TerBracket : "has many"
```

**Diagram sources**
- [app/models/tax.py:19-114](file://app/models/tax.py#L19-L114)

**Section sources**
- [app/models/tax.py:19-114](file://app/models/tax.py#L19-L114)

### Salary and Compensation
- Purpose: Define salary structures, allowance types, and employee-specific allowances and deductions.
- Key Entities:
  - Grade: Employee grade definitions.
  - GradeSalaryMatrix: Salary bands per grade with effective dates.
  - AllowanceType: Types of allowances with calculation modes.
  - EmployeeAllowance: Employee-specific allowance assignments.
  - DeductionType: Types of deductions.

```mermaid
classDiagram
class Grade {
+int id
+int company_id
+string grade_name
+string grade_code
+boolean is_active
}
class GradeSalaryMatrix {
+int id
+int grade_id
+numeric basic_salary_min
+numeric basic_salary_max
+date effective_date
+date end_date
+boolean is_active
}
class AllowanceType {
+int id
+int company_id
+string name
+string code
+string calculation_type
+boolean is_taxable
+boolean is_bpjs_base
+boolean is_active
}
class EmployeeAllowance {
+int id
+int employee_id
+int allowance_type_id
+numeric amount
+date effective_date
+date end_date
+boolean is_active
}
class DeductionType {
+int id
+int company_id
+string name
+string code
+string calculation_type
+boolean is_recurring
+boolean is_active
}
Grade --> GradeSalaryMatrix : "has many"
Company --> Grade : "has many"
Company --> AllowanceType : "has many"
Company --> DeductionType : "has many"
Employee --> EmployeeAllowance : "has many"
AllowanceType --> EmployeeAllowance : "has many"
```

**Diagram sources**
- [app/models/salary.py:21-134](file://app/models/salary.py#L21-L134)

**Section sources**
- [app/models/salary.py:21-134](file://app/models/salary.py#L21-L134)

### Leave Management
- Purpose: Track leave types, employee balances, and requests with approval workflows.
- Key Entities:
  - LeaveType: Types of leave with entitlement and approval requirements.
  - EmployeeLeaveBalance: Annual leave balances per year.
  - LeaveRequest: Leave requests with statuses and approvals.

```mermaid
classDiagram
class LeaveType {
+int id
+int company_id
+string name
+string code
+int default_annual_entitlement
+boolean is_paid
+boolean requires_approval
+boolean is_active
}
class EmployeeLeaveBalance {
+int id
+int employee_id
+int leave_type_id
+int year
+int opening_balance
+int entitlement
+int used
+int carried_forward
+int closing_balance
}
class LeaveRequest {
+int id
+int employee_id
+int leave_type_id
+date start_date
+date end_date
+int days_requested
+string status
}
Company --> LeaveType : "has many"
Employee --> EmployeeLeaveBalance : "has many"
LeaveType --> EmployeeLeaveBalance : "has many"
Employee --> LeaveRequest : "has many"
LeaveType --> LeaveRequest : "has many"
```

**Diagram sources**
- [app/models/leave.py:19-96](file://app/models/leave.py#L19-L96)

**Section sources**
- [app/models/leave.py:19-96](file://app/models/leave.py#L19-L96)

### BPJS Configuration
- Purpose: Configure BPJS contribution rates and caps for employee and employer.
- Key Entity:
  - BpjsSetting: Contribution rates and caps per BPJS type.

```mermaid
classDiagram
class BpjsSetting {
+int id
+int company_id
+string bpjs_type
+numeric employee_rate
+numeric employer_rate
+numeric max_salary_base
+int regulation_year
+date effective_date
+date end_date
+boolean is_active
}
Company --> BpjsSetting : "has many"
```

**Diagram sources**
- [app/models/bpjs.py:17-43](file://app/models/bpjs.py#L17-L43)

**Section sources**
- [app/models/bpjs.py:17-43](file://app/models/bpjs.py#L17-L43)

## Dependency Analysis
- External Dependencies: FastAPI, Uvicorn, SQLAlchemy, Alembic, Pydantic, python-jose, passlib, httpx, langchain, openai, python-dotenv.
- Configuration: JWT secret, algorithm, expiration minutes, database URL, debug, and log level are managed via settings.

```mermaid
graph TB
Req["requirements.txt"]
Conf["app/config.py"]
Models["SQLAlchemy Models<br/>auth.py, employee.py, payroll.py,<br/>attendance.py, tax.py, salary.py,<br/>leave.py, bpjs.py"]
Req --> Conf
Conf --> Models
```

**Diagram sources**
- [requirements.txt:1-14](file://requirements.txt#L1-L14)
- [app/config.py:4-17](file://app/config.py#L4-L17)

**Section sources**
- [requirements.txt:1-14](file://requirements.txt#L1-L14)
- [app/config.py:4-17](file://app/config.py#L4-L17)

## Performance Considerations
- Indexes: Models define indexes on frequently queried columns (e.g., employee code, department, status, payroll period, attendance date).
- Constraints: Check constraints enforce valid enumerations and data ranges, preventing invalid writes and reducing runtime validation overhead.
- Pagination: For large datasets, implement pagination in API responses.
- Caching: Cache company-level settings (e.g., tax, BPJS, overtime) to reduce repeated reads.
- Asynchronous Operations: Offload heavy computations (e.g., payroll run) to background tasks.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
- Authentication Failures: Verify JWT secret, algorithm, and expiration settings. Ensure clients send Authorization header with bearer token.
- Data Validation Errors: Check constraint violations (enums, numeric ranges) and unique constraints (codes, usernames, emails).
- Database Connectivity: Confirm database URL and connection string in settings.
- Logging: Enable debug mode and appropriate log levels for diagnostics.

**Section sources**
- [app/config.py:4-17](file://app/config.py#L4-L17)
- [app/models/auth.py:128-132](file://app/models/auth.py#L128-L132)
- [app/models/employee.py:119-131](file://app/models/employee.py#L119-L131)
- [app/models/payroll.py:45-61](file://app/models/payroll.py#L45-L61)
- [app/models/attendance.py:72-80](file://app/models/attendance.py#L72-L80)

## Conclusion
This API Reference outlines the Payroll system’s RESTful endpoints and data models across authentication, employee management, payroll processing, attendance tracking, tax management, salary and compensation, leave management, and BPJS configuration. Clients should implement robust authentication using JWT, adhere to request/response schemas, apply rate limiting, and follow security best practices. Use the provided models and constraints to guide API design and validation.

[No sources needed since this section summarizes without analyzing specific files]

## Appendices

### API Versioning Information
- No explicit versioning scheme is defined in the repository. Consider adopting semantic versioning (e.g., v1, v2) and X-API-Version header for future releases.

[No sources needed since this section provides general guidance]

### Rate Limiting
- No built-in rate limiting is present in the repository. Implement rate limiting at the gateway or middleware level (e.g., per IP, per user, per endpoint).

[No sources needed since this section provides general guidance]

### Security Considerations
- Transport Security: Enforce HTTPS/TLS.
- Authentication: Use signed JWT with HS256 and a strong secret key.
- Authorization: Enforce RBAC via roles and permissions.
- Input Sanitization: Validate and sanitize all inputs; rely on model constraints.
- Secrets Management: Store JWT secret and database credentials in environment variables.

**Section sources**
- [app/config.py:6-8](file://app/config.py#L6-L8)

### API Testing Procedures
- Unit Tests: Validate model constraints and business rules.
- Integration Tests: Simulate end-to-end flows for payroll runs, payslip generation, and attendance/overtime updates.
- Load Tests: Assess performance under concurrent requests for payroll computation.
- Security Tests: Verify JWT handling, RBAC enforcement, and SQL injection prevention.

[No sources needed since this section provides general guidance]