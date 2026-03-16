/**
 * Minimal smoke test for tiny_node_service.
 * Run with: node test.js
 */

const http = require("http");
const assert = require("assert");

// Start the server on a test port
process.env.PORT = "3001";
const { server } = require("./index");

function get(path) {
  return new Promise((resolve, reject) => {
    http.get(`http://localhost:3001${path}`, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () =>
        resolve({ status: res.statusCode, body: JSON.parse(data) })
      );
    }).on("error", reject);
  });
}

async function run() {
  // Give the server a moment to start
  await new Promise((r) => setTimeout(r, 100));

  const health = await get("/health");
  assert.strictEqual(health.status, 200);
  assert.strictEqual(health.body.status, "ok");
  console.log("✓ GET /health");

  const items = await get("/items");
  assert.strictEqual(items.status, 200);
  console.log("✓ GET /items");

  server.close();
  console.log("\nAll tests passed.");
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
