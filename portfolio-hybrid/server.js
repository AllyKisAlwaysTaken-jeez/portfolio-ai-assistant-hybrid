// server.js
import express from "express";
import dotenv from "dotenv";
import bodyParser from "body-parser";
import axios from "axios";
import path from "path";
import { fileURLToPath } from "url";
import { chatSystemPrompt } from "./prompts/chatSystem.js";
import { generatorSystemPrompt } from "./prompts/generatorSystem.js";
import { addMemory, searchMemory } from "./embeddings/index.js";

dotenv.config();
const app = express();
app.use(bodyParser.json());

const __dirname = path.dirname(fileURLToPath(import.meta.url));
app.use(express.static(path.join(__dirname, "public")));

const BASE = process.env.GROQ_BASE;
const API_KEY = process.env.GROQ_API_KEY;

// 🧠 Store memory (facts about users)
app.post("/api/store", async (req, res) => {
  const { text, meta } = req.body;
  await addMemory(text, meta);
  res.json({ status: "stored", text });
});

// 💬 Chat endpoint
app.post("/api/chat", async (req, res) => {
  const { userMessage, model = "llama-3.1-8b-instant" } = req.body;
  try {
    const payload = {
      model,
      input: [
        { role: "system", content: chatSystemPrompt },
        { role: "user", content: userMessage }
      ],
      max_output_tokens: 500
    };
    const groqRes = await axios.post(`${BASE}/responses`, payload, {
      headers: { Authorization: `Bearer ${API_KEY}` }
    });

    const reply = groqRes.data?.output?.[0]?.content?.text || "Sorry, I couldn’t process that.";
    res.json({ reply });
  } catch (err) {
    console.error(err.response?.data || err);
    res.status(500).json({ error: "Chat failed", details: err.message });
  }
});

// 💡 Generate portfolio (uses memory)
app.post("/api/generate", async (req, res) => {
  const { name, role, color, sections, style, model = "llama-3.1-8b-instant" } = req.body;

  const query = `${name} ${role} portfolio information`;
  const context = await searchMemory(query, 5);
  const contextText = context.map(c => c.item.text).join("\n");

  const userInput = `
Name: ${name}
Role: ${role}
Color theme: ${color}
Sections: ${sections.join(", ")}
Style: ${style}

Use the following information to fill in About Me, Experience, and Projects:
${contextText}
`;

  try {
    const payload = {
      model,
      input: [
        { role: "system", content: generatorSystemPrompt },
        { role: "user", content: userInput }
      ],
      max_output_tokens: 1500
    };

    const groqRes = await axios.post(`${BASE}/responses`, payload, {
      headers: { Authorization: `Bearer ${API_KEY}` }
    });

    const raw = groqRes.data?.output?.[0]?.content?.text || "{}";
    const jsonOutput = JSON.parse(raw);
    res.json(jsonOutput);
  } catch (err) {
    console.error(err.response?.data || err);
    res.status(500).json({ error: "Generation failed", details: err.message });
  }
});

app.listen(process.env.PORT || 3000, () =>
  console.log(`✅ AI Agent with Memory running on port ${process.env.PORT || 3000}`)
);
