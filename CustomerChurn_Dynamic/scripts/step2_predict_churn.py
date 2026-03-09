import pandas as pd
import pickle
from pathlib import Path

def make_predictions():
    try:
        # File paths
        data_path = Path.cwd() / 'data' / 'fetched_data.xlsx'
        model_path = Path.cwd() / 'models' / 'churn_model_smoteenn.pkl'
        output_path = Path.cwd() / 'data' / 'predictions.xlsx'

        # Validate input files
        if not data_path.exists():
            raise FileNotFoundError(f"Data file missing at {data_path}")
        if not model_path.exists():
            raise FileNotFoundError(f"Model file missing at {model_path}")

        # Load data and model
        df = pd.read_excel(data_path)
        print(f"Loaded {len(df)} rows")

        with open(model_path, 'rb') as f:
            model = pickle.load(f)

        # Features used for prediction
        features = ['Tenure_in_Months', 'Monthly_Charge', 'Total_Revenue']
        missing_cols = [col for col in features if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing columns in data: {missing_cols}")

        # Handle missing values
        df[features] = df[features].fillna(df[features].median())

        # Make predictions
        df['Churn_Prediction'] = model.predict(df[features])  # <-- renamed here
        df['Churn_Probability'] = model.predict_proba(df[features])[:, 1]
        df['Churn_Status_Predicted'] = df['Churn_Prediction'].map({0: 'Stayed', 1: 'Churned'})

        # Save to Excel
        output_path.parent.mkdir(exist_ok=True)
        df.to_excel(output_path, index=False)

        print(f"✅ Predictions saved to {output_path}")
        print(df['Churn_Status_Predicted'].value_counts())

    except Exception as e:
        print(f"❌ Prediction failed: {e}")

if __name__ == "__main__":
    make_predictions()
