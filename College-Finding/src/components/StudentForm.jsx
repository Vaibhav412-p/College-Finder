
import { useState } from "react";

function StudentForm({ onBack, onSubmit }) {

  const [name, setName] = useState("");
  const [percentage, setPercentage] = useState("");
  const [category, setCategory] = useState("");
  const [branch, setBranch] = useState("");
  const [round, setRound] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();

    const percent = Number(percentage);

    if (!name || !category || !branch || !round) {
      alert("Please fill all information.");
      return;
    }

    if (
      Number.isNaN(percent) ||
      percent < 0 ||
      percent > 100
    ) {
      alert("Percentage must be between 0 and 100.");
      return;
    }

    onSubmit({
      name,
      percentage: percent,
      category,
      branch,
      round,
    });
  };

  return (
    <section className="page student-page">

      <div className="grid-background"></div>

      {/* Floating Education Objects */}

      <div className="floating-book">
        📓
      </div>

      <div className="floating-book book-two">
        📖
      </div>

      <div className="floating-pencil">
        ✏️
      </div>

      <div className="floating-cap">
        🎓
      </div>

      <div className="floating-bulb">
        💡
      </div>


      <div className="student-container">

        <div className="page-header">

          <div className="small-logo">
            🎓
          </div>

          <p className="profile-title">
            STUDENT PROFILE
          </p>

          <div className="information-title">
            Enter Your Information
          </div>

          <p className="header-description">
            Enter your academic information and find suitable colleges.
          </p>

        </div>


        <div className="form-box">

          <form onSubmit={handleSubmit}>

            {/* Name */}

            <div className="input-group">

              <label>
                👤 Student Name
              </label>

              <input
                type="text"
                placeholder="Enter your full name"
                value={name}
                onChange={(e) =>
                  setName(e.target.value)
                }
                required
              />

            </div>


            {/* Percentage */}

            <div className="input-group">

              <label>
                📊 Percentage
              </label>

              <input
                type="number"
                placeholder="Example: 72.50"
                min="0"
                max="100"
                step="0.01"
                value={percentage}
                onChange={(e) =>
                  setPercentage(e.target.value)
                }
                required
              />

            </div>


            {/* Category */}

            <div className="input-group">

              <label>
                🏷️ Category
              </label>

              <select
                value={category}
                onChange={(e) =>
                  setCategory(e.target.value)
                }
                required
              >

                <option value="">
                  Select Category
                </option>

                <option value="OPEN">
                  OPEN
                </option>

                <option value="OBC">
                  OBC
                </option>

                <option value="SC">
                  SC
                </option>

                <option value="ST">
                  ST
                </option>

                <option value="EWS">
                  EWS
                </option>

                <option value="NT">
                  NT
                </option>

              </select>

            </div>


            {/* Branch */}

            <div className="input-group">

              <label>
                💻 Preferred Branch
              </label>

              <select
                value={branch}
                onChange={(e) =>
                  setBranch(e.target.value)
                }
                required
              >

                <option value="">
                  Select Branch
                </option>

                <option value="Computer Science">
                  Computer Science
                </option>

                <option value="AI & DS">
                  AI & Data Science
                </option>

                <option value="AI & ML">
                  AI & Machine Learning
                </option>

                <option value="Information Technology">
                  Information Technology
                </option>

                <option value="Electronics">
                  Electronics
                </option>

                <option value="Mechanical">
                  Mechanical
                </option>

                <option value="Civil">
                  Civil
                </option>

              </select>

            </div>


            {/* CAP Round */}

            <div className="input-group">

              <label>
                🎯 CAP Round
              </label>

              <select
                value={round}
                onChange={(e) =>
                  setRound(e.target.value)
                }
                required
              >

                <option value="">
                  Select CAP Round
                </option>

                <option value="1">
                  CAP Round 1
                </option>

                <option value="2">
                  CAP Round 2
                </option>

                <option value="3">
                  CAP Round 3
                </option>

                <option value="4">
                  CAP Round 4
                </option>

              </select>

            </div>


            {/* Buttons */}

            <div className="form-buttons">

              <button
                type="button"
                className="back-form-button"
                onClick={onBack}
              >
                ← Back
              </button>

              <button
                type="submit"
                className="find-button"
              >
                Find Colleges
                <span>→</span>
              </button>

            </div>

          </form>

        </div>

      </div>

    </section>
  );
}

export default StudentForm;

