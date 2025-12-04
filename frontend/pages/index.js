import { useState, useRef, useEffect } from "react";

export default function Home() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const fileRef = useRef(null);

  const backend = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

  async function sendMessage() {
    if (!input.trim()) return;
    const userMsg = { role: "user", text: input };

    const res = await fetch(`${backend}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: input, top_k: 4 })
    });

    const data = await res.json();
    const botMsg = { role: "assistant", text: data.answer };

    setMessages(prev => [...prev, userMsg, botMsg]);
    setInput("");
  }

  async function uploadDocument() {
    const file = fileRef.current?.files[0];
    if (!file) return alert("Select a file first.");

    const form = new FormData();
    form.append("file", file);

    const res = await fetch(`${backend}/api/upload/document`, {
      method: "POST",
      body: form
    });

    const data = await res.json();
    alert(`Document uploaded. Chunks stored: ${data.inserted}`);
  }

  async function uploadVoice() {
    const file = fileRef.current?.files[0];
    if (!file) return alert("Select an audio file.");

    const form = new FormData();
    form.append("file", file);

    const res = await fetch(`${backend}/api/upload/voice`, {
      method: "POST",
      body: form
    });

    const data = await res.json();
    alert(`Voice processed. Chunks stored: ${data.inserted}`);
  }

  async function resetChat() {
    await fetch(`${backend}/api/chat/reset`, { method: "POST" });
    setMessages([]);
    alert("Chat history cleared.");
  }

  return (
    <div style={{ maxWidth: "800px", margin: "0 auto", padding: 20 }}>
      <h1 style={{ fontSize: "24px", marginBottom: "20px" }}>
        AI Chatbot
      </h1>

      <div
        style={{
          border: "1px solid #ccc",
          borderRadius: 6,
          height: 400,
          padding: 10,
          overflowY: "auto",
          background: "#fafafa"
        }}
      >
        {messages.map((m, i) => (
          <div key={i} style={{ margin: "10px 0" }}>
            <strong>{m.role === "user" ? "You" : "Assistant"}:</strong>{" "}
            {m.text}
          </div>
        ))}
      </div>

      <div style={{ display: "flex", gap: 10, marginTop: 15 }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Ask something..."
          style={{
            flex: 1,
            padding: 10,
            borderRadius: 6,
            border: "1px solid #ccc"
          }}
        />
        <button onClick={sendMessage} style={{ padding: "10px 20px" }}>
          Send
        </button>
      </div>

      <div style={{ marginTop: 20 }}>
        <input type="file" ref={fileRef} />
      </div>

      <div style={{ display: "flex", gap: 10, marginTop: 10 }}>
        <button onClick={uploadDocument}>Upload Document</button>
        <button onClick={uploadVoice}>Upload Voice</button>
      </div>

      <div style={{ marginTop: 20 }}>
        <button onClick={resetChat} style={{ background: "#fee", padding: "10px 20px" }}>
          New Chat (Reset)
        </button>
      </div>
    </div>
  );
}