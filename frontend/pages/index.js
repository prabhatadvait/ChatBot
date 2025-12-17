import Head from "next/head";
import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";

/* ======================= ICONS ======================= */
const Icon = ({ children, size = 20, color = "currentColor" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    {children}
  </svg>
);

const PlusIcon = () => <Icon><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></Icon>;
const MessageSquareIcon = () => <Icon><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></Icon>;
const FolderIcon = () => <Icon><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></Icon>;
const AttachIcon = () => <Icon><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path></Icon>;
const MicIcon = () => <Icon><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></Icon>;
const SearchIcon = () => <Icon><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></Icon>;
const MoreHorizontalIcon = () => <Icon><circle cx="12" cy="12" r="1"></circle><circle cx="19" cy="12" r="1"></circle><circle cx="5" cy="12" r="1"></circle></Icon>;
const ChevronLeftIcon = () => <Icon><polyline points="15 18 9 12 15 6"></polyline></Icon>;
const TrashIcon = () => <Icon><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></Icon>;

/* ======================= COMPONENT ======================= */
export default function Home() {
  const [conversations, setConversations] = useState([]);
  const [folders, setFolders] = useState([]);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [isRecording, setIsRecording] = useState(false);

  // Menus
  const [openMenuId, setOpenMenuId] = useState(null); // 'chat-ID' or 'folder-ID'

  const messagesEndRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const backend = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

  useEffect(() => {
    fetchConversations();
    fetchFolders();
    document.addEventListener("click", () => setOpenMenuId(null));
    return () => document.removeEventListener("click", () => setOpenMenuId(null));
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function fetchConversations() {
    try {
      const res = await fetch(`${backend}/api/chat/history`);
      const data = await res.json();
      if (data.history) {
        setConversations(data.history);
      }
    } catch (err) {
      console.error("Failed to fetch conversations", err);
    }
  }

  async function fetchFolders() {
    try {
      const res = await fetch(`${backend}/api/chat/folders`);
      const data = await res.json();
      if (data.folders) {
        setFolders(data.folders);
      }
    } catch (err) {
      console.error("Failed to fetch folders", err);
    }
  }

  async function createFolder() {
    const name = prompt("Enter folder name:");
    if (!name) return;
    try {
      await fetch(`${backend}/api/chat/folders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name })
      });
      fetchFolders();
    } catch (err) {
      console.error("Failed to create folder", err);
    }
  }

  async function deleteFolder(id) {
    if (!confirm("Delete this folder?")) return;
    try {
      await fetch(`${backend}/api/chat/folders/${id}`, { method: "DELETE" });
      fetchFolders();
    } catch (err) {
      console.error("Failed to delete folder", err);
    }
  }

  async function deleteChat(e, id) {
    e.stopPropagation();
    if (!confirm("Delete this chat?")) return;
    try {
      await fetch(`${backend}/api/chat/history/${id}`, { method: "DELETE" });
      if (conversationId === id) {
        setConversationId(null);
        setMessages([]);
      }
      fetchConversations();
    } catch (err) {
      console.error("Failed to delete chat", err);
    }
  }

  async function loadConversation(id) {
    setLoading(true);
    setConversationId(id);
    setMessages([]); // Clear previous messages first
    try {
      const res = await fetch(`${backend}/api/chat/history/${id}`);
      const data = await res.json();
      if (data.messages) {
        const uiMessages = [];
        data.messages.forEach(msg => {
          uiMessages.push({ role: "user", text: msg.query });
          uiMessages.push({ role: "assistant", text: msg.response });
        });
        setMessages(uiMessages);
      }
    } catch (err) {
      console.error("Failed to load chat", err);
    }
    setLoading(false);
  }

  function startNewChat() {
    setConversationId(null);
    setMessages([]);
  }

  async function sendMessage(textOverride) {
    const text = textOverride || input.trim();
    if (!text || loading) return;

    const userMsg = { role: "user", text };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const payload = {
        query: text,
        top_k: 4,
        conversation_id: conversationId
      };

      const res = await fetch(`${backend}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      const botMsg = { role: "assistant", text: data.answer || "No response received." };
      setMessages(prev => [...prev, botMsg]);

      if (!conversationId && data.conversation_id) {
        setConversationId(data.conversation_id);
        fetchConversations();
      }
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
    setMessages(prev => [...prev, { role: "system", text: `Uploading ${file.name}...` }]);

    const form = new FormData();
    form.append("file", file);
    try {
      const res = await fetch(`${backend}/api/upload/document`, { method: "POST", body: form });
      const data = await res.json();
      setMessages(prev => [...prev, { role: "system", text: `Processed ${data.inserted} chunks.` }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: "system", text: "Upload failed." }]);
    }
    setLoading(false);
  }

  // --- AUDIO ---
  async function toggleRecording() {
    if (isRecording) stopRecording();
    else startRecording();
  }

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunksRef.current.push(event.data);
      };
      mediaRecorderRef.current.onstop = uploadVoice;
      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (err) {
      alert("Microphone access denied.");
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

    const form = new FormData();
    form.append("file", file);

    try {
      const res = await fetch(`${backend}/api/chat/transcribe`, { method: "POST", body: form });
      const data = await res.json();
      if (data.text) {
        sendMessage(data.text);
      }
    } catch (err) {
      console.error("Voice failed", err);
    }
    setLoading(false);
  }

  function toggleMenu(e, id) {
    e.stopPropagation();
    if (openMenuId === id) setOpenMenuId(null);
    else setOpenMenuId(id);
  }

  return (
    <>
      <Head>
        <title>Personal Chatbot</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600&display=swap" rel="stylesheet" />
      </Head>

      <div className="layout">
        {/* SIDEBAR */}
        <aside className="sidebar">
          <div className="sidebar-header">
            <div className="logo-area">
              <span className="logo-icon">AI</span>
              <span className="logo-text">My Chats</span>
            </div>
            {/* Settings icon removed as requested */}
          </div>

          <div className="search-bar">
            <SearchIcon />
            <input type="text" placeholder="Search" />
          </div>

          <div className="section-label">
            <span>Folders</span>
            <div className="section-actions" onClick={createFolder}>
              <PlusIcon />
            </div>
          </div>

          <div className="folders-list">
            {folders.map(folder => (
              <div key={folder.id} className="folder-item">
                <div className="folder-content">
                  <div className="folder-icon"><FolderIcon /></div>
                  <span>{folder.name}</span>
                </div>
                <div style={{ position: 'relative' }}>
                  <div onClick={(e) => toggleMenu(e, `folder-${folder.id}`)} style={{ cursor: 'pointer' }}><MoreHorizontalIcon /></div>
                  {openMenuId === `folder-${folder.id}` && (
                    <div className="popup-menu">
                      <div onClick={() => deleteFolder(folder.id)}>Delete</div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="section-label">
            <span>Chats</span>
          </div>

          <div className="chats-list">
            {conversations.map(chat => (
              <div key={chat.id} className={`chat-item ${conversationId === chat.id ? 'active' : ''}`} onClick={() => loadConversation(chat.id)}>
                <MessageSquareIcon />
                <div className="chat-info">
                  <span className="chat-title">{chat.title || "New Chat"}</span>
                  <span className="chat-preview">Check history...</span>
                </div>
                <div style={{ position: 'relative' }} onClick={(e) => e.stopPropagation()}>
                  <div className="menu-trigger" onClick={(e) => toggleMenu(e, `chat-${chat.id}`)}>
                    <MoreHorizontalIcon />
                  </div>
                  {openMenuId === `chat-${chat.id}` && (
                    <div className="popup-menu">
                      <div onClick={(e) => deleteChat(e, chat.id)} className="delete-option"><TrashIcon size={14} /> Delete</div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          <button className="new-chat-btn" onClick={startNewChat}>
            <span>New chat</span>
            <div className="plus-box"><PlusIcon /></div>
          </button>
        </aside>

        {/* MAIN AREA */}
        <main className="main-content">
          <header className="top-bar">
            {conversationId ? (
              <div className="breadcrumb">
                <ChevronLeftIcon />
                <span>{conversations.find(c => c.id === conversationId)?.title || "Current Chat"}</span>
                <span className="tag">HelpfulAI</span>
              </div>
            ) : (
              <div className="breadcrumb">
                <span className="tag">HelpfulAI</span>
              </div>
            )}
          </header>

          <div className="chat-area">
            {messages.length === 0 ? (
              <div className="welcome-screen">
                <div className="logo-center">AI</div>
                <h1>How can I help you today?</h1>
                <p>welcome to helpfulAI..</p>

                <div className="suggestion-cards">
                  <div className="card" onClick={() => sendMessage("Summarise the content properly and effectively")}>
                    <h3>Summarise Content</h3>
                    <p>Summarise the document.</p>
                  </div>
                  <div className="card" onClick={() => sendMessage("Explain quantum computing")}>
                    <h3>Explain Concepts</h3>
                    <p>Explain quantum computing to me.</p>
                  </div>
                  <div className="card" onClick={() => sendMessage("Draft a professional email properly and concise")}>
                    <h3>Draft Email</h3>
                    <p>Draft a professional email.</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="messages-list">
                {messages.map((msg, idx) => (
                  <div key={idx} className={`message ${msg.role}`}>
                    {msg.role === 'assistant' && <div className="avatar">AI</div>}
                    <div className="bubble">
                      {msg.role === 'system' ? <i>{msg.text}</i> : <ReactMarkdown>{msg.text}</ReactMarkdown>}
                    </div>
                    {msg.role === 'user' && <div className="avatar user">Me</div>}
                  </div>
                ))}
                {loading && <div className="message assistant"><div className="avatar">AI</div><div className="bubble typing">...</div></div>}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          <div className="input-area">
            <div className="input-box">
              <label className="icon-btn" title="Upload Document">
                <AttachIcon />
                <input type="file" onChange={uploadDocument} style={{ display: 'none' }} accept=".pdf,.txt" />
              </label>
              <input
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={isRecording ? "Listening..." : "Message helpfulAI..."}
                disabled={loading}
              />
              <button className={`icon-btn ${isRecording ? 'recording' : ''}`} onClick={toggleRecording}>
                <MicIcon />
              </button>
              <button className="send-btn" onClick={() => sendMessage()}>
                <Icon><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></Icon>
              </button>
            </div>
            <div className="footer-links">
              <span>AI</span>
              <span>Text</span>
              <span>Image</span>
              <span>Video</span>
              <span>Music</span>
              <span>Analytics</span>
            </div>
          </div>
        </main>
      </div>

      <style jsx global>{`
        :root {
          --bg-dark: #000000;
          --sidebar-bg: #111111;
          --border-color: #333;
          --accent-green: #22c55e;
          --text-primary: #fff;
          --text-secondary: #888;
        }

        * { box-sizing: border-box; }
        body, html { margin: 0; padding: 0; background: var(--bg-dark); color: var(--text-primary); font-family: 'Outfit', sans-serif; height: 100vh; overflow: hidden; }

        .layout { display: flex; height: 100vh; width: 100vw; }

        /* SIDEBAR */
        .sidebar {
          width: 300px;
          background: var(--sidebar-bg);
          border-right: 1px solid var(--border-color);
          display: flex;
          flex-direction: column;
          padding: 20px;
          gap: 20px;
        }

        .sidebar-header { display: flex; justify-content: space-between; align-items: center; }
        .logo-area { display: flex; align-items: center; gap: 10px; font-weight: bold; font-size: 18px; }
        .logo-icon { width: 24px; height: 24px; border-radius: 50%; border: 1px solid #fff; display: flex; align-items: center; justify-content: center; font-size: 10px; }

        .search-bar {
          background: #222;
          border-radius: 8px;
          padding: 10px;
          display: flex;
          align-items: center;
          gap: 10px;
          color: #666;
        }
        .search-bar input { background: transparent; border: none; color: white; outline: none; width: 100%; }

        .section-label { display: flex; justify-content: space-between; color: var(--text-secondary); font-size: 12px; font-weight: 600; text-transform: uppercase; margin-top: 10px; }
        .section-actions { cursor: pointer; }

        .folders-list, .chats-list { display: flex; flex-direction: column; gap: 5px; flex: 1; overflow-y: auto; }
        
        .folder-item, .chat-item {
          display: flex; align-items: center; justify-content: space-between; padding: 12px;
          border-radius: 8px; cursor: pointer;
          transition: background 0.2s;
          color: #ccc;
        }
        .folder-content { display: flex; align-items: center; gap: 12px; }

        .folder-item:hover, .chat-item:hover, .chat-item.active { background: #222; }
        .folder-icon { color: var(--accent-green); display: flex; }
        .chat-info { flex: 1; display: flex; flex-direction: column; overflow: hidden; margin-right: 10px; }
        .chat-title { color: white; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .chat-preview { font-size: 12px; color: #666; }

        .new-chat-btn {
          margin-top: auto;
          background: var(--accent-green);
          color: black;
          border: none;
          padding: 14px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          font-weight: 600;
          cursor: pointer;
        }
        .plus-box { background: white; border-radius: 4px; display: flex; width: 20px; height: 20px; align-items: center; justify-content: center; }

        /* MAIN CONTENT */
        .main-content {
          flex: 1;
          background: radial-gradient(circle at center, #1a2e1a 0%, #000000 70%);
          display: flex;
          flex-direction: column;
          position: relative;
        }

        .top-bar { padding: 20px; height: 60px; display: flex; align-items: center; }
        .breadcrumb { display: flex; align-items: center; gap: 10px; color: #ccc; font-size: 14px; }
        .tag { background: #1a2e1a; color: var(--accent-green); padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }

        .chat-area { flex: 1; overflow-y: auto; padding: 40px; display: flex; flex-direction: column; }
        
        .welcome-screen { max-width: 800px; margin: auto; text-align: center; color: #ccc; width: 100%; }
        .welcome-screen h1 { font-size: 32px; color: white; margin-bottom: 10px; }
        .logo-center { width: 40px; height: 40px; font-size: 20px;  color: var(--accent-green); margin: 0 auto 20px; display: flex; align-items: center; justify-content: center;}
        
        .suggestion-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 40px; }
        .card { background: #111; padding: 20px; border-radius: 12px; border: 1px solid #222; text-align: left; transition: transform 0.2s; cursor: pointer; }
        .card:hover { transform: translateY(-5px); border-color: var(--accent-green); }
        .card h3 { color: white; font-size: 14px; margin: 0 0 10px 0; }
        .card p { font-size: 12px; color: #666; margin: 0; lineHeight: 1.5; }

        .messages-list { max-width: 800px; width: 100%; margin: 0 auto; display: flex; flex-direction: column; gap: 20px; }
        .message { display: flex; gap: 15px; }
        .message.user { justify-content: flex-end; }
        .bubble { padding: 12px 18px; border-radius: 12px; background: #222; color: #eee; max-width: 80%; line-height: 1.5; }
        .message.user .bubble { background: var(--accent-green); color: black; }
        .avatar { width: 32px; height: 32px; background: #111; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; color: #666; border: 1px solid #333; }
        .avatar.user { background: #333; color: white; }

        .input-area { padding: 40px; display: flex; flex-direction: column; align-items: center; gap: 20px; }
        .input-box {
          width: 100%; max-width: 700px;
          background: #111;
          border: 1px solid #333;
          border-radius: 50px;
          padding: 8px 16px;
          display: flex; align-items: center; gap: 10px;
        }
        .input-box input { flex: 1; background: transparent; border: none; color: white; font-size: 16px; outline: none; padding: 10px; }
        .icon-btn { background: none; border: none; color: #666; cursor: pointer; padding: 8px; display: flex; transition: color 0.2s; }
        .icon-btn:hover { color: white; }
        .icon-btn.recording { color: red; animation: pulse 1s infinite; }
        .send-btn { background: var(--accent-green); color: black; border: none; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; }
        
        .footer-links { display: flex; gap: 20px; color: #555; font-size: 12px; }
        .footer-links span { cursor: pointer; transition: color 0.2s; }
        .footer-links span:hover { color: var(--accent-green); }
        
        .popup-menu {
           position: absolute;
           right: 0;
           top: 100%;
           background: #222;
           border: 1px solid #444;
           border-radius: 6px;
           padding: 4px;
           z-index: 100;
           min-width: 100px;
        }
        .popup-menu div {
           padding: 8px 12px;
           cursor: pointer;
           border-radius: 4px;
           font-size: 13px;
           display: flex; align-items: center; gap: 8px;
        }
        .popup-menu div:hover { background: #333; }
        .delete-option { color: #ef4444; }

        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
      `}</style>
    </>
  );
}