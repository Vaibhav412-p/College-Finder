
import { useState } from "react";
import Welcome from "./components/Welcome";
import StudentForm from "./components/StudentForm";
import Results from "./components/Result";
import "./App.css";

function App() {
  const [page, setPage] = useState("welcome");
  const [resultData, setResultData] = useState(null);
  const [loading, setLoading] = useState(false);

  const findColleges = async (studentData) => {
    setLoading(true);

    try {
      const payload = {
        name: studentData.name,
        percentile: Number(studentData.percentage ?? studentData.percentile),
        category: studentData.category,
        branch: studentData.branch,
        round: String(studentData.round || "1"),
      };

      const response = await fetch(
        "http://127.0.0.1:8000/predict",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        }
      );

      if (!response.ok) {
        const errData = await response.json().catch(() => null);
        const detailMsg = errData?.detail
          ? (typeof errData.detail === "string" ? errData.detail : JSON.stringify(errData.detail))
          : `Server returned status ${response.status}`;
        throw new Error(detailMsg);
      }

      const data = await response.json();
      const collegesList = data.top_10_colleges || data.colleges || [];

      setResultData({
        ...studentData,
        name: data.student?.name || studentData.name,
        percentage: data.student?.percentile ?? studentData.percentage,
        predicted_merit_rank: data.student?.predicted_merit_rank,
        category: data.student?.category || studentData.category,
        branch: data.student?.branch || studentData.branch,
        round: data.student?.round || "1",
        colleges: collegesList,
      });

      setPage("results");
    } catch (error) {
      console.error("Prediction Error:", error);

      alert(
        "Unable to connect to prediction server.\n\n" +
        "Please start the Python backend.\n\n" +
        "Details: " + (error.message || error)
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {page === "welcome" && (
        <Welcome
          onStart={() => setPage("student")}
        />
      )}

      {page === "student" && (
        <StudentForm
          onBack={() => setPage("welcome")}
          onSubmit={findColleges}
        />
      )}

      {page === "results" && resultData && (
        <Results
          data={resultData}
          onBack={() => setPage("student")}
        />
      )}

      {loading && (
        <div className="loading-overlay">
          <div className="loading-box">
            <div className="spinner"></div>

            <h2>Finding Suitable Colleges...</h2>

            <p>
              Connecting to your college database
            </p>
          </div>
        </div>
      )}
    </>
  );
}

export default App;
