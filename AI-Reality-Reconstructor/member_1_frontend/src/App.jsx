import { useMemo, useState } from 'react';

const defaultEvents = [
  {
    timestamp: '2024-06-20 09:12',
    source: 'CCTV',
    location: 'Corridor B',
    description: 'Person seen in corridor',
  },
  {
    timestamp: '2024-06-20 09:18',
    source: 'sensor',
    location: 'Main Door',
    description: 'Door access sensor triggered',
  },
  {
    timestamp: '2024-06-20 09:26',
    source: 'witness',
    location: 'Outside Gate',
    description: 'Witness confirms route near gate',
  },
];

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function analyzeEvents(events) {
  const response = await fetch(`${apiBaseUrl}/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ events }),
  });

  if (!response.ok) {
    throw new Error('Investigation analysis failed');
  }

  return response.json();
}

export default function App() {
  const [events, setEvents] = useState(defaultEvents);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const summary = useMemo(() => {
    if (!results) return null;
    return {
      gapCount: results.gaps.length,
      questionCount: results.questions.length,
      critical: results.gaps.filter((gap) => gap.severity === 'high').length,
    };
  }, [results]);

  const handleAnalyze = async () => {
    setLoading(true);
    setError('');
    try {
      const payload = await analyzeEvents(events);
      setResults(payload);
    } catch (err) {
      setError(err.message || 'Unable to connect to the investigation backend.');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (index, field, value) => {
    const nextEvents = [...events];
    nextEvents[index] = { ...nextEvents[index], [field]: value };
    setEvents(nextEvents);
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">AI Reality Reconstructor</p>
          <h1>Investigation Layer</h1>
        </div>
        <button onClick={handleAnalyze} disabled={loading} className="primary-btn">
          {loading ? 'Analyzing...' : 'Run investigation analysis'}
        </button>
      </header>

      <main className="content-grid">
        <section className="panel">
          <h2>Evidence timeline</h2>

          {events.map((event, index) => (
            <div key={`${event.timestamp}-${index}`} className="event-card">
              <label>
                Timestamp
                <input
                  value={event.timestamp}
                  onChange={(e) => handleInputChange(index, 'timestamp', e.target.value)}
                />
              </label>
              <label>
                Source
                <input
                  value={event.source}
                  onChange={(e) => handleInputChange(index, 'source', e.target.value)}
                />
              </label>
              <label>
                Location
                <input
                  value={event.location}
                  onChange={(e) => handleInputChange(index, 'location', e.target.value)}
                />
              </label>
              <label>
                Description
                <textarea
                  value={event.description}
                  onChange={(e) => handleInputChange(index, 'description', e.target.value)}
                />
              </label>
            </div>
          ))}
        </section>

        <aside className="panel">
          <h2>Analysis summary</h2>
          {error ? <p className="error">{error}</p> : null}

          {summary ? (
            <div className="summary-grid">
              <div>
                <span>Detected gaps</span>
                <strong>{summary.gapCount}</strong>
              </div>
              <div>
                <span>Questions</span>
                <strong>{summary.questionCount}</strong>
              </div>
              <div>
                <span>Critical</span>
                <strong>{summary.critical}</strong>
              </div>
            </div>
          ) : (
            <p className="placeholder">Run the investigation to surface evidence gaps and follow-up questions.</p>
          )}

          {results?.gaps?.length ? (
            <div className="list-panel">
              <h3>Gaps</h3>
              {results.gaps.map((gap, index) => (
                <div className="result-card" key={`${gap.start}-${index}`}>
                  <div className="meta-row">
                    <span className="badge severity">{gap.severity}</span>
                    <span>{gap.location}</span>
                  </div>
                  <p>{gap.reason}</p>
                  <small>
                    {gap.start} → {gap.end}
                  </small>
                  <small>Sources: {gap.sources.join(', ')}</small>
                </div>
              ))}
            </div>
          ) : null}

          {results?.questions?.length ? (
            <div className="list-panel">
              <h3>Suggested questions</h3>
              <ul>
                {results.questions.map((question, index) => (
                  <li key={`${question}-${index}`}>{question}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </aside>
      </main>
    </div>
  );
}
