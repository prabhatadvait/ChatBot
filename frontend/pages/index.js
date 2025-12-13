import Head from "next/head";
import { useState, useRef, useEffect } from "react";

/* ======================= ICONS (Feather UI clone) ======================= */
const Icon = ({ children }) => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    {children}
  </svg>
);

const SendIcon = () => <Icon><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></Icon>;
const AttachIcon = () => <Icon><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path></Icon>;
const MicIcon = () => <Icon><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></Icon>;
const TrashIcon = () => <Icon><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></Icon>;
const PlusIcon = () => <Icon><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></Icon>;
const MessageSquareIcon = () => <Icon><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></Icon>;
const MenuIcon = () => <Icon><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></Icon>;
const HistoryIcon = () => <Icon><path d="M12 8v4l3 3"></path><circle cx="12" cy="12" r="9"></circle></Icon>; // Clock icon for history

/* ======================= COMPONENT ======================= */
export default function Home() {
  const [messages, setMessages] = useState([]);
  const [history, setHistory] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isRecording, setIsRecording] = useState(false);

  const messagesEndRef = useRef(null);
  const fileRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const backend = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

  useEffect(() => {
    fetchHistory();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function fetchHistory() {
    try {
      const res = await fetch(`${backend}/api/chat/history`);
      const data = await res.json();
      if (data.history) {
        setHistory(data.history); // Array of {id, query, response}
      }
    } catch (err) {
      console.error("Failed to fetch history", err);
    }
  }

  async function sendMessage(textOverride) {
    const text = textOverride || input.trim();
    if (!text || loading) return;

    // Add user message
    const userMsg = { role: "user", text };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${backend}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: text, top_k: 4 })
      });
      const data = await res.json();
      const botMsg = { role: "assistant", text: data.answer || "No response received." };
      setMessages(prev => [...prev, botMsg]);
      // Refresh history slightly delayed to start showing the new chat
      setTimeout(fetchHistory, 1000);
    } catch (err) {
      setMessages(prev => [...prev, { role: "assistant", text: "Error: Service unreachable." }]);
    }
    setLoading(false);
  }

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  async function uploadDocument(e) {
    const file = e.target.files[0];
    if (!file) return;
    setLoading(true);

    // Optimistic UI feedback
    setMessages(prev => [...prev, { role: "system", text: `Uploading ${file.name}...` }]);

    const form = new FormData();
    form.append("file", file);
    try {
      const res = await fetch(`${backend}/api/upload/document`, { method: "POST", body: form });
      const data = await res.json();
      setMessages(prev => [...prev, { role: "system", text: `processed. ${data.inserted} chunks stored.` }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: "system", text: "Upload failed." }]);
    }
    setLoading(false);
  }

  // --- AUDIO RECORDING ---
  async function toggleRecording() {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  }

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = uploadVoice;
      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (err) {
      alert("Microphone access denied or not available.");
    }
  }

  function stopRecording() {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }

  async function uploadVoice() {
    const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
    const file = new File([audioBlob], "voice_message.webm", { type: "audio/webm" });

    setLoading(true);
    setMessages(prev => [...prev, { role: "system", text: "🎤 Processing voice..." }]);

    const form = new FormData();
    form.append("file", file);

    try {
      const res = await fetch(`${backend}/api/chat/transcribe`, { method: "POST", body: form });
      const data = await res.json();

      if (data.text) {
        setMessages(prev => prev.filter(m => m.text !== "🎤 Processing voice..."));
        sendMessage(data.text);
      } else {
        setMessages(prev => [...prev, { role: "system", text: "Voice processing failed (No text)." }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: "system", text: "Voice processing failed." }]);
    }
    setLoading(false);
  }

  async function clearHistory() {
    if (!confirm("Clear all history?")) return;
    try {
      await fetch(`${backend}/api/chat/reset`, { method: "POST" });
      setMessages([]);
      setHistory([]);
    } catch (err) {
      alert("Failed to reset.");
    }
  }

  function loadHistoryItem(item) {
    // For now, just append/show this Q&A as if it just happened, or clear and show it.
    // Let's clear and show this single interaction to be simple.
    setMessages([
      { role: "user", text: item.query },
      { role: "assistant", text: item.response }
    ]);
    if (window.innerWidth < 768) setSidebarOpen(false);
  }

  function startNewChat() {
    setMessages([]);
    if (window.innerWidth < 768) setSidebarOpen(false);
  }

  return (
    <>
      <Head>
        <title>Personal Chatbot</title>
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1" />
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600&display=swap" rel="stylesheet" />
      </Head>

      <div style={styles.layout}>
        {/* SIDEBAR */}
        <div style={{ ...styles.sidebar, transform: sidebarOpen ? "translateX(0)" : "translateX(-100%)" }}>

          <div style={styles.sidebarHeader}>
            <button onClick={startNewChat} style={styles.newChatBtn}>
              <PlusIcon /> <span>New Chat</span>
            </button>
            <button onClick={() => setSidebarOpen(false)} style={styles.closeSidebarBtn}>
              <MenuIcon />
            </button>
          </div>

          <div style={styles.historyList}>
            <div style={styles.historyLabel}>Recent</div>
            {history.length === 0 && <div style={styles.noHistory}>No history yet.</div>}
            {history.map((item, i) => (
              <div key={item.id || i} onClick={() => loadHistoryItem(item)} style={styles.historyItem}>
                <MessageSquareIcon />
                <span style={styles.historyText}>{item.query}</span>
              </div>
            ))}
          </div>

          <div style={styles.sidebarFooter}>
            <button onClick={clearHistory} style={styles.clearBtn}>
              <TrashIcon /> Clear Data
            </button>
          </div>
        </div>

        {/* MAIN CHAT */}
        <div style={styles.main}>
          {/* Top Bar for Mobile/Toggle */}
          <div style={styles.topBar}>
            {!sidebarOpen && (
              <button onClick={() => setSidebarOpen(true)} style={styles.toggleBtn}>
                <MenuIcon />
              </button>
            )}
            <span style={styles.brandTitle}>Personal chatbot</span>
          </div>

          <div style={styles.chatContainer}>
            {messages.length === 0 ? (
              <div style={styles.emptyState}>
                <div style={styles.logoGiant}>AI</div>
                <h2>How can I help you today?</h2>
              </div>
            ) : (
              <div style={styles.messageList}>
                {messages.map((msg, i) => (
                  <div key={i} style={{
                    ...styles.messageRow,
                    justifyContent: msg.role === "user" ? "flex-end"
                      : msg.role === "system" ? "center"
                        : "flex-start"
                  }}>
                    {msg.role === "assistant" && <div style={styles.avatarAI}>AI</div>}

                    {msg.role === "system" ? (
                      <div style={styles.systemMessage}>{msg.text}</div>
                    ) : (
                      <div style={{
                        ...styles.bubble,
                        background: msg.role === "user" ? "#4f46e5" : "#1e293b",
                        color: "#fff",
                        borderRadius: msg.role === "user" ? "20px 20px 4px 20px" : "20px 20px 20px 4px",
                      }}>
                        {msg.text}
                      </div>
                    )}

                    {msg.role === "user" && <div style={styles.avatarUser}>Me</div>}
                  </div>
                ))}
                {loading && (
                  <div style={styles.messageRow}>
                    <div style={styles.avatarAI}>AI</div>
                    <div style={{ ...styles.bubble, background: "transparent", paddingLeft: 0 }}>
                      <span style={styles.typing}>Thinking...</span>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* INPUT AREA */}
          <div style={styles.inputWrapper}>
            <div style={styles.inputBox}>
              <label style={styles.attachBtn} title="Upload PDF">
                <AttachIcon />
                <input type="file" onChange={uploadDocument} style={{ display: 'none' }} accept=".pdf,.txt" />
              </label>
              <input
                style={styles.input}
                placeholder={isRecording ? "Listening..." : "Message Personal chatbot..."}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={loading || isRecording}
              />

              {/* MIC BUTTON */}
              <button onClick={toggleRecording} style={{
                ...styles.iconBtn,
                color: isRecording ? "#ef4444" : "#94a3b8",
                animation: isRecording ? "pulse 1.5s infinite" : "none"
              }} title="Record Audio">
                <MicIcon />
              </button>

              <button onClick={() => sendMessage()} disabled={loading || !input.trim()} style={{
                ...styles.sendBtn,
                opacity: input.trim() ? 1 : 0.5
              }}>
                <SendIcon />
              </button>
            </div>
            <div style={styles.footerText}>
              Personal chatbot can make mistakes. Verify important information.
            </div>
          </div>

        </div>
      </div>
      <style jsx global>{`
        body, html {
          margin: 0;
          padding: 0;
          width: 100%;
          height: 100%;
          background: #0f172a;
          overflow: hidden;
        }
        * {
          box-sizing: border-box;
        }
        @keyframes pulse {
            0% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.1); opacity: 0.7; }
            100% { transform: scale(1); opacity: 1; }
        }
      `}</style>
    </>
  );
}

const styles = {
  layout: {
    display: "flex",
    height: "100vh",
    width: "100vw",
    background: "#0f172a", // Slate 950
    color: "#e2e8f0",
    fontFamily: "'Outfit', sans-serif",
    overflow: "hidden",
  },
  sidebar: {
    width: "260px",
    background: "#020617", // Slate 950 darker
    borderRight: "1px solid #1e293b",
    display: "flex",
    flexDirection: "column",
    transition: "transform 0.3s ease",
    zIndex: 20,
    position: "absolute",
    height: "100%",
    // Responsive: On desktop usually absolute logic needs distinct handling, 
    // but for simple 'Chatgpt-like' mobile-first assumption:
    // We'll set generic styles, effectively overlay on mobile, static on desktop if we had media queries.
    // For inline styles limitation, let's assume overlay default or use logic.
    // Actually simplicity: making it absolute always works as drawer.
    // But for desktop we want it static. 
  },
  // We'll trust standard desktop resolution for 'static' behavior via simple hack:
  // We can't do media queries in inline styles easily. 
  // We'll assume the user is on a desktop or will tolerate the drawer behavior.
  // Wait, user asked for "right left panel", implies split view.
  // I will make it `position: relative` for the sidebar so it takes space.

  sidebarHeader: {
    padding: "16px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  newChatBtn: {
    flex: 1,
    display: "flex",
    alignItems: "center",
    gap: "10px",
    padding: "10px 14px",
    borderRadius: "8px",
    background: "transparent",
    border: "1px solid #334155",
    color: "#fff",
    cursor: "pointer",
    fontSize: "14px",
    transition: "background 0.2s",
    marginRight: "8px",
    justifyContent: "flex-start",
  },
  closeSidebarBtn: {
    background: "transparent",
    border: "none",
    color: "#94a3b8",
    cursor: "pointer",
    display: "none", // Hide by default, show via overrides if we could
  },
  historyList: {
    flex: 1,
    overflowY: "auto",
    padding: "0 12px",
    marginTop: "20px",
  },
  historyLabel: {
    fontSize: "12px",
    fontWeight: "600",
    color: "#64748b",
    marginBottom: "10px",
    paddingLeft: "8px",
    textTransform: "uppercase",
  },
  historyItem: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    padding: "10px",
    borderRadius: "8px",
    cursor: "pointer",
    color: "#cbd5e1",
    fontSize: "14px",
    transition: "background 0.2s",
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
  },
  historyText: {
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
    flex: 1,
  },
  noHistory: {
    padding: "10px",
    color: "#475569",
    fontSize: "13px",
    fontStyle: "italic",
  },
  sidebarFooter: {
    padding: "16px",
    borderTop: "1px solid #1e293b",
  },
  clearBtn: {
    width: "100%",
    display: "flex",
    alignItems: "center",
    gap: "8px",
    background: "transparent",
    border: "none",
    color: "#ef4444",
    padding: "10px",
    borderRadius: "6px",
    cursor: "pointer",
    fontSize: "14px",
  },

  main: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    position: "relative",
    height: "100%",
    background: "#0f172a",
    marginLeft: "260px", // Offset for fixed sidebar
  },
  topBar: {
    height: "50px",
    display: "flex",
    alignItems: "center",
    padding: "0 16px",
    borderBottom: "1px solid #1e293b",
    color: "#94a3b8",
    justifyContent: "space-between",
  },
  toggleBtn: {
    background: "transparent",
    border: "none",
    color: "#fff",
    cursor: "pointer",
  },
  brandTitle: {
    fontWeight: "500",
    color: "#e2e8f0",
  },
  chatContainer: {
    flex: 1,
    overflowY: "auto",
    display: "flex",
    flexDirection: "column",
    paddingBottom: "120px", // Space for input
  },
  emptyState: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    color: "#fff",
  },
  logoGiant: {
    width: "64px",
    height: "64px",
    borderRadius: "50%",
    background: "#fff",
    color: "#0f172a",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "24px",
    fontWeight: "bold",
    marginBottom: "16px",
    boxShadow: "0 0 20px rgba(255,255,255,0.2)",
  },
  messageList: {
    maxWidth: "800px",
    width: "100%",
    margin: "0 auto",
    padding: "24px",
    display: "flex",
    flexDirection: "column",
    gap: "24px",
  },
  messageRow: {
    display: "flex",
    gap: "16px",
    width: "100%",
  },
  avatarAI: {
    width: "36px",
    height: "36px",
    borderRadius: "50%",
    background: "#10b981", // Emerald
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "12px",
    fontWeight: "bold",
    flexShrink: 0,
  },
  avatarUser: {
    width: "36px",
    height: "36px",
    borderRadius: "50%",
    background: "#6366f1", // Indigo
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "12px",
    fontWeight: "bold",
    flexShrink: 0,
  },
  bubble: {
    padding: "12px 18px",
    fontSize: "15px",
    lineHeight: "1.6",
    maxWidth: "85%",
    boxShadow: "0 1px 2px rgba(0,0,0,0.1)",
  },
  systemMessage: {
    fontSize: "13px",
    color: "#94a3b8",
    fontStyle: "italic",
    padding: "8px 16px",
    background: "rgba(30,41,59,0.5)",
    borderRadius: "12px",
  },
  inputWrapper: {
    position: "absolute",
    bottom: 0,
    left: 0,
    width: "100%",
    background: "linear-gradient(to top, #0f172a 80%, transparent)",
    padding: "24px",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
  },
  inputBox: {
    maxWidth: "800px",
    width: "100%",
    background: "#1e293b",
    border: "1px solid #334155",
    borderRadius: "12px",
    display: "flex",
    alignItems: "center",
    padding: "8px 12px",
    boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
  },
  attachBtn: {
    color: "#94a3b8",
    padding: "8px",
    cursor: "pointer",
    display: "flex",
    transition: "color 0.2s",
  },
  iconBtn: {
    padding: "8px",
    cursor: "pointer",
    display: "flex",
    background: "transparent",
    border: "none",
    transition: "all 0.2s",
  },
  input: {
    flex: 1,
    background: "transparent",
    border: "none",
    color: "#fff",
    padding: "10px",
    fontSize: "15px",
    outline: "none",
  },
  sendBtn: {
    background: "#4f46e5",
    color: "#fff",
    border: "none",
    borderRadius: "8px",
    width: "36px",
    height: "36px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    cursor: "pointer",
    transition: "opacity 0.2s",
  },
  footerText: {
    fontSize: "12px",
    color: "#64748b",
    marginTop: "12px",
  },
  typing: {
    color: "#94a3b8",
    fontStyle: "italic",
    fontSize: "13px",
  }
};