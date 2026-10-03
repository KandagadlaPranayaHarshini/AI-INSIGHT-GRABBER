from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import pandas as pd
import numpy as np
import io

from database import engine, get_db, Base
import models, schemas

# Auto create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Insight Grabber")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "AI Insight Grabber Backend API is Running!"}

@app.post("/api/signup")
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = models.User(
        full_name=user.full_name,
        email=user.email,
        hashed_password=user.password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully", "user": {"id": new_user.id, "email": new_user.email}}

@app.post("/api/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or db_user.hashed_password != user.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    return {"message": "Login successful", "user": {"id": db_user.id, "email": db_user.email, "full_name": db_user.full_name}}

@app.post("/api/analyze")
async def analyze_dataset(
    file: UploadFile = File(...), 
    user_id: int = Form(1), 
    db: Session = Depends(get_db)
):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        db_user = db.query(models.User).first()
        if not db_user:
            raise HTTPException(status_code=400, detail="Please create a user account first.")
        user_id = db_user.id

    try:
        contents = await file.read()
        filename = file.filename.lower()

        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(contents))
        elif filename.endswith(".json"):
            df = pd.read_json(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")

        total_rows = int(len(df))
        total_cols = int(len(df.columns))
        missing_vals = int(df.isnull().sum().sum())
        duplicates_cnt = int(df.duplicated().sum())

        # Save Dataset Record
        db_dataset = models.Dataset(
            filename=file.filename,
            file_type=filename.split('.')[-1],
            row_count=total_rows,
            column_count=total_cols,
            missing_values=missing_vals,
            duplicate_rows=duplicates_cnt,
            user_id=user_id
        )
        db.add(db_dataset)
        db.commit()
        db.refresh(db_dataset)

        # 1. Calculate Summary Statistics
        numeric_df = df.select_dtypes(include=[np.number])
        stats_list = []

        for col in numeric_df.columns:
            mean_val = numeric_df[col].mean()
            median_val = numeric_df[col].median()
            std_val = numeric_df[col].std() if len(numeric_df[col]) > 1 else None
            min_val = numeric_df[col].min()
            max_val = numeric_df[col].max()

            stats_list.append({
                "column": str(col),
                "mean": round(float(mean_val), 2) if pd.notnull(mean_val) else None,
                "median": round(float(median_val), 2) if pd.notnull(median_val) else None,
                "std_dev": round(float(std_val), 2) if pd.notnull(std_val) else None,
                "min": round(float(min_val), 2) if pd.notnull(min_val) else None,
                "max": round(float(max_val), 2) if pd.notnull(max_val) else None
            })

        # 2. Generate Default Chart Configurations
        charts_data = {}
        all_cols = list(df.columns)
        num_cols = list(numeric_df.columns)

        if len(all_cols) > 0:
            # Bar Chart: Frequency distribution of 1st column or 1st categorical column
            cat_col = next((c for c in df.columns if df[c].dtype == 'object'), all_cols[0])
            val_counts = df[cat_col].value_counts().head(10)
            charts_data["bar"] = {
                "title": f"Top 10 Categories in {cat_col}",
                "labels": list(val_counts.index.astype(str)),
                "data": list(val_counts.values.astype(float))
            }

        if len(num_cols) > 0:
            # Line / Histogram Chart: Distribution of 1st numeric column
            target_num = num_cols[0]
            sample_data = numeric_df[target_num].dropna().head(30)
            charts_data["line"] = {
                "title": f"Trend of {target_num} (First 30 Samples)",
                "labels": [f"Row {i+1}" for i in range(len(sample_data))],
                "data": [round(float(x), 2) for x in sample_data]
            }

        return {
            "dataset_id": db_dataset.id,
            "filename": file.filename,
            "rows": total_rows,
            "columns": total_cols,
            "missing_values": missing_vals,
            "duplicates": duplicates_cnt,
            "statistics": stats_list,
            "charts": charts_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing file: {str(e)}")