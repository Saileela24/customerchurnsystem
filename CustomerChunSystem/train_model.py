import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from imblearn.combine import SMOTEENN

def train_model():

    df = pd.read_csv("data/fetched_data.csv")

    df = df[df["Customer_Status"].isin(["Stayed","Churned"])]
    df["Churn"] = df["Customer_Status"].map({"Stayed":0,"Churned":1})

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

    X = df[features]
    y = df["Churn"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    smote = SMOTEENN(random_state=42)
    X_res, y_res = smote.fit_resample(X_train, y_train)

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=8,
        random_state=42,
        class_weight="balanced"
    )

    model.fit(X_res, y_res)

    print(classification_report(y_test, model.predict(X_test)))

    with open("models/churn_model.pkl", "wb") as f:
        pickle.dump(model, f)

    print("✅ Model Trained & Saved")

if __name__ == "__main__":
    train_model()