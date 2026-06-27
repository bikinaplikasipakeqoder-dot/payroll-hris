# Payroll Processing

<cite>
**Referenced Files in This Document**
- [payroll.py](file://app/models/payroll.py)
- [salary.py](file://app/models/salary.py)
- [bpjs.py](file://app/models/bpjs.py)
- [tax.py](file://app/models/tax.py)
- [attendance.py](file://app/models/attendance.py)
- [employee.py](file://app/models/employee.py)
- [leave.py](file://app/models/leave.py)
- [bonus.py](file://app/models/bonus.py)
- [kasbon.py](file://app/models/kasbon.py)
- [integration.py](file://app/models/integration.py)
- [auth.py](file://app/models/auth.py)
- [base.py](file://app/models/base.py)
- [database.py](file://app/database.py)
- [seed_data.py](file://app/seed/seed_data.py)
- [env.py](file://alembic/env.py)
- [requirements.txt](file://requirements.txt)
- [payroll_service.py](file://app/services/payroll_service.py)
- [payslip_bulk_service.py](file://app/services/payslip_bulk_service.py)
- [payslip_pdf_service.py](file://app/services/payslip_pdf_service.py)
- [payslip_builder.py](file://app/services/payslip_builder.py)
- [config_loader.py](file://app/services/config_loader.py)
- [allowance.py](file://app/calculations/allowance.py)
- [overtime.py](file://app/calculations/overtime.py)
- [payroll.py](file://app/routers/payroll.py)
- [payroll.py](file://app/routers/payslip.py)
- [decimal_utils.py](file://app/utils/decimal_utils.py)
</cite>

## Update Summary
**Changes Made**
- Added comprehensive bulk payslip generation capabilities with background job processing
- Enhanced automated computation system with pure calculation modules
- Integrated advanced workflow management with job tracking and progress monitoring
- Implemented template-based PDF generation with customizable styling
- Added comprehensive approval workflows and audit tracking

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Automated Computation Engine](#automated-computation-engine)
7. [Bulk Generation and Workflow Management](#bulk-generation-and-workflow-management)
8. [Template-Based PDF Generation](#template-based-pdf-generation)
9. [Approval Workflows and Compliance](#approval-workflows-and-compliance)
10. [Performance Considerations](#performance-considerations)
11. [Troubleshooting Guide](#troubleshooting-guide)
12. [Conclusion](#conclusion)
13. [Appendices](#appendices)

## Introduction
This document explains the complete payroll processing system with automated computation, bulk generation, and comprehensive workflow management for Indonesia-based operations. The system features sophisticated batch processing orchestration, detailed payslip computation, attendance and salary integration, tax and BPJS adherence, and robust approval and audit controls. It covers payroll run configuration, payslip generation, batch processing workflows, approval processes, calculation algorithms, payslip line item processing, automated payment generation, integration with attendance records, salary structures, tax calculations, BPJS contributions, scheduling, approval workflows, and compliance reporting features.

## Project Structure
The system is organized around domain-focused SQLAlchemy models with enhanced service layers for automated computation and bulk processing. The architecture includes pure calculation modules, service orchestration, and comprehensive workflow management with background job processing.

```mermaid
graph TB
subgraph "Core Models"
A["auth.py<br/>Companies, Users, Roles, Permissions"]
B["employee.py<br/>Departments, Positions, Employment Status, Employees"]
C["attendance.py<br/>Shifts, Attendance, Overtime, Overtime Settings"]
D["salary.py<br/>Grades, Salary Matrix, Allowance Types, Employee Allowances, Deduction Types"]
E["leave.py<br/>Leave Types, Leave Balances, Leave Requests"]
F["bonus.py<br/>Bonus Types, Bonuses, Reimbursement Types, Reimbursements"]
G["kasbon.py<br/>Kasbon Requests, Installments"]
H["bpjs.py<br/>BPJS Settings"]
I["tax.py<br/>Tax Settings, PTKP, Tax Brackets (Pasal 17), TER Brackets"]
J["payroll.py<br/>Payroll Runs, Payslips, Payslip Lines, Jobs, Templates"]
K["integration.py<br/>Languages, Translations, Audit Logs"]
L["base.py<br/>Base, Timestamp, Soft Delete, Audit Mixins"]
end
subgraph "Service Layer"
M["payroll_service.py<br/>Batch Processing Orchestration"]
N["payslip_bulk_service.py<br/>Bulk Generation & Job Management"]
O["payslip_pdf_service.py<br/>PDF Generation & Templates"]
P["payslip_builder.py<br/>Payslip Construction"]
Q["config_loader.py<br/>Configuration Management"]
R["decimal_utils.py<br/>Precision Handling"]
end
subgraph "Calculation Engine"
S["allowance.py<br/>Allowance Calculations"]
T["overtime.py<br/>Overtime Computations"]
U["payroll.py<br/>Tax & BPJS Calculations"]
V["payroll.py<br/>Gross/Nett Methods"]
end
subgraph "API Layer"
W["payroll.py<br/>Payroll Endpoints"]
X["payroll.py<br/>Payslip Endpoints"]
end
subgraph "Runtime"
Y["database.py<br/>Engine, Session, get_db(), init_db()"]
Z["seed_data.py<br/>Indonesian defaults seeding"]
AA["env.py<br/>Alembic env for migrations"]
BB["requirements.txt<br/>Dependencies"]
end
A --> |"references"| B
B --> |"references"| D
B --> |"references"| E
B --> |"references"| F
B --> |"references"| G
C --> |"feeds"| M
D --> |"feeds"| M
E --> |"feeds"| M
F --> |"feeds"| M
G --> |"feeds"| M
H --> |"feeds"| M
I --> |"feeds"| M
J --> |"orchestrates"| M
M --> |"uses"| S
M --> |"uses"| T
M --> |"uses"| U
M --> |"uses"| V
M --> |"generates"| P
P --> |"creates"| J
N --> |"manages"| J
O --> |"renders"| J
Q --> |"provides"| M
W --> |"calls"| M
X --> |"calls"| N
X --> |"calls"| O
```

**Diagram sources**
- [payroll.py:19-197](file://app/models/payroll.py#L19-L197)
- [payroll_service.py:51-478](file://app/services/payroll_service.py#L51-L478)
- [payslip_bulk_service.py:27-345](file://app/services/payslip_bulk_service.py#L27-L345)
- [payslip_pdf_service.py:36-508](file://app/services/payslip_pdf_service.py#L36-L508)
- [payslip_builder.py:17-277](file://app/services/payslip_builder.py#L17-L277)
- [config_loader.py:35-144](file://app/services/config_loader.py#L35-L144)
- [allowance.py:19-122](file://app/calculations/allowance.py#L19-L122)
- [overtime.py:26-200](file://app/calculations/overtime.py#L26-L200)

**Section sources**
- [database.py:17-63](file://app/database.py#L17-L63)
- [env.py:14-80](file://alembic/env.py#L14-L80)
- [seed_data.py:27-64](file://app/seed/seed_data.py#L27-L64)

## Core Components
- **PayrollRun**: Batch processing container with period, method, tax method, status, and comprehensive totals
- **Payslip**: Per-employee earnings, deductions, taxes, BPJS, and net amounts with detailed line items
- **PayslipLine**: Line items categorized as EARNING, DEDUCTION, TAX, BPJS, or NET with structured sorting
- **PayslipGenerationJob**: Background job tracking for bulk PDF generation with progress monitoring
- **PayslipTemplate**: Admin-editable HTML templates for customizable PDF generation
- **PayslipRecord**: Metadata tracking for generated PDF files with status and file paths
- **PayrollConfig**: Frozen configuration snapshot containing tax, BPJS, and overtime settings
- **Pure Calculation Modules**: Stateless calculation engines for allowances, overtime, taxes, and BPJS
- **Service Layer**: Orchestration services for batch processing, bulk generation, and PDF rendering
- **Workflow Management**: Comprehensive approval workflows with audit trails and compliance tracking

**Section sources**
- [payroll.py:19-197](file://app/models/payroll.py#L19-L197)
- [payroll_service.py:51-478](file://app/services/payroll_service.py#L51-L478)
- [payslip_bulk_service.py:27-345](file://app/services/payslip_bulk_service.py#L27-L345)
- [payslip_pdf_service.py:36-508](file://app/services/payslip_pdf_service.py#L36-L508)
- [config_loader.py:24-144](file://app/services/config_loader.py#L24-L144)

## Architecture Overview
The system uses a comprehensive layered architecture with pure calculation modules, service orchestration, and advanced workflow management:

- **Data Layer**: SQLAlchemy models with shared mixins for timestamps, soft deletes, and audit tracking
- **Service Layer**: Pure calculation modules, batch processing orchestration, and bulk generation services
- **Presentation Layer**: RESTful APIs for payroll management and payslip generation
- **Workflow Layer**: Background job processing, approval workflows, and progress monitoring
- **Template Engine**: Jinja2-based HTML/CSS templating for customizable PDF generation
- **Compliance Layer**: Audit logs, validation rules, and regulatory compliance tracking

```mermaid
graph TB
PR["PayrollRun"]
PS["Payslip"]
PL["PayslipLine"]
PJ["PayslipGenerationJob"]
PT["PayslipTemplate"]
PRC["PayslipRecord"]
PC["PayrollConfig"]
CALC["Pure Calculation Engine"]
SERVICE["Service Layer"]
API["API Layer"]
PR --> PS
PS --> PL
PJ --> PS
PT --> PS
PRC --> PS
PC --> SERVICE
CALC --> SERVICE
SERVICE --> API
```

**Diagram sources**
- [payroll.py:19-197](file://app/models/payroll.py#L19-L197)
- [payroll_service.py:51-478](file://app/services/payroll_service.py#L51-L478)
- [payslip_bulk_service.py:27-345](file://app/services/payslip_bulk_service.py#L27-L345)

## Detailed Component Analysis

### Payroll Run Configuration and Lifecycle
The system manages complete payroll run lifecycle with comprehensive status tracking and validation:

```mermaid
stateDiagram-v2
[*] --> DRAFT
DRAFT --> PROCESSING : "process_payroll_run()"
PROCESSING --> COMPLETED : "batch calculation complete"
COMPLETED --> APPROVED : "approve_payroll_run()"
APPROVED --> PAID : "payment processing"
COMPLETED --> DRAFT : "rejection/adjustment"
```

**Diagram sources**
- [payroll.py:29-40](file://app/models/payroll.py#L29-L40)
- [payroll_service.py:137-252](file://app/services/payroll_service.py#L137-L252)

The PayrollRun model supports five distinct states with proper validation and audit tracking. The system ensures data integrity through transaction boundaries and comprehensive error handling.

**Section sources**
- [payroll.py:19-61](file://app/models/payroll.py#L19-L61)
- [payroll_service.py:61-134](file://app/services/payroll_service.py#L61-L134)

### Advanced Payslip Generation System
The payslip generation system creates comprehensive payroll records with detailed line items and automated computation:

```mermaid
classDiagram
class PayrollRun {
+int id
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
+bool is_approved
+string allowances_detail
+string deductions_detail
}
class PayslipLine {
+int id
+int payslip_id
+string line_type
+string category
+string description
+numeric amount
+int sort_order
}
class PayslipGenerationJob {
+int id
+string job_id
+int company_id
+int payroll_run_id
+int total_count
+int completed_count
+int failed_count
+string status
+string result_file_path
+datetime started_at
+datetime completed_at
}
PayrollRun "1" --> "*" Payslip : "contains"
Payslip "1" --> "*" PayslipLine : "has"
PayslipGenerationJob "1" --> "*" Payslip : "processes"
```

**Diagram sources**
- [payroll.py:64-197](file://app/models/payroll.py#L64-L197)

**Section sources**
- [payroll.py:64-124](file://app/models/payroll.py#L64-L124)
- [payroll.py:126-197](file://app/models/payroll.py#L126-L197)

### Attendance and Overtime Integration
The system integrates comprehensive attendance tracking with sophisticated overtime calculation:

```mermaid
flowchart TD
Start(["Collect Attendance Data"]) --> Validate["Validate Employee Data"]
Validate --> LoadOT["Load Overtime Records"]
LoadOT --> CalcOT["Calculate Overtime Pay"]
CalcOT --> BaseCalc["Calculate Salary Base"]
BaseCalc --> Taxable["Determine Taxable Income"]
Taxable --> TaxCalc["Compute PPh 21 Tax"]
TaxCalc --> BPJSCalc["Calculate BPJS Contributions"]
BPJSCalc --> NetCalc["Compute Net Salary"]
NetCalc --> BuildPayslip["Build Payslip Record"]
BuildPayslip --> End(["Complete"])
```

**Diagram sources**
- [payroll_service.py:262-378](file://app/services/payroll_service.py#L262-L378)
- [overtime.py:164-200](file://app/calculations/overtime.py#L164-L200)

**Section sources**
- [attendance.py:21-134](file://app/models/attendance.py#L21-L134)
- [payroll_service.py:262-378](file://app/services/payroll_service.py#L262-L378)

## Automated Computation Engine
The system features a comprehensive automated computation engine with pure calculation modules:

### Pure Calculation Architecture
All calculation functions are stateless and side-effect free, operating on immutable data structures:

```mermaid
graph TB
subgraph "Calculation Modules"
A["allowance.py<br/>Allowance Calculations"]
B["overtime.py<br/>Overtime Computations"]
C["tax.py<br/>Tax Calculations"]
D["bpjs.py<br/>BPJS Contributions"]
E["gross_nett.py<br/>Gross/Nett Methods"]
end
subgraph "Data Structures"
F["AllowanceEntry<br/>AllowanceResult"]
G["OvertimeEntry<br/>Work Week Types"]
H["TaxBracket<br/>TerBracketData"]
I["BpjsConfig<br/>BpjsResult"]
J["Decimal Utils<br/>Precision Handling"]
end
A --> F
B --> G
C --> H
D --> I
E --> J
F --> K["PayrollService"]
G --> K
H --> K
I --> K
J --> K
```

**Diagram sources**
- [allowance.py:19-122](file://app/calculations/allowance.py#L19-L122)
- [overtime.py:26-200](file://app/calculations/overtime.py#L26-L200)
- [config_loader.py:24-144](file://app/services/config_loader.py#L24-L144)
- [decimal_utils.py:11-33](file://app/utils/decimal_utils.py#L11-L33)

**Section sources**
- [allowance.py:19-122](file://app/calculations/allowance.py#L19-L122)
- [overtime.py:26-200](file://app/calculations/overtime.py#L26-L200)
- [config_loader.py:24-144](file://app/services/config_loader.py#L24-L144)
- [decimal_utils.py:11-33](file://app/utils/decimal_utils.py#L11-L33)

## Bulk Generation and Workflow Management
The system provides comprehensive bulk payslip generation with background job processing and progress monitoring:

### Bulk Generation Architecture
```mermaid
sequenceDiagram
participant Client as "Client"
participant API as "Payslip Router"
participant Service as "PayslipBulkService"
participant DB as "Database"
participant Worker as "Background Worker"
Client->>API : POST /payslip/bulk-generate
API->>Service : start_bulk_generation()
Service->>DB : Create PayslipGenerationJob
DB-->>Service : Job created
Service->>Worker : process_bulk_job(job_id)
Worker->>DB : Load payslips for run
Worker->>Worker : Render PDFs (parallel)
Worker->>DB : Update job progress
Worker->>DB : Create ZIP file
Worker->>DB : Create notifications
DB-->>API : Job status QUEUED
API-->>Client : {"job_id" : "...", "status" : "QUEUED"}
loop Progress Monitoring
Client->>API : GET /payslip/job-status/{job_id}
API->>DB : Query job status
DB-->>API : Progress data
API-->>Client : Progress update
end
Client->>API : GET /payslip/job/{job_id}/download
API->>DB : Verify completion
API-->>Client : ZIP file download
```

**Diagram sources**
- [payslip_bulk_service.py:32-345](file://app/services/payslip_bulk_service.py#L32-L345)
- [payroll.py:81-157](file://app/routers/payslip.py#L81-L157)

**Section sources**
- [payslip_bulk_service.py:27-345](file://app/services/payslip_bulk_service.py#L27-L345)
- [payroll.py:79-157](file://app/routers/payslip.py#L79-L157)

### Background Job Management
The system implements robust background job processing with thread pool management and progress tracking:

- **Job States**: QUEUED, PROCESSING, COMPLETED, FAILED with comprehensive error handling
- **Progress Tracking**: Real-time progress monitoring with completion and failure counts
- **Parallel Processing**: Thread pool executor for concurrent PDF generation (max 4 workers)
- **Storage Management**: Automatic ZIP file creation and individual PDF storage
- **Notification System**: Audit trail notifications for job completion and failures

**Section sources**
- [payslip_bulk_service.py:93-345](file://app/services/payslip_bulk_service.py#L93-L345)
- [payroll.py:171-197](file://app/models/payroll.py#L171-L197)

## Template-Based PDF Generation
The system provides flexible template-based PDF generation with customizable styling and content:

### Template Architecture
```mermaid
classDiagram
class PayslipPdfService {
+get_default_template() str
+render_html() str
+generate_pdf() bytes
+ensure_storage_dir() Path
+generate_single_payslip() tuple
}
class PayslipTemplate {
+int id
+int company_id
+string template_name
+text html_content
+text css_content
+bool is_default
+bool is_active
}
class PayslipRecord {
+int id
+int payslip_id
+int employee_id
+int company_id
+int year
+int month
+string file_path
+int file_size_bytes
+datetime generated_at
+int generated_by
+string status
}
PayslipPdfService --> PayslipTemplate : "uses"
PayslipPdfService --> PayslipRecord : "creates"
```

**Diagram sources**
- [payslip_pdf_service.py:36-508](file://app/services/payslip_pdf_service.py#L36-L508)
- [payroll.py:126-168](file://app/models/payroll.py#L126-L168)

**Section sources**
- [payslip_pdf_service.py:36-508](file://app/services/payslip_pdf_service.py#L36-L508)
- [payroll.py:126-168](file://app/models/payroll.py#L126-L168)

### Template Customization Features
- **Jinja2 Templating**: Dynamic HTML generation with variable substitution
- **Custom CSS Support**: Inline and external CSS styling options
- **Period Labeling**: Automatic month/year formatting with Indonesian localization
- **JSON Data Binding**: Structured data binding for allowances and deductions
- **File Storage**: Organized storage by year and month directories

**Section sources**
- [payslip_pdf_service.py:294-508](file://app/services/payslip_pdf_service.py#L294-L508)

## Approval Workflows and Compliance
The system implements comprehensive approval workflows with audit tracking and compliance features:

### Approval Workflow Architecture
```mermaid
flowchart TD
A["Create Payroll Run"] --> B["Process Batch Calculation"]
B --> C["Validate Results"]
C --> D["Approve Payroll Run"]
D --> E["Mark Payslips Approved"]
E --> F["Update Status to APPROVED"]
F --> G["Ready for Payment"]
H["Reject/Adjust"] --> A
```

**Diagram sources**
- [payroll_service.py:381-434](file://app/services/payroll_service.py#L381-L434)
- [payroll.py:37-40](file://app/models/payroll.py#L37-L40)

**Section sources**
- [payroll_service.py:381-434](file://app/services/payroll_service.py#L381-L434)
- [payroll.py:37-40](file://app/models/payroll.py#L37-L40)

### Compliance and Audit Features
- **Audit Trail**: Comprehensive logging of all payroll operations and approvals
- **Validation Rules**: Multi-layer validation for data integrity and regulatory compliance
- **Error Handling**: Graceful error handling with detailed error messages
- **Transaction Management**: Atomic operations with rollback capabilities
- **Regulatory Compliance**: Built-in support for Indonesian tax and social security regulations

**Section sources**
- [integration.py:70-93](file://app/models/integration.py#L70-L93)
- [payroll_service.py:137-252](file://app/services/payroll_service.py#L137-L252)

## Performance Considerations
The system is optimized for performance through several key strategies:

### Optimization Strategies
- **Batch Processing**: Bulk inserts for payslips and line items to minimize database round trips
- **Thread Pool Management**: Concurrent PDF generation with controlled parallelism (max 4 workers)
- **Memory Management**: Efficient handling of large PDF generation workloads
- **Database Indexing**: Strategic indexing on frequently queried columns
- **Connection Pooling**: Optimized database connection management
- **Decimal Precision**: Careful handling of monetary calculations with appropriate precision

### Scalability Features
- **Background Processing**: Non-blocking job execution for long-running operations
- **Progress Monitoring**: Real-time progress tracking for large-scale operations
- **Resource Management**: Controlled resource usage with worker limits
- **Error Recovery**: Automatic retry mechanisms and comprehensive error handling

## Troubleshooting Guide
Common issues and their solutions:

### Database and Schema Issues
- **Migration Failures**: Ensure Alembic migrations are applied successfully
- **Foreign Key Constraints**: Verify database constraints are properly configured
- **Connection Issues**: Check database URL and connection pool settings

### Calculation Errors
- **Invalid Configuration**: Verify tax settings, BPJS rates, and allowance configurations
- **Missing Data**: Ensure all required employee data is properly entered
- **Precision Issues**: Check decimal precision settings for monetary calculations

### Bulk Generation Problems
- **Job Queue Issues**: Monitor background worker availability and health
- **Storage Space**: Ensure adequate disk space for PDF generation
- **Template Errors**: Validate HTML/CSS template syntax and structure

**Section sources**
- [database.py:56-63](file://app/database.py#L56-L63)
- [env.py:41-73](file://alembic/env.py#L41-L73)
- [seed_data.py:27-64](file://app/seed/seed_data.py#L27-L64)

## Conclusion
The payroll processing system represents a comprehensive solution for Indonesian payroll management with automated computation, bulk generation capabilities, and robust workflow management. The system's architecture emphasizes modularity, scalability, and compliance with Indonesian labor and tax regulations. Through pure calculation modules, background job processing, and template-based PDF generation, it provides a complete solution for enterprise payroll processing with advanced features like real-time progress monitoring, comprehensive approval workflows, and detailed audit tracking.

## Appendices

### Concrete Examples (Step-by-step)

#### Create and Process Payroll Run
1. **Create Payroll Run**: Initialize with period, method, and tax configuration
2. **Process Batch**: Execute automated calculation for all employees
3. **Validate Results**: Review computed totals and individual payslips
4. **Approve Run**: Mark as approved and ready for payment processing

**Section sources**
- [payroll_service.py:61-134](file://app/services/payroll_service.py#L61-L134)
- [payroll_service.py:137-252](file://app/services/payroll_service.py#L137-L252)

#### Bulk Payslip Generation Workflow
1. **Start Job**: Initiate bulk generation with payroll run reference
2. **Monitor Progress**: Track completion percentage and individual PDF status
3. **Handle Errors**: Review failed generations and resolve issues
4. **Download Results**: Access completed ZIP file with all PDFs

**Section sources**
- [payslip_bulk_service.py:32-345](file://app/services/payslip_bulk_service.py#L32-L345)
- [payroll.py:81-157](file://app/routers/payslip.py#L81-L157)

#### Template-Based PDF Generation
1. **Create Template**: Design HTML/CSS template with Jinja2 variables
2. **Configure Settings**: Set template as active and default
3. **Generate PDF**: Render payslip with dynamic content
4. **Store Results**: Save PDF with metadata tracking

**Section sources**
- [payslip_pdf_service.py:294-508](file://app/services/payslip_pdf_service.py#L294-L508)
- [payroll.py:298-450](file://app/routers/payslip.py#L298-L450)

### System Configuration and Setup
- **Database Setup**: Initialize with proper constraints and indexes
- **Seed Data**: Load Indonesian regulatory defaults automatically
- **Template Management**: Configure default and custom templates
- **Background Workers**: Set up job processing infrastructure

**Section sources**
- [database.py:17-63](file://app/database.py#L17-L63)
- [seed_data.py:224-430](file://app/seed/seed_data.py#L224-L430)
- [payslip_bulk_service.py:30-31](file://app/services/payslip_bulk_service.py#L30-L31)