import { useState, useEffect, useRef } from "react";
import ProviderCard from "./components/ProviderCard";
import "./App.css";

const API_BASE = "http://localhost:8000/api/v1";

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        'Hi! I can help you find healthcare providers. Try something like: "Find a cardiologist near 30318 that accepts Medicaid and offers telehealth."',
    },
  ]);
  const [input, setInput] = useState("");
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function sendMessage() {
    const text = input.trim();
    if (!text || loading) return;

    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, history: messages }),
      });

      if (!res.ok) throw new Error("API error");

      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.reply },
      ]);
      setProviders(data.providers);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, something went wrong. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-icon">🏥</div>
        <div>
          <h1>Healthcare Burden Navigator</h1>
          <p>Find providers that fit your needs</p>
        </div>
      </header>

      <div className="layout">
        <div className="chat-panel">
          <div className="chat-panel-header">Chat with our assistant</div>

          <div className="messages">
            {messages.map((msg, i) => (
              <div key={i} className={`message ${msg.role}`}>
                {msg.role === "assistant" && (
                  <div className="avatar">AI</div>
                )}
                <div className="bubble">{msg.content}</div>
              </div>
            ))}
            {loading && (
              <div className="message assistant">
                <div className="avatar">AI</div>
                <div className="bubble">
                  <div className="loading-dots">
                    <span /><span /><span />
                  </div>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div className="input-row">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Describe what you're looking for..."
              rows={2}
              disabled={loading}
            />
            <button className="send-btn" onClick={sendMessage} disabled={loading || !input.trim()}>
              ➤
            </button>
          </div>
        </div>

        <div className="results-panel">
          {providers.length > 0 ? (
            <>
              <div className="results-header">
                <h2>Recommended Providers</h2>
                <span className="results-count">{providers.length} found</span>
              </div>
              <div className="provider-list">
                {providers.map((p) => (
                  <ProviderCard key={p.id} provider={p} />
                ))}
              </div>
            </>
          ) : (
            <div className="empty-results">
              <div className="empty-icon">🔍</div>
              <p>Provider recommendations will appear here after you search.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
