import { useState, useRef } from "react";

export default function Home() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const fileRef = useRef(null);

  const backend = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

  async function sendMessage() {
    if (!input.trim()) return;

    const userMsg = { role: "user", text: input };
    setMessages(prev => [...prev, userMsg]);

    const res = await fetch(`${backend}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: input, top_k: 4 })
    });

    const data = await res.json();
    const botMsg = { role: "assistant", text: data.answer };

    setMessages(prev => [...prev, botMsg]);
    setInput("");
  }

  async function uploadDocument() {
    const file = fileRef.current?.files[0];
    if (!file) return alert("Select a file.");

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
    alert("Chat reset.");
  }

  return (
    <div style={styles.page}>
      {/* NAVBAR */}
      <div style={styles.navbar}>
        <div style={styles.logo}>🤖 Secure AI</div>
        <button onClick={resetChat} style={styles.navResetBtn}>Reset</button>
      </div>

      {/* CHAT WINDOW */}
      <div style={styles.chatWindow}>
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              ...styles.message,
              alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
              background: msg.role === "user" ? "#6366f1" : "rgba(255,255,255,0.4)",
              color: msg.role === "user" ? "#fff" : "#000",
            }}
          >
            {msg.text}
          </div>
        ))}
      </div>

      {/* FLOATING INPUT BAR */}
      <div style={styles.inputContainer}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Type your message..."
          style={styles.input}
        />

        <button onClick={sendMessage} style={styles.sendBtn}>➤</button>

        <label style={styles.uploadBtn}>
          📄
          <input type="file" ref={fileRef} onChange={uploadDocument} style={styles.fileInput} />
        </label>

        <label style={styles.uploadBtn}>
          🎤
          <input type="file" ref={fileRef} onChange={uploadVoice} style={styles.fileInput} />
        </label>
      </div>
    </div>
  );
}

/* ======================= STYLES ======================= */

const styles = {
  page: {
    minHeight: "100vh",
    background: "linear-gradient(135deg, #eef2ff, #c7d2fe)",
    padding: "0px 20px",
    display: "flex",
    flexDirection: "column",
  },

  navbar: {
    height: "70px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0 20px",
    backdropFilter: "blur(12px)",
    background: "rgba(255,255,255,0.2)",
    borderRadius: "0 0 20px 20px",
    boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
  },

  logo: {
    fontSize: "24px",
    fontWeight: "bold",
    color: "#4338ca",
  },

  navResetBtn: {
    padding: "8px 14px",
    background: "#f87171",
    color: "#fff",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
    fontWeight: "bold",
  },

  chatWindow: {
    flex: 1,
    marginTop: "20px",
    padding: "20px",
    overflowY: "auto",
    display: "flex",
    flexDirection: "column",
    gap: "14px",
    background: "rgba(255,255,255,0.3)",
    borderRadius: "14px",
    boxShadow: "0 4px 15px rgba(0,0,0,0.1)",
  },

  message: {
    padding: "12px 16px",
    borderRadius: "12px",
    maxWidth: "70%",
    fontSize: "15px",
    lineHeight: "1.45",
    animation: "fadeIn 0.3s ease",
    wordBreak: "break-word",
    boxShadow: "0 2px 8px rgba(0,0,0,0.12)"
  },

  /* Floating input bar */
  inputContainer: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    padding: "14px",
    position: "sticky",
    bottom: "10px",
    background: "rgba(255,255,255,0.6)",
    backdropFilter: "blur(12px)",
    borderRadius: "12px",
    boxShadow: "0 4px 20px rgba(0,0,0,0.15)",
  },

  input: {
    flex: 1,
    padding: "12px",
    fontSize: "16px",
    borderRadius: "10px",
    border: "1px solid #c7d2fe",
    outline: "none",
    background: "#f8fafc",
  },

  sendBtn: {
    background: "#4f46e5",
    color: "#fff",
    padding: "10px 14px",
    fontSize: "18px",
    borderRadius: "10px",
    border: "none",
    cursor: "pointer",
    fontWeight: "bold",
  },

  uploadBtn: {
    padding: "10px 14px",
    background: "#6366f1",
    borderRadius: "10px",
    color: "#fff",
    cursor: "pointer",
    fontSize: "18px",
    fontWeight: "bold",
    display: "flex",
    alignItems: "center",
    justifyContent: "center"
  },

  fileInput: {
    display: "none",
  }
};