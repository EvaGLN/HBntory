# Communication Strategies
## Backoffice `REST + HTML/CSS/JS`

**Selected option**<br>
JSON API for routes and a HTML static page which fetch.

**Benefits**<br>
API can be tested alone, without interface.

**Limitations**<br>
More JavaScript code to write compared to Server-Side Rendering due to page validation duplication.

## Client Web Interface `REST`

**Selected option**<br>
One request equal one reply.

**Benefits**<br>
Easier to implement and debug compared to WebSockets due to independant queries.

**Limitations**<br>
Impossibility to have dynamic conversation.

## AI Query Service `MCP via stdio`

**Selected option**<br>
AI agent runs MCP server for 3 sub-queries (product and branches stock and optimal shopping selection).

**Benefits**<br>
No free SQL and no additional network port.

**Limitations**<br>
Each query requires its own instruction tool.