1) POST /issues
   Body: { title: string, body?: string, labels?: string[] }
   Behavior: Creates a GitHub issue in the configured repo.
   Responses:
     201 Created → { number, html_url, state, title, body, labels, created_at, updated_at }
     400 if invalid payload; 401 if missing/invalid token (propagate useful error info)
   Notes:
     - Return Location header: /issues/{number}
     - Map external validation errors into clear messages.

2) GET /issues
   Query: state=open|closed|all (default=open), labels?, page?, per_page? (<=100)
   Behavior: Lists issues for the repo; preserve GitHub pagination semantics.
   Responses:
     200 OK → [{ number, title, state, labels, ... }], plus pagination headers.

3) ✅ GET /issues/{number}
   Behavior: Returns a single issue.
   Responses: 200 OK, 404 if not found.

4) PATCH /issues/{number}
   Body: { title?, body?, state? }   # state may be "open" or "closed"
   Behavior: Updates the issue (rename, edit body, close/open).
   Responses: 200 OK; 400/404 on errors.

5) POST /issues/{number}/comments
   Body: { body: string }
   Behavior: Adds a comment to the issue.
   Responses: 201 Created → { id, body, user, created_at, html_url }

6) POST /webhook
   Behavior:
     - Verify HMAC SHA-256 signature using WEBHOOK_SECRET.
     - Accept events: "issues", "issue_comment" (and "ping").
     - On valid signature + known event: persist event to a local store (file/SQLite/in-memory ok), log summary.
     - Respond 2xx quickly (ack), never block on long work. Use retry-safe handling.
   Responses:
     204 No Content on success; 401 if signature invalid; 400 for unknown event/action.

7) GET /events (optional but recommended)
   Behavior: Returns the last N processed webhook deliveries for debugging.
   Response: 200 OK → array of { id, event, action, issue_number, timestamp }