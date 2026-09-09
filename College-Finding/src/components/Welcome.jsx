
function Welcome({ onStart }) {
  return (
    <section className="page welcome-page">

      <div className="glow glow-one"></div>
      <div className="glow glow-two"></div>

      {/* Floating Butterflies */}
      <div className="butterfly butterfly-one">🦋</div>
      <div className="butterfly butterfly-two">🦋</div>
      <div className="butterfly butterfly-three">🦋</div>

      {/* Education Objects */}
      <div className="education-icon book">📚</div>
      <div className="education-icon pencil">✏️</div>
      <div className="education-icon cap">🎓</div>
      <div className="education-icon bulb">💡</div>

      <div className="welcome-content">

        <div className="welcome-logo">
          🎓
        </div>

        <p className="welcome-tagline">
          AI POWERED EDUCATION
        </p>

        <h1>
          Welcome to
          <span> College Finder</span>
        </h1>

        <p className="welcome-description">
          Discover colleges that match your percentage,
          category and preferred branch.
          <br />
          Make your college search{" "}
          <strong>simple, smart and fast.</strong>
        </p>

        <button
          className="start-button"
          onClick={onStart}
        >
          Get Started
          <span>→</span>
        </button>

        <div className="welcome-features">

          <div>
            🎓
            <span>Smart Search</span>
          </div>

          <div>
            📊
            <span>Percentage Based</span>
          </div>

          <div>
            🏫
            <span>College Results</span>
          </div>

        </div>

      </div>
    </section>
  );
}

export default Welcome;

