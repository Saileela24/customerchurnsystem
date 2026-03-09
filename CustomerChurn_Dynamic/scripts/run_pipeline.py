from step1_fetch_data import fetch_data
from step2_predict_churn import make_predictions

def run_pipeline():
    print("Starting pipeline execution...")
    print("Step 1: Fetching data...")
    fetch_data()
    print("Step 2: Making predictions...")
    make_predictions()
    print("Pipeline completed successfully!")

if __name__ == "__main__":
    run_pipeline()
