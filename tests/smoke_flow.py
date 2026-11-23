import os
import sys
import requests

BACKOFFICE = os.environ.get("BACKOFFICE_URL", "http://localhost:5000")
PRODUCTS = os.environ.get("PRODUCT_API_URL", "http://localhost:8000")
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]


def check(label, condition):
    print("OK   " if condition else "FAIL", label)
    if not condition:
        sys.exit(1)


check("Product API answers",
      requests.get(f"{PRODUCTS}/products", timeout=5).status_code == 200)

s = requests.Session()

check("Admin can log in", s.post(f"{BACKOFFICE}/login", json={"username":
      "admin", "password": ADMIN_PASSWORD}).status_code == 200)

check("Admin can list users", s.get(f"{BACKOFFICE}/admin/users").status_code
      == 200)

check("Admin cannot manage stock", s.get(f"{BACKOFFICE}/branches/1/stock")
      .status_code == 403)

check("Anonymous is rejected", s.get(f"{BACKOFFICE}/admin/users").status_code
      == 401)

print("Flow OK: now test a common user, the MCP server and the client page.")
