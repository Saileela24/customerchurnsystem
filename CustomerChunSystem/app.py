import os
import pandas as pd
import plotly.express as px
import pickle
from flask import Flask, render_template, redirect, url_for, request, send_file
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin
from config import engine
from pipeline import run_pipeline

app = Flask(__name__)
app.secret_key = "super_secret_key"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- LOGIN ----------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin":
            login_user(User(1))
            return redirect(url_for("upload"))
        return "Invalid credentials"
    return render_template("login.html")

# ---------------- UPLOAD ----------------
@app.route("/upload", methods=["GET","POST"])
@login_required
def upload():
    if request.method == "POST":
        file = request.files["file"]
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        df = pd.read_csv(file_path)
        df.to_sql("Customers", engine, if_exists="replace", index=False)

        return redirect(url_for("dashboard"))
    return render_template("upload.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
@login_required
def dashboard():

    run_pipeline()
    df = pd.read_sql("SELECT * FROM Customers_Predictions", engine)

    if df.empty:
        return render_template("dashboard.html")

    total = len(df)
    churned = len(df[df["Churn_Status_Predicted"]=="Churned"])
    churn_rate = round((churned/total)*100,2)

    df["Revenue_At_Risk"] = df["Total_Revenue"] * df["Churn_Probability"]
    total_revenue_risk = round(df["Revenue_At_Risk"].sum(),2)

    # Risk segmentation
      # Ensure Churn_Probability exists
    if "Churn_Probability" not in df.columns:
       df["Churn_Probability"] = 0.5

# Create Risk Level
    df["Risk_Level"] = pd.cut(
       df["Churn_Probability"],
    bins=[0, 0.3, 0.6, 1],
    labels=["Low", "Medium", "High"],
    include_lowest=True
)

# Build Risk Chart
    risk_counts = df["Risk_Level"].value_counts().reset_index()
    risk_counts.columns = ["Risk_Level", "Count"]

    risk_chart = px.bar(
    risk_counts,
    x="Risk_Level",
    y="Count",
    title="Customer Risk Segmentation",
    category_orders={"Risk_Level": ["Low", "Medium", "High"]}
).to_html(full_html=False)
    # Churn by Contract
    contract_chart = px.pie(
        df[df["Churn_Status_Predicted"]=="Churned"]
        .groupby("Contract")
        .size().reset_index(name="Count"),
        names="Contract", values="Count",
        title="Churn by Contract"
    ).to_html(False)

    # Churn by Category
    category_chart = px.bar(
        df[df["Customer_Status"]=="Churned"]
        .groupby("Churn_Category")
        .size().reset_index(name="Count"),
        x="Churn_Category", y="Count",
        title="Churn by Category"
    ).to_html(False)

    # Revenue Loss by Reason
    reason_revenue_chart = px.bar(
        df[df["Customer_Status"]=="Churned"]
        .groupby("Churn_Reason")["Total_Revenue"]
        .sum().reset_index(),
        x="Churn_Reason", y="Total_Revenue",
        title="Revenue Loss by Reason"
    ).to_html(False)

    # Sector Impact
    sector_chart = px.bar(
        df[df["Customer_Status"]=="Churned"]
        .groupby("Internet_Type")
        .size().reset_index(name="Count"),
        x="Internet_Type", y="Count",
        title="Churn by Internet Type"
    ).to_html(False)

    # Future Forecast
    df["Future_Prob_6M"] = (df["Churn_Probability"]*1.2).clip(0,1)
    forecast_chart = px.histogram(
        df, x="Future_Prob_6M",
        title="6 Month Churn Forecast"
    ).to_html(False)

    # Feature Importance
    with open("models/churn_model.pkl","rb") as f:
        model = pickle.load(f)

    importance_df = pd.DataFrame({
        "Feature": model.feature_names_in_,
        "Importance": model.feature_importances_
    }).sort_values("Importance",ascending=False)

    feature_importance_chart = px.bar(
        importance_df.head(10),
        x="Importance", y="Feature",
        orientation="h",
        title="Feature Importance"
    ).to_html(False)

    # High Risk Customers
    high_risk = df[df["Churn_Probability"]>0.7]\
        .sort_values("Churn_Probability",ascending=False)\
        .head(15)

    high_risk_table = high_risk[[
        "Customer_ID",
        "Monthly_Charge",
        "Total_Revenue",
        "Churn_Probability"
    ]].to_html(index=False)

    # Smart Advice
    advice = []
    if churn_rate > 25:
        advice.append("Critical churn level. Immediate retention needed.")
    if total_revenue_risk > 100000:
        advice.append("High revenue exposure. Focus on premium customers.")
    if len(high_risk) > 0:
        advice.append("Engage high-risk customers with offers.")

    return render_template(
        "dashboard.html",
        total=total,
        churned=churned,
        churn_rate=churn_rate,
        total_revenue_risk=total_revenue_risk,
        risk_chart=risk_chart,
        contract_chart=contract_chart,
        category_chart=category_chart,
        reason_revenue_chart=reason_revenue_chart,
        sector_chart=sector_chart,
        forecast_chart=forecast_chart,
        feature_importance_chart=feature_importance_chart,
        high_risk_table=high_risk_table,
        advice=advice
    )

# ---------------- DOWNLOAD ----------------
@app.route("/download")
@login_required
def download():
    df = pd.read_sql("SELECT * FROM Customers_Predictions", engine)
    file_path = "churn_predictions.xlsx"
    df.to_excel(file_path,index=False)
    return send_file(file_path, as_attachment=True)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)