import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from imblearn.combine import SMOTEENN
import pickle
from pathlib import Path
from collections import Counter
from sklearn.metrics import classification_report

def train_model():
    try:
        data_path = Path.cwd() / 'data' / 'fetched_data.xlsx'
        if not data_path.exists():
            raise FileNotFoundError(f"Data file not found at {data_path}")

        df = pd.read_excel(data_path)

        required_statuses = {'Stayed', 'Churned'}
        statuses_present = set(df['Customer_Status'].unique())
        if not required_statuses.issubset(statuses_present):
            raise ValueError(f"Data must contain 'Customer_Status' with values {required_statuses}. Found: {statuses_present}")

        df = df[df['Customer_Status'].isin(required_statuses)].copy()
        df['Churn'] = df['Customer_Status'].map({'Stayed': 0, 'Churned': 1})

        if len(df) < 50:
            raise ValueError("Not enough records to train, minimum 50 required.")

        features = [
            'Tenure_in_Months',
            'Monthly_Charge',
            'Total_Revenue',
        ]

        missing_feats = [f for f in features if f not in df.columns]
        if missing_feats:
            raise ValueError(f"Missing feature columns in data: {missing_feats}")

        df[features] = df[features].fillna(df[features].median())

        X = df[features]
        y = df['Churn']

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42, stratify=y
        )

        print("Class distribution before SMOTEENN:", Counter(y_train))

        smote_enn = SMOTEENN(random_state=42)
        X_resampled, y_resampled = smote_enn.fit_resample(X_train, y_train)

        print("Class distribution after SMOTEENN:", Counter(y_resampled))

        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            random_state=42,
            class_weight='balanced'
        )
        model.fit(X_resampled, y_resampled)

        y_pred = model.predict(X_test)
        print("\nModel classification report on test set:")
        print(classification_report(y_test, y_pred))

        model_dir = Path.cwd() / 'models'
        model_dir.mkdir(exist_ok=True)
        model_path = model_dir / 'churn_model_smoteenn.pkl'

        with open(model_path, 'wb') as f:
            pickle.dump(model, f)

        print(f"\n✅ Model trained and saved at {model_path}")
        print(f"Test set churn rate: {y_test.mean():.2%}")
        print(f"Training samples after SMOTEENN: {len(X_resampled)}")

    except Exception as e:
        print(f"❌ Training failed: {e}")

if __name__ == "__main__":
    train_model()
