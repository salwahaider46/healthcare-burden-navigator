import { useState, useRef, useEffect } from "react";
import ProviderCard from "./components/ProviderCard";
import "./App.css";

const API_BASE = "http://localhost:8000/api/v1";

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        'Hi! I can help you find healthcare providers. Tell me what you\'re looking for — for example: "Find a cardiologist near 30318 that accepts Medicaid and offers telehealth."',
    },
  ]);
  const [input, setInput] = useState("");
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage() {
    const text = input.trim();
    if (!text || loading) return;

    const userMessage = { role: "user", content: text };
    setMessages((prev) => [...prev, userMessage]);
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
        {
          role: "assistant",
          content: "Sorry, something went wrong. Please try again.",
        },
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
        <h1>Healthcare Burden Navigator</h1>
        <p>Find providers that fit your needs</p>
      </header>

      <div className="layout">
        <div className="chat-panel">
          <div className="messages">
            {messages.map((msg, i) => (
              <div key={i} className={`message ${msg.role}`}>
                <div className="bubble">{msg.content}</div>
              </div>
            ))}
            {loading && (
              <div className="message assistant">
                <div className="bubble loading">Searching...</div>
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
            <button onClick={sendMessage} disabled={loading || !input.trim()}>
              Send
            </button>
          </div>
        </div>

        <div className="results-panel">
          {providers.length > 0 ? (
            <>
              <h2>
                {providers.length} Provider{providers.length !== 1 ? "s" : ""} Found
              </h2>
              <div className="provider-list">
                {providers.map((p) => (
                  <ProviderCard key={p.id} provider={p} />
                ))}
              </div>
            </>
          ) : (
            <div className="empty-results">
              <p>Provider recommendations will appear here after you search.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
