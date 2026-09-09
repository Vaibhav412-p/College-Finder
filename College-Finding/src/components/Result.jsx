
function Results({ data, onBack }) {

  return (
    <section className="page result-page">

      <div className="result-background"></div>

      <div className="result-container">

        <div className="result-header">

          <div className="result-logo">
            🎓
          </div>

          <p className="result-tag">
            COLLEGE SEARCH RESULTS
          </p>

          <h1>
            Hello,{" "}
            <span>
              {data.name}
            </span>{" "}
            👋
          </h1>

          <p>
            Here are the colleges suitable for your profile.
            {data.predicted_merit_rank && (
              <> • Predicted Merit Rank: <strong>#{Number(data.predicted_merit_rank).toLocaleString()}</strong></>
            )}
          </p>

        </div>


        {/* Student Summary */}

        <div className="student-details">

          <div className="detail-card">
            <small>NAME</small>
            <strong>{data.name}</strong>
          </div>

          <div className="detail-card">
            <small>PERCENTAGE</small>
            <strong>{data.percentage}%</strong>
          </div>

          <div className="detail-card">
            <small>CATEGORY</small>
            <strong>{data.category}</strong>
          </div>

          <div className="detail-card">
            <small>BRANCH</small>
            <strong>{data.branch}</strong>
          </div>
          <div className="detail-card">
            <small>CAP ROUND</small>
            <strong>Round {data.round}</strong>
          </div>

        </div>


        {/* Results Title */}

        <div className="results-title">

          <h2>
            Suitable Colleges
          </h2>

          <span>
            {data.colleges.length} Colleges
          </span>

        </div>


        {/* Colleges */}

        <div className="college-results">

          {data.colleges.length === 0 ? (

            <div className="no-result">

              <h3>
                😔 No Matching College Found
              </h3>

              <p>
                Your Python program did not
                return any matching colleges.
              </p>

            </div>

          ) : (

            data.colleges.map(
              (college, index) => (

                <div
                  className="college-card"
                  key={index}
                >

                  <h3>
                    {college.name}
                  </h3>

                  <p className="city">
                    📍 {college.city}
                  </p>

                  <div className="college-info">

                    <div className="info-box">
                      <small>BRANCH</small>
                      <strong>
                        {college.branch}
                      </strong>
                    </div>

                    <div className="info-box">
                      <small>CATEGORY</small>
                      <strong>
                        {college.category}
                      </strong>
                    </div>

                    <div className="info-box">
                      <small>CUTOFF</small>
                      <strong>
                        {college.cutoff}%
                      </strong>
                    </div>

                    <div className="info-box">
                      <small>SEATS</small>
                      <strong>
                        {college.seats}
                      </strong>
                    </div>

                  </div>

                  <span className="eligible">
                    ✓ Eligible {college.chance ? `(${college.chance} Chance)` : ""}
                  </span>

                </div>

              )
            )

          )}

        </div>


        <button
          className="back-result-button"
          onClick={onBack}
        >
          ← Back to Student Information
        </button>

      </div>

    </section>
  );
}

export default Results;

