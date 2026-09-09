import os
import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator, model_validator


# =====================================================================
# PATH RESOLUTION HELPERS
# =====================================================================
BASE_DIR = Path(__file__).resolve().parent

def resolve_file(filename: str, subfolder: str = "") -> Path:
    """
    Safely locates a file in:
    1. BASE_DIR / subfolder / filename
    2. BASE_DIR / filename
    3. BASE_DIR.parent / "database" / filename
    4. BASE_DIR.parent / subfolder / filename
    """
    search_paths = [
        BASE_DIR / subfolder / filename if subfolder else BASE_DIR / filename,
        BASE_DIR / filename,
        BASE_DIR.parent / "database" / filename,
        BASE_DIR.parent / subfolder / filename if subfolder else BASE_DIR / filename,
    ]
    for p in search_paths:
        if p.exists() and p.is_file():
            return p
    raise FileNotFoundError(
        f"Critical file '{filename}' not found. Searched paths:\n"
        + "\n".join(f" - {p}" for p in search_paths)
    )


# =====================================================================
# NORMALIZATION MAPS & FUNCTIONS
# =====================================================================

CATEGORY_MAP = {
    "open": "OPEN",
    "general": "OPEN",
    "gen": "OPEN",
    "obc": "OBC",
    "obc category": "OBC",
    "sc": "SC",
    "st": "ST",
    "ews": "EWS",
    "nt": "NT",
    "nt1": "NT",
    "nt2": "NT",
    "nt3": "NT",
    "vj": "NT",
    "vjnt": "NT",
    "tfws": "TFWS",
}

# Mapping normalized category to primary MHT-CET CAP seat_category one-hot code
SEAT_CATEGORY_MAP = {
    "OPEN": "GOPENS",
    "OBC": "GOBCS",
    "SC": "GSCS",
    "ST": "GSTS",
    "EWS": "EWS",
    "NT": "GNT1S",
    "TFWS": "TFWS",
}

BRANCH_MAP = {
    "cse": "Computer Engineering",
    "cs": "Computer Engineering",
    "computer": "Computer Engineering",
    "computer science": "Computer Engineering",
    "computer engineering": "Computer Engineering",
    "computer science and engineering": "Computer Science and Engineering",
    
    "it": "Information Technology",
    "information technology": "Information Technology",
    
    "entc": "Electronics and Telecommunication Engg",
    "e&tc": "Electronics and Telecommunication Engg",
    "electronics and telecommunication": "Electronics and Telecommunication Engg",
    "electronics and telecommunication engineering": "Electronics and Telecommunication Engg",
    
    "ai": "Artificial Intelligence",
    "artificial intelligence": "Artificial Intelligence",
    
    "ai&ds": "Artificial Intelligence and Data Science",
    "aids": "Artificial Intelligence and Data Science",
    "ai & ds": "Artificial Intelligence and Data Science",
    "ai & data science": "Artificial Intelligence and Data Science",
    "artificial intelligence and data science": "Artificial Intelligence and Data Science",
    "artificial intelligence (ai) and data science": "Artificial Intelligence (AI) and Data Science",
    
    "ai&ml": "Artificial Intelligence and Machine Learning",
    "aiml": "Artificial Intelligence and Machine Learning",
    "ai & ml": "Artificial Intelligence and Machine Learning",
    "ai & machine learning": "Artificial Intelligence and Machine Learning",
    "artificial intelligence and machine learning": "Artificial Intelligence and Machine Learning",
    
    "ds": "Data Science",
    "data science": "Data Science",
    
    "ece": "Electronics Engineering",
    "electronics": "Electronics Engineering",
    "electronics engineering": "Electronics Engineering",
    
    "electrical": "Electrical Engineering",
    "electrical engineering": "Electrical Engineering",
    
    "mechanical": "Mechanical Engineering",
    "mechanical engineering": "Mechanical Engineering",
    
    "civil": "Civil Engineering",
    "civil engineering": "Civil Engineering",
    
    "chemical": "Chemical Engineering",
    "chemical engineering": "Chemical Engineering",
    
    "automobile": "Automobile Engineering",
    "automobile engineering": "Automobile Engineering",
    
    "biotechnology": "Biotechnology",
    "biotech": "Biotechnology",
    
    "production": "Production Engineering",
    "production engineering": "Production Engineering",
    
    "industrial": "Industrial IoT",
    "industrial engineering": "Industrial IoT",
    
    "instrumentation": "Instrumentation Engineering",
    "instrumentation engineering": "Instrumentation Engineering",
}

def normalize_category(raw_cat: str, valid_seat_cats: set) -> tuple[str, str]:
    """
    Returns (normalized_display_category, seat_category_for_model).
    """
    cleaned = raw_cat.strip()
    upper = cleaned.upper()
    lower = cleaned.lower()

    # If already a valid seat category code directly present in model columns
    if upper in valid_seat_cats:
        # Determine display category
        display = "OPEN"
        for k, v in SEAT_CATEGORY_MAP.items():
            if v == upper:
                display = k
                break
        return display, upper

    norm_display = CATEGORY_MAP.get(lower, upper)
    seat_cat = SEAT_CATEGORY_MAP.get(norm_display, "GOPENS")
    return norm_display, seat_cat

def normalize_branch(raw_branch: str, valid_branches: list[str]) -> str:
    cleaned = raw_branch.strip()
    lower = cleaned.lower()

    if lower in BRANCH_MAP:
        return BRANCH_MAP[lower]

    # Check for direct match among valid model branches
    for b in valid_branches:
        if cleaned.lower() == b.lower():
            return b

    # Fuzzy / substring match
    for b in valid_branches:
        if lower in b.lower():
            return b

    # Default fallback
    return "Computer Engineering"

def normalize_round(raw_round: Union[str, int]) -> str:
    r_str = str(raw_round).strip()
    if r_str in {"1", "2", "3", "4"}:
        return r_str
    match = re.search(r"[1-4]", r_str)
    if match:
        return match.group(0)
    return "1"

def extract_city_from_college(college_name: str) -> str:
    """Extracts city from college name (typically after the last comma or district suffix)."""
    parts = [p.strip() for p in college_name.split(",") if p.strip()]
    if len(parts) > 1:
        last = parts[-1]
        # Clean up common words
        clean_city = re.sub(r"(?i)\b(dist|tal|district|taluka|near|road)\b.*", "", last).strip()
        if clean_city:
            return clean_city
    # Known cities
    for city in ["Pune", "Mumbai", "Nagpur", "Nashik", "Amravati", "Aurangabad", "Chhatrapati Sambhajinagar", "Kolhapur", "Sangli", "Thane", "Nanded", "Solapur", "Jalgaon"]:
        if city.lower() in college_name.lower():
            return city
    return "Maharashtra"


# =====================================================================
# FASTAPI APP & LIFESPAN (MODEL + DATA LOADING)
# =====================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n=======================================================")
    print("[*] Initializing MHT-CET College Predictor Backend...")
    print("=======================================================")

    # 1. Locate files
    catboost_path = resolve_file("catboost_rank_predict.pkl", "models")
    rf_model_path = resolve_file("random_forest_college_model_2023.pkl", "models")
    rf_columns_path = resolve_file("random_forest_columns_2023.pkl", "models")
    csv_path = resolve_file("mht_cet_cap_cutoffs_2023_2024_all_rounds.csv", "data")

    print(f"[-] CatBoost Model:  {catboost_path}")
    print(f"[-] RF Model:        {rf_model_path}")
    print(f"[-] RF Columns:      {rf_columns_path}")
    print(f"[-] Cutoff Dataset:  {csv_path}")

    # 2. Load CatBoost Rank Model
    try:
        rank_model = joblib.load(catboost_path)
        app.state.rank_model = rank_model
        print("[+] CatBoost Rank Model loaded successfully.")
    except Exception as e:
        raise RuntimeError(f"Failed to load CatBoost rank model from '{catboost_path}': {e}") from e

    # 3. Load Random Forest Columns
    try:
        rf_columns = joblib.load(rf_columns_path)
        app.state.rf_columns = rf_columns
        # Cache valid seat categories & branches for fast normalization
        app.state.valid_seat_cats = {
            c.replace("seat_category_", "") for c in rf_columns if c.startswith("seat_category_")
        }
        app.state.valid_branches = [
            c.replace("branch_", "") for c in rf_columns if c.startswith("branch_")
        ]
        print(f"[+] RF Columns loaded ({len(rf_columns)} features).")
    except Exception as e:
        raise RuntimeError(f"Failed to load RF columns from '{rf_columns_path}': {e}") from e

    # 4. Load Random Forest Cutoff Model
    try:
        rf_model = joblib.load(rf_model_path)
        app.state.rf_model = rf_model
        print("[+] Random Forest Cutoff Model loaded successfully.")
    except Exception as e:
        raise RuntimeError(f"Failed to load Random Forest model from '{rf_model_path}': {e}") from e

    # 5. Load CSV Dataset & Validate Required Columns
    try:
        df_csv = pd.read_csv(csv_path)
        required_cols = {"college", "branch", "seat_category", "round", "cutoff_percentile"}
        missing = required_cols - set(df_csv.columns)
        if missing:
            raise ValueError(f"Cutoff CSV is missing required columns: {missing}")

        unique_colleges = df_csv["college"].dropna().unique().tolist()
        if not unique_colleges:
            raise ValueError("No colleges found in cutoff CSV dataset.")

        app.state.unique_colleges = unique_colleges
        app.state.colleges_by_round = {
            str(round_number): sorted(
                df_csv.loc[
                    df_csv["round"].astype(str).str.extract(r"([1-4])", expand=False) == str(round_number),
                    "college",
                ].dropna().unique().tolist()
            )
            for round_number in range(1, 5)
        }
        # Precompute city lookup for unique colleges
        app.state.college_cities = {c: extract_city_from_college(c) for c in unique_colleges}

        print(f"[+] Cutoff CSV loaded ({len(df_csv):,} rows, {len(unique_colleges)} unique colleges).")
    except Exception as e:
        raise RuntimeError(f"Failed to load/validate cutoff CSV dataset from '{csv_path}': {e}") from e

    print("[*] Backend initialization complete. Server is ready!")
    print("=======================================================\n")

    yield

    print("[*] Shutting down MHT-CET College Predictor Backend...")


app = FastAPI(
    title="MHT-CET College Predictor API",
    description="Machine learning-powered college cutoff predictor and merit rank estimator.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================================
# REQUEST & RESPONSE SCHEMAS
# =====================================================================

class PredictRequest(BaseModel):
    name: str = Field(..., description="Student's name (required, non-empty)")
    percentile: Optional[float] = Field(None, description="MHT-CET Percentile (0 to 100)")
    percentage: Optional[float] = Field(None, description="Alternative alias for percentile")
    category: str = Field(..., description="Student category (e.g., OPEN, OBC, SC, ST, EWS)")
    branch: str = Field(..., description="Preferred branch (e.g., CSE, IT, AI&DS, Mechanical)")
    round: Union[str, int] = Field(default="1", description="CAP round number (1, 2, 3, or 4)")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Name is required and cannot be empty.")
        return s

    @model_validator(mode="after")
    def validate_percentile_value(self) -> "PredictRequest":
        # Resolve percentile from either `percentile` or `percentage`
        val = self.percentile if self.percentile is not None else self.percentage
        if val is None:
            raise ValueError("Percentile is required.")
        if not isinstance(val, (int, float)) or np.isnan(val):
            raise ValueError("Percentile must be a valid number.")
        if val < 0.0 or val > 100.0:
            raise ValueError(f"Percentile must be between 0 and 100. Received: {val}")
        self.percentile = float(val)
        return self


class CollegeItem(BaseModel):
    college: str
    name: str
    city: str
    branch: str
    category: str
    predicted_cutoff: float
    cutoff: float
    your_percentile: float
    difference: float
    chance: str
    seats: Union[int, str]


class StudentInfo(BaseModel):
    name: str
    percentile: float
    predicted_merit_rank: int
    category: str
    branch: str
    round: str


class PredictResponse(BaseModel):
    success: bool
    student: StudentInfo
    top_10_colleges: List[CollegeItem]
    colleges: List[CollegeItem]


# =====================================================================
# ROUTES
# =====================================================================

@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "online",
        "message": "MHT-CET College Predictor API",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
    }


@app.post("/predict", response_model=PredictResponse, tags=["Prediction"])
async def predict_colleges(req: PredictRequest, request: Request):
    """
    Main prediction endpoint:
    1. Normalizes category, branch, and round.
    2. Predicts merit rank using the pre-trained CatBoost model.
    3. Builds input vector across all unique colleges.
    4. Predicts cutoff percentiles using Random Forest.
    5. Calculates difference & admission chance (HIGH, GOOD, MODERATE, LOW).
    6. Returns the top 10 best-matching colleges.
    """
    try:
        rank_model = request.app.state.rank_model
        rf_model = request.app.state.rf_model
        rf_columns = request.app.state.rf_columns
        valid_seat_cats = request.app.state.valid_seat_cats
        valid_branches = request.app.state.valid_branches
        unique_colleges = request.app.state.unique_colleges
        colleges_by_round = request.app.state.colleges_by_round
        college_cities = request.app.state.college_cities
    except AttributeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML models or datasets are not loaded yet. Please wait or check backend startup logs.",
        ) from e

    # 1. Input normalization
    norm_category, seat_category = normalize_category(req.category, valid_seat_cats)
    norm_branch = normalize_branch(req.branch, valid_branches)
    norm_round = normalize_round(req.round)
    student_percentile = float(req.percentile)
    round_colleges = colleges_by_round.get(norm_round, [])

    # 2. Predict Merit Rank using CatBoost
    try:
        rank_pred = rank_model.predict([[student_percentile]])
        predicted_merit_rank = int(round(float(rank_pred[0])))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error predicting merit rank with CatBoost model: {e}",
        ) from e

    if not round_colleges:
        student_summary = StudentInfo(
            name=req.name,
            percentile=student_percentile,
            predicted_merit_rank=predicted_merit_rank,
            category=norm_category,
            branch=norm_branch,
            round=norm_round,
        )
        return PredictResponse(
            success=True,
            student=student_summary,
            top_10_colleges=[],
            colleges=[],
        )

    # 3. Build model input for all colleges
    num_colleges = len(round_colleges)
    input_df = pd.DataFrame({
        "college": round_colleges,
        "branch": [norm_branch] * num_colleges,
        "seat_category": [seat_category] * num_colleges,
        "round": [norm_round] * num_colleges,
        "merit_rank": [predicted_merit_rank] * num_colleges,
    })

    # Ensure categorical columns are strings
    for col in ["college", "branch", "seat_category", "round"]:
        input_df[col] = input_df[col].astype(str)

    # 4. One-hot encoding & align columns with RF features
    try:
        encoded_df = pd.get_dummies(input_df)
        encoded_df = encoded_df.reindex(columns=rf_columns, fill_value=0)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error encoding input features for Random Forest: {e}",
        ) from e

    # 5. Predict cutoffs with Random Forest
    try:
        cutoffs = rf_model.predict(encoded_df)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running Random Forest cutoff prediction: {e}",
        ) from e

    # 6. Calculate differences & chance
    results = []
    for college_name, pred_cutoff in zip(round_colleges, cutoffs):
        diff = student_percentile - pred_cutoff

        # Chance calculation rule
        if diff >= 3.0:
            chance = "HIGH"
        elif diff >= 0.0:
            chance = "GOOD"
        elif diff >= -3.0:
            chance = "MODERATE"
        else:
            chance = "LOW"

        cutoff_rounded = round(float(pred_cutoff), 2)
        diff_rounded = round(float(diff), 2)

        results.append({
            "college": college_name,
            "name": college_name,
            "city": college_cities.get(college_name, "Maharashtra"),
            "branch": norm_branch,
            "category": norm_category,
            "predicted_cutoff": cutoff_rounded,
            "cutoff": cutoff_rounded,
            "your_percentile": student_percentile,
            "difference": diff_rounded,
            "abs_diff": abs(diff),
            "chance": chance,
            "seats": 60,
        })

    # 7. Sort by absolute difference and take top 10
    results.sort(key=lambda x: x["abs_diff"])
    top_10 = results[:10]

    # Clean up internal sorting helper key
    cleaned_top_10 = []
    for item in top_10:
        item_copy = dict(item)
        item_copy.pop("abs_diff", None)
        cleaned_top_10.append(CollegeItem(**item_copy))

    student_summary = StudentInfo(
        name=req.name,
        percentile=student_percentile,
        predicted_merit_rank=predicted_merit_rank,
        category=norm_category,
        branch=norm_branch,
        round=norm_round,
    )

    return PredictResponse(
        success=True,
        student=student_summary,
        top_10_colleges=cleaned_top_10,
        colleges=cleaned_top_10,
    )


@app.post("/api/find-colleges", response_model=PredictResponse, tags=["Prediction"])
async def find_colleges_alias(req: PredictRequest, request: Request):
    """
    Backward-compatible alias for existing frontend client callers.
    """
    return await predict_colleges(req, request)


# =====================================================================
# ENTRY POINT
# =====================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
