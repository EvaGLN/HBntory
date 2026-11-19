# Supported requests

| Type | Example | Tool | Reply if missing |
|---|---|---|---|
| Product details | Give me details about product P-001. | get_product | Unknown product |                                                     
| Where to find a product | Which branch has stock of P-001? | find_product_stock | No stock available |
| Branch content | What products can I find in Lyon? | find_branch_stock | Unknown branch |
| Shopping list | I want 3 of P-001 and 2 of P-002. Where can I buy it? | find_shopping_plan | Stock missing |

**Common rules**

- No history: each request is independant.
- Request limit: 500 characters.
- Out of scope: reply explaining what is supported.
- Failing tool: reply explaining the issue, never imagined.

**Limited cases tested**

- Product unknown
- Branch unknown
- Quantity requested higher than total stock available