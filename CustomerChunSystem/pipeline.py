import pandas as pd
import pickle
from config import engine

def run_pipeline():

    df = pd.read_sql("SELECT * FROM Customers", engine)

    features = [
        "Tenure_in_Months",
        "Monthly_Charge",
        "Total_Revenue",
        "Age",
        "Number_of_Referrals",
        "Total_Charges",
        "Total_Refunds",
        "Total_Extra_Data_Charges",
        "Total_Long_Distance_Charges"
    ]

    df[features] = df[features].fillna(df[features].median())

    with open("models/churn_model.pkl","rb") as f:
        model = pickle.load(f)

    df["Churn_Prediction"] = model.predict(df[features])
    df["Churn_Probability"] = model.predict_proba(df[features])[:,1]

    df["Churn_Status_Predicted"] = df["Churn_Prediction"].map({
        0:"Stayed",
        1:"Churned"
    })

    df.to_sql("Customers_Predictions", engine, if_exists="replace", index=False)