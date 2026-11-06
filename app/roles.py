from enum import StrEnum

class RoleName(StrEnum):
    EMPLOYEE = "employee"
    SALES = "sales"
    FINANCE = "finance"
    HR = "hr"

ROLE_DESCRIPTIONS = {
    RoleName.EMPLOYEE: "General employee access",
    RoleName.SALES: "Sales department access",
    RoleName.FINANCE: "Finance department access",
    RoleName.HR: "Human Resources department access"
}