import { Routes, Route, NavLink } from "react-router-dom";
import ChatPage from "./pages/ChatPage";
import SearchPage from "./pages/SearchPage";
import "./App.css";

export default function App() {
  return (
    <div className="app">
      <header className="header">
        <div className="header-top">
          <div>
            <h1>Healthcare Burden Navigator</h1>
            <p>Find providers that fit your needs</p>
          </div>
          <nav className="header-nav">
            <NavLink to="/" end>
              Chat
            </NavLink>
            <NavLink to="/search">
              Search
            </NavLink>
          </nav>
        </div>
      </header>

      <Routes>
        <Route path="/" element={<ChatPage />} />
        <Route path="/search" element={<SearchPage />} />
      </Routes>
    </div>
  );
}
