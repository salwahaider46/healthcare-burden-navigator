import { useState } from "react";
import ProviderCard from "../components/ProviderCard";
import "./SearchPage.css";

const API_BASE = "http://localhost:8000/api/v1";

const SPECIALTY_OPTIONS = [
  "Cardiology",
  "Dermatology",
  "Endocrinology",
  "Family Medicine",
  "Gastroenterology",
  "Internal Medicine",
  "Neurology",
  "Obstetrics & Gynecology",
  "Oncology",
  "Ophthalmology",
  "Orthopedics",
  "Pediatrics",
  "Psychiatry",
  "Pulmonology",
  "Urology",
];

const INSURANCE_OPTIONS = [
  "Medicaid",
  "Medicare",
  "Aetna",
  "Blue Cross Blue Shield",
  "Cigna",
  "Humana",
  "Kaiser Permanente",
  "UnitedHealthcare",
  "Tricare",
  "Uninsured / Self-Pay",
];

const LANGUAGE_OPTIONS = [
  "English",
  "Spanish",
  "Mandarin",
  "Cantonese",
  "Vietnamese",
  "Korean",
  "Arabic",
  "French",
  "Portuguese",
  "Russian",
];

const DISTANCE_OPTIONS = [
  { label: "5 miles", value: 5 },
  { label: "10 miles", value: 10 },
  { label: "25 miles", value: 25 },
  { label: "50 miles", value: 50 },
  { label: "100 miles", value: 100 },
];

export default function SearchPage() {
  const [filters, setFilters] = useState({
    specialty: "",
    insurance: "",
    telehealth: "",
    zip_code: "",
    max_distance_miles: "",
    language: "",
  });
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState(null);

  function updateFilter(key, value) {
    setFilters((prev) => ({ ...prev, [key]: value }));
  }

  function resetFilters() {
    setFilters({
      specialty: "",
      insurance: "",
      telehealth: "",
      zip_code: "",
      max_distance_miles: "",
      language: "",
    });
    setProviders([]);
    setSearched(false);
    setError(null);
  }

  async function handleSearch(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSearched(true);

    const params = new URLSearchParams();
    if (filters.specialty) params.append("specialty", filters.specialty);
    if (filters.insurance) params.append("insurance", filters.insurance);
    if (filters.telehealth === "true") params.append("telehealth", "true");
    if (filters.telehealth === "false") params.append("telehealth", "false");
    if (filters.zip_code) params.append("zip_code", filters.zip_code);
    if (filters.max_distance_miles)
      params.append("max_distance_miles", filters.max_distance_miles);
    params.append("limit", "20");

    try {
      const res = await fetch(
        `${API_BASE}/providers/recommendations?${params.toString()}`
      );
      if (!res.ok) throw new Error(`Server error (${res.status})`);
      const data = await res.json();
      setProviders(data);
    } catch (err) {
      setError(err.message || "Something went wrong. Please try again.");
      setProviders([]);
    } finally {
      setLoading(false);
    }
  }

  const activeFilterCount = Object.values(filters).filter(Boolean).length;

  return (
    <div className="search-page">
      <aside className="filter-sidebar">
        <div className="filter-header">
          <h2>Search Filters</h2>
          {activeFilterCount > 0 && (
            <button className="clear-btn" onClick={resetFilters}>
              Clear All ({activeFilterCount})
            </button>
          )}
        </div>

        <form onSubmit={handleSearch} className="filter-form">
          {/* Specialty */}
          <div className="filter-group">
            <label htmlFor="specialty">Specialty</label>
            <select
              id="specialty"
              value={filters.specialty}
              onChange={(e) => updateFilter("specialty", e.target.value)}
            >
              <option value="">Any Specialty</option>
              {SPECIALTY_OPTIONS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          {/* Insurance */}
          <div className="filter-group">
            <label htmlFor="insurance">Insurance</label>
            <select
              id="insurance"
              value={filters.insurance}
              onChange={(e) => updateFilter("insurance", e.target.value)}
            >
              <option value="">Any Insurance</option>
              {INSURANCE_OPTIONS.map((ins) => (
                <option key={ins} value={ins}>
                  {ins}
                </option>
              ))}
            </select>
          </div>

          {/* Telehealth */}
          <div className="filter-group">
            <label htmlFor="telehealth">Telehealth</label>
            <select
              id="telehealth"
              value={filters.telehealth}
              onChange={(e) => updateFilter("telehealth", e.target.value)}
            >
              <option value="">Any</option>
              <option value="true">Telehealth Available</option>
              <option value="false">In-Person Only</option>
            </select>
          </div>

          {/* Distance */}
          <div className="filter-group">
            <label htmlFor="zip_code">ZIP Code</label>
            <input
              id="zip_code"
              type="text"
              placeholder="e.g. 30318"
              maxLength={5}
              value={filters.zip_code}
              onChange={(e) =>
                updateFilter("zip_code", e.target.value.replace(/\D/g, ""))
              }
            />
          </div>

          <div className="filter-group">
            <label htmlFor="distance">Max Distance</label>
            <select
              id="distance"
              value={filters.max_distance_miles}
              onChange={(e) =>
                updateFilter("max_distance_miles", e.target.value)
              }
            >
              <option value="">Any Distance</option>
              {DISTANCE_OPTIONS.map((d) => (
                <option key={d.value} value={d.value}>
                  {d.label}
                </option>
              ))}
            </select>
          </div>

          {/* Language */}
          <div className="filter-group">
            <label htmlFor="language">Language</label>
            <select
              id="language"
              value={filters.language}
              onChange={(e) => updateFilter("language", e.target.value)}
            >
              <option value="">Any Language</option>
              {LANGUAGE_OPTIONS.map((lang) => (
                <option key={lang} value={lang}>
                  {lang}
                </option>
              ))}
            </select>
            <span className="hint">Coming soon</span>
          </div>

          <button type="submit" className="search-btn" disabled={loading}>
            {loading ? "Searching..." : "Search Providers"}
          </button>
        </form>
      </aside>

      <main className="search-results">
        {loading && (
          <div className="search-status">
            <div className="spinner" />
            <p>Searching for providers...</p>
          </div>
        )}

        {!loading && error && (
          <div className="search-status error">
            <p>{error}</p>
          </div>
        )}

        {!loading && !error && searched && providers.length === 0 && (
          <div className="search-status">
            <p>No providers found matching your criteria. Try broadening your filters.</p>
          </div>
        )}

        {!loading && !searched && (
          <div className="search-status placeholder">
            <div className="placeholder-icon">&#128269;</div>
            <h3>Find the right provider for you</h3>
            <p>Use the filters on the left to search for healthcare providers by specialty, insurance, telehealth availability, location, and more.</p>
          </div>
        )}

        {!loading && providers.length > 0 && (
          <>
            <div className="results-header">
              <h2>
                {providers.length} Provider{providers.length !== 1 ? "s" : ""}{" "}
                Found
              </h2>
            </div>
            <div className="search-provider-list">
              {providers.map((p) => (
                <ProviderCard key={p.id} provider={p} />
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
