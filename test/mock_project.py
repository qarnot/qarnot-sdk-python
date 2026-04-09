
from typing import List


default_project_json: dict = {
  "uuid": "12345678-1234-1234-1234-123456789012",
  "slug": "default",
  "name": "Default Project",
  "organizationUuid": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "description": "Organization default project",
  "isDefault": True
}

non_default_project_json: dict = {
  "uuid": "3fa85f64-5717-4562-b3fc-000000000001",
  "slug": "super-project",
  "name": "Super Project",
  "organizationUuid": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "description": "Organization super project"
}

default_json_active_budget: dict = {
  "uuid": "3fa85f64-5717-4562-b3fc-000000000001",
  "alias": "my-active-budget",
  "consumedAmountInCents": 321,
  "totalAmountInCents": 1000,
  "remainingAmountInCents": 679,
  "startDateUtc": "2026-03-26T09:53:57.414Z",
  "expirationDateUtc": "2026-03-31T09:53:57.414Z",
  "budgetOverrunPolicy": "AlertOnly",
  "isArchived": False
}

default_json_active_budgets: dict = {
  "budgets": [
    default_json_active_budget,
    {
      "uuid": "3fa85f64-5717-4562-b3fc-000000000002",
      "alias": "my-active-budget",
      "consumedAmountInCents": 120,
      "totalAmountInCents": 460,
      "remainingAmountInCents": 340,
      "startDateUtc": "2026-03-26T09:53:57.414Z",
      "expirationDateUtc": "2026-03-27T09:53:57.414Z",
      "budgetOverrunPolicy": "StopAndBlockAll",
      "isArchived": False
  }
  ]
}

default_json_all_budgets: dict = {
  "budgets": [
      default_json_active_budget,
    {
      "uuid": "3fa85f64-5717-4562-b3fc-000000000002",
      "alias": "my-active-budget",
      "consumedAmountInCents": 120,
      "totalAmountInCents": 460,
      "remainingAmountInCents": 340,
      "startDateUtc": "2026-03-26T09:53:57.414Z",
      "expirationDateUtc": "2026-03-27T09:53:57.414Z",
      "budgetOverrunPolicy": "StopAndBlockAll",
      "isArchived": False
    },
    {
      "uuid": "3fa85f64-5717-4562-b3fc-000000000003",
      "alias": "my-active-budget",
      "consumedAmountInCents": 2345,
      "totalAmountInCents": 2300,
      "remainingAmountInCents": -45,
      "startDateUtc": "2026-03-24T09:53:57.414Z",
      "expirationDateUtc": "2026-03-26T09:53:57.414Z",
      "budgetOverrunPolicy": "StopAndBlockAll",
      "isArchived": True
  },
  ]
}

json_empty_budgets: dict = { "budgets": [] }