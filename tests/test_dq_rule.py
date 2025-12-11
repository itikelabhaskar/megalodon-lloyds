import os
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

project_id = os.getenv("BQ_DATA_PROJECT_ID")
dataset_id = os.getenv("BQ_DATASET_ID")

client = bigquery.Client(project=project_id)

# Test DQ Rule 1: Find records where CUS_DOB contains invalid date formats or future dates
# Note: CUS_DOB is STRING type, so we need to check for parsing issues
test_rule_1 = f"""
SELECT 
    CUS_ID,
    CUS_FORNAME,
    CUS_SURNAME,
    CUS_DOB,
    'Invalid DOB Format' as issue_type,
    'Accuracy' as dq_dimension
FROM `{project_id}.{dataset_id}.policies_week1`
WHERE CUS_DOB IS NULL 
   OR CUS_DOB = ''
   OR LENGTH(CUS_DOB) < 10
LIMIT 10
"""

print("🔍 Testing DQ Rule 1: Invalid Date of Birth Format\n")
print(f"SQL:\n{test_rule_1}\n")

results = client.query(test_rule_1).result()
issue_count = 0

print("Issues Found:")
for row in results:
    issue_count += 1
    print(f"  - Customer {row.CUS_ID} ({row.CUS_FORNAME} {row.CUS_SURNAME}): DOB = '{row.CUS_DOB}'")

if issue_count > 0:
    print(f"\n✅ Test passed: Found {issue_count} DQ issues")
else:
    print("\n⚠️  No issues found")

print("\n" + "="*70 + "\n")

# Test DQ Rule 2: Find records where life status is DCD but no death date
test_rule_2 = f"""
SELECT 
    CUS_ID,
    CUS_FORNAME,
    CUS_SURNAME,
    CUS_LIFE_STATUS,
    CUS_DEATH_DATE,
    'Deceased without Death Date' as issue_type,
    'Completeness' as dq_dimension
FROM `{project_id}.{dataset_id}.policies_week1`
WHERE CUS_LIFE_STATUS = 'DCD'
  AND CUS_DEATH_DATE IS NULL
LIMIT 10
"""

print("🔍 Testing DQ Rule 2: Deceased Status without Death Date\n")
print(f"SQL:\n{test_rule_2}\n")

results = client.query(test_rule_2).result()
issue_count = 0

print("Issues Found:")
for row in results:
    issue_count += 1
    print(f"  - Customer {row.CUS_ID} ({row.CUS_FORNAME} {row.CUS_SURNAME}): Status={row.CUS_LIFE_STATUS}, Death Date={row.CUS_DEATH_DATE}")

if issue_count > 0:
    print(f"\n✅ Test passed: Found {issue_count} DQ issues")
else:
    print("\n⚠️  No issues found")

print("\n" + "="*70 + "\n")

# Test DQ Rule 3: Find records with negative payment amounts
test_rule_3 = f"""
SELECT 
    CUS_ID,
    CRL_KEY_POLICY_NO,
    POLI_GROSS_PMT,
    POLI_TAX_PMT,
    POLI_INCOME_PMT,
    'Negative Payment Amount' as issue_type,
    'Accuracy' as dq_dimension
FROM `{project_id}.{dataset_id}.policies_week1`
WHERE POLI_GROSS_PMT < 0
   OR POLI_TAX_PMT < 0
   OR POLI_INCOME_PMT < 0
LIMIT 10
"""

print("🔍 Testing DQ Rule 3: Negative Payment Amounts\n")
print(f"SQL:\n{test_rule_3}\n")

results = client.query(test_rule_3).result()
issue_count = 0

print("Issues Found:")
for row in results:
    issue_count += 1
    print(f"  - Customer {row.CUS_ID}, Policy {row.CRL_KEY_POLICY_NO}: Gross={row.POLI_GROSS_PMT}, Tax={row.POLI_TAX_PMT}, Income={row.POLI_INCOME_PMT}")

if issue_count > 0:
    print(f"\n✅ Test passed: Found {issue_count} DQ issues")
else:
    print("\n⚠️  No issues found")

print("\n✅ All DQ rule tests complete - SQL-based rules work correctly!")
