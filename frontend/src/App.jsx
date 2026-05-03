import { Routes, Route, NavLink } from "react-router-dom";
import ChatPage from "./pages/ChatPage";
import SearchPage from "./pages/SearchPage";
import "./App.css";

export default function App() {
  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>Healthcare Burden Navigator</h1>
          <p className="subtitle">Find providers that fit your needs</p>
        </div>
        <nav className="nav-tabs">
          <NavLink to="/" end className={({ isActive }) => (isActive ? "tab active" : "tab")}>
            Chat
          </NavLink>
          <NavLink to="/search" className={({ isActive }) => (isActive ? "tab active" : "tab")}>
            Search
          </NavLink>
        </nav>
      </header>

      <Routes>
        <Route path="/" element={<ChatPage />} />
        <Route path="/search" element={<SearchPage />} />
      </Routes>
    </div>
  );
}
