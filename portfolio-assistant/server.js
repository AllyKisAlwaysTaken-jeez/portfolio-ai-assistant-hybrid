import express from "express";
import dotenv from "dotenv";
import bodyParser from "body-parser";
import axios from "axios";
import path from "path";
import { fileURLToPath } from "url";
import { systemPrompt } from "./promptSystem.js";

dotenv.config();
const app = express();
app.use(bodyParser.json());

// Serve frontend
const __dirname = path.dirname(fileURLToPath(import.meta.url));
app.use(express.static(path.join(__dirname, "public")));

// API details
const BASE = process.env.GROQ_BASE || "https://api.groq.com/openai/v1";
const API_KEY = process.env.GROQ_API_KEY;

// 💾 Temporary in-memory store (per session)
const sessions = {}; // { sessionId: [{ role: "user"/"assistant", content: "..." }, ...] }

// Helper function: ensure memory doesn’t grow infinitely
function trimMemory(history, limit = 5) {
  return history.slice(-limit); // keep only the last `limit` messages
}

// Chat endpoint
app.post("/api/chat", async (req, res) => {
  const { userMessage, model = "llama-3.1-8b-instant", sessionId } = req.body;

  if (!sessionId) {
    return res.status(400).json({ error: "Missing sessionId" });
  }

  // Initialise session history if new
  if (!sessions[sessionId]) {
    sessions[sessionId] = [];
  }

  // Add user message to session history
  sessions[sessionId].push({ role: "user", content: userMessage });

  // Combine system + memory + new input
  const conversation = [
    { role: "system", content: systemPrompt },
    ...trimMemory(sessions[sessionId])
  ];

  try {
    const payload = {
      model,
      input: conversation,
      max_output_tokens: 500,
    };

    const groqRes = await axios.post(`${BASE}/responses`, payload, {
      headers: {
        Authorization: `Bearer ${API_KEY}`,
        "Content-Type": "application/json"
      }
    });

    const reply =
      groqRes.data?.output?.[0]?.content?.text ||
      groqRes.data?.output_text ||
      "Sorry, I couldn’t process that.";

    // Save assistant reply to session memory
    sessions[sessionId].push({ role: "assistant", content: reply });
    sessions[sessionId] = trimMemory(sessions[sessionId]);

    res.json({ reply });
  } catch (err) {
    console.error(err.response?.data || err);
    res.status(500).json({ error: "Chat failed", details: err.message });
  }
});

// Clear session (optional)
app.post("/api/clear", (req, res) => {
  const { sessionId } = req.body;
  if (sessionId && sessions[sessionId]) {
    delete sessions[sessionId];
  }
  res.json({ cleared: true });
});

// Start server
app.listen(process.env.PORT || 3000, () =>
  console.log(`✅ Chat assistant with memory running on port ${process.env.PORT || 3000}`)
);
