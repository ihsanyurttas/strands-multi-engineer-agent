/**
 * tiny_node_service/index.js
 *
 * Intentionally minimal Node.js HTTP service.
 * Deliberate gaps: no error handling, no 404 handler.
 * Agent task: add centralised error handling.
 */

const http = require("http");

const PORT = process.env.PORT || 3000;

const routes = {
  "/health": (req, res) => {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "ok" }));
  },

  "/items": (req, res) => {
    // TODO: replace with a real data store
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ items: [] }));
  },
};

const server = http.createServer((req, res) => {
  const handler = routes[req.url];
  if (handler) {
    handler(req, res);
  }
  // No 404 or error handling — agent task is to add this.
});

server.listen(PORT, () => {
  console.log(`tiny_node_service listening on port ${PORT}`);
});

module.exports = { server };
