/**
 * ATS Optimizer Component - Transparent, Trust-Building UX
 *
 * Key Principles:
 * 1. Always show original CV first
 * 2. Display score breakdown with details
 * 3. List all issues and recommendations
 * 4. Show optimized version separately
 * 5. Display every change with before/after/reason
 * 6. Never hide anything
 */

// ==================== ATS SCORE DISPLAY ====================

export function ATSScoreBreakdown({ analysis }) {
  if (!analysis) return <p>Analyzing CV...</p>;

  const { overall_score, grade, score_breakdown, issues, recommendations } =
    analysis;

  return (
    <div className="ats-score-container">
      {/* Overall Score */}
      <div className="overall-score">
        <h2>ATS Compatibility Score</h2>
        <div className="score-display">
          <span className={`score score-${grade}`}>{overall_score}/100</span>
          <span className={`grade grade-${grade}`}>{grade}</span>
        </div>
        <p className="score-description">
          {getScoreDescription(overall_score)}
        </p>
      </div>

      {/* Score Breakdown */}
      <div className="score-breakdown">
        <h3>Score Breakdown</h3>
        <div className="breakdown-grid">
          {Object.entries(score_breakdown).map(([category, data]) => (
            <div key={category} className="breakdown-item">
              <h4>{formatCategoryName(category)}</h4>
              <div className="score-bar">
                <div
                  className="score-fill"
                  style={{ width: `${(data.score / data.max) * 100}%` }}
                />
              </div>
              <p className="score-text">
                {data.score}/{data.max} ({data.percentage?.toFixed(1)}%)
              </p>

              {/* Details */}
              <div className="details">
                {data.details.map((detail, i) => (
                  <p key={i} className={`detail ${getSeverityClass(detail)}`}>
                    {detail}
                  </p>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Issues Found */}
      {issues.length > 0 && (
        <div className="issues-section">
          <h3>Issues Found ({issues.length})</h3>
          <div className="issues-list">
            {issues.map((issue, i) => (
              <div key={i} className={`issue ${issue.severity}`}>
                <span className="severity-badge">
                  {issue.severity.toUpperCase()}
                </span>
                <span className="category">
                  {formatCategoryName(issue.category)}
                </span>
                <p className="message">{issue.message}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      <div className="recommendations-section">
        <h3>How to Improve</h3>
        {Object.entries(recommendations)
          .filter(([_, items]) => items.length > 0)
          .map(([priority, items]) => (
            <div key={priority} className={`priority-group ${priority}`}>
              <h4>{formatPriority(priority)}</h4>
              <ul>
                {items.map((item, i) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
            </div>
          ))}
      </div>
    </div>
  );
}

// ==================== ATS OPTIMIZATION DISPLAY ====================

export function ATSOptimizationPreview({
  original_cv,
  optimized_cv,
  changes,
  score_improvement,
  original_analysis,
  optimized_analysis,
}) {
  const [activeTab, setActiveTab] = useState("changes");
  const [expandedChange, setExpandedChange] = useState(null);

  return (
    <div className="ats-optimization-container">
      <div className="optimization-header">
        <h2>ATS Optimization</h2>
        <div className="score-improvement">
          <span className="improvement-label">Score Improvement:</span>
          <span
            className={`improvement-badge ${
              score_improvement >= 0 ? "positive" : "negative"
            }`}
          >
            {score_improvement >= 0 ? "+" : ""}
            {score_improvement}
          </span>
          <span className="score-details">
            {original_analysis.overall_score} →{" "}
            {optimized_analysis.overall_score}
          </span>
        </div>
      </div>

      {/* Tab Selection */}
      <div className="optimization-tabs">
        <button
          className={`tab ${activeTab === "changes" ? "active" : ""}`}
          onClick={() => setActiveTab("changes")}
        >
          Changes ({changes.length})
        </button>
        <button
          className={`tab ${activeTab === "comparison" ? "active" : ""}`}
          onClick={() => setActiveTab("comparison")}
        >
          Analysis Comparison
        </button>
      </div>

      {/* Changes Tab */}
      {activeTab === "changes" && (
        <div className="changes-list">
          {changes.length === 0 ? (
            <p className="no-changes">No changes recommended at this time.</p>
          ) : (
            changes.map((change, i) => (
              <div
                key={i}
                className="change-item"
                onClick={() =>
                  setExpandedChange(expandedChange === i ? null : i)
                }
              >
                <div className="change-header">
                  <span className="change-number">Change {i + 1}</span>
                  <span className="change-field">{change.field}</span>
                  <span className="change-toggle">
                    {expandedChange === i ? "▼" : "▶"}
                  </span>
                </div>

                {expandedChange === i && (
                  <div className="change-details">
                    <div className="before-after">
                      <div className="before">
                        <label>BEFORE</label>
                        <p className="text">{change.before}</p>
                      </div>
                      <div className="arrow">→</div>
                      <div className="after">
                        <label>AFTER</label>
                        <p className="text">{change.after}</p>
                      </div>
                    </div>

                    <div className="reason">
                      <label>WHY THIS HELPS</label>
                      <p>{change.reason}</p>
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* Comparison Tab */}
      {activeTab === "comparison" && (
        <div className="analysis-comparison">
          <div className="comparison-column original">
            <h3>Original Analysis</h3>
            <ScoreBreakdownCompact analysis={original_analysis} />
          </div>
          <div className="comparison-column optimized">
            <h3>Optimized Analysis</h3>
            <ScoreBreakdownCompact analysis={optimized_analysis} />
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="optimization-actions">
        <button
          className="btn btn-secondary"
          onClick={() => downloadCVVersion(original_cv, "original")}
        >
          Download Original CV
        </button>
        <button
          className="btn btn-primary"
          onClick={() => downloadCVVersion(optimized_cv, "optimized")}
        >
          Download ATS-Optimized CV
        </button>
      </div>

      {/* Transparency Notice */}
      <div className="transparency-notice">
        <p>
          ✅ All changes shown above. Original CV is never modified. You can
          review each change and download either version.
        </p>
      </div>
    </div>
  );
}

// ==================== CV PREVIEW ====================

export function CVPreviewTabs({ original_file_url, optimized_cv }) {
  const [activeVersion, setActiveVersion] = useState("original");

  return (
    <div className="cv-preview-container">
      <div className="version-selector">
        <button
          className={`version-btn ${
            activeVersion === "original" ? "active" : ""
          }`}
          onClick={() => setActiveVersion("original")}
        >
          📄 Original CV
        </button>
        {optimized_cv && (
          <button
            className={`version-btn ${
              activeVersion === "optimized" ? "active" : ""
            }`}
            onClick={() => setActiveVersion("optimized")}
          >
            ✨ ATS-Optimized
          </button>
        )}
      </div>

      <div className="preview-container">
        {activeVersion === "original" && original_file_url && (
          <div className="original-preview">
            <p className="version-label">Original Uploaded Document</p>
            <embed
              src={original_file_url}
              type="application/pdf"
              width="100%"
              height="600"
            />
            <p className="note">
              This is the exact document you uploaded. No changes applied.
            </p>
          </div>
        )}

        {activeVersion === "optimized" && optimized_cv && (
          <div className="optimized-preview">
            <p className="version-label">ATS-Optimized CV (Text Version)</p>
            <div className="cv-content">
              <CVRenderer cvData={optimized_cv} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ==================== HELPER FUNCTIONS ====================

function formatCategoryName(category) {
  return category
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function formatPriority(priority) {
  const labels = {
    critical: "🔴 CRITICAL",
    high: "🟠 HIGH",
    medium: "🟡 MEDIUM",
    low: "🟢 LOW",
  };
  return labels[priority] || priority;
}

function getSeverityClass(detail) {
  if (detail.includes("❌")) return "critical";
  if (detail.includes("⚠️")) return "warning";
  if (detail.includes("✅")) return "success";
  return "info";
}

function getScoreDescription(score) {
  if (score >= 90)
    return "Excellent! Your CV is highly optimized for ATS systems.";
  if (score >= 80) return "Good! Your CV should pass most ATS screens.";
  if (score >= 70)
    return "Fair. Some improvements would help your CV pass ATS screening.";
  if (score >= 60) return "Needs work. Several issues should be addressed.";
  return "Critical. Major changes needed to improve ATS compatibility.";
}

async function downloadCVVersion(cvData, version) {
  // Convert CV data to PDF and download
  // Implementation depends on your PDF library
}

// ==================== STYLING ====================

// CSS (use your styling system - Tailwind, styled-components, etc.)

const styles = `
.ats-score-container {
  max-width: 900px;
  padding: 2rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.overall-score {
  text-align: center;
  margin-bottom: 3rem;
  padding: 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: white;
}

.score-display {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin: 1rem 0;
}

.score {
  font-size: 3rem;
  font-weight: bold;
}

.score-A+ { color: #10b981; }
.score-A { color: #3b82f6; }
.score-B { color: #f59e0b; }
.score-C { color: #ef4444; }
.score-D { color: #7f1d1d; }

.breakdown-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin: 2rem 0;
}

.breakdown-item {
  padding: 1.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.score-bar {
  width: 100%;
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  margin: 0.5rem 0;
  overflow: hidden;
}

.score-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
}

.change-item {
  margin: 1rem 0;
  padding: 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.change-item:hover {
  background: #f9fafb;
  border-color: #667eea;
}

.before-after {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 1rem;
  margin: 1rem 0;
}

.before, .after {
  padding: 1rem;
  border-radius: 4px;
  background: #f3f4f6;
}

.before label, .after label {
  font-weight: bold;
  font-size: 0.85rem;
  color: #666;
}

.reason {
  padding: 1rem;
  background: #f0f9ff;
  border-left: 4px solid #3b82f6;
  border-radius: 4px;
}

.transparency-notice {
  margin-top: 2rem;
  padding: 1rem;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
  color: #166534;
  text-align: center;
}
`;
