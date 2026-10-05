"""
Trains the milk yield prediction model for the Smart Dairy Manager.

Source dataset: global_cattle_milk_yield_prediction_dataset.csv
(Kaggle: "Global Cattle Milk Yield Prediction Dataset")

KEY DESIGN DECISION:
The dominant predictor of a cow's yield on a given day is her OWN recent
history, not population-level breed/feed averages (confirmed empirically:
adding a "recent average yield" feature raised R^2 from 0.08 to 0.94 on
this dataset). This matches real dairy biology -- lactation curves are
smooth, so day-to-day yield is highly autocorrelated for an individual
cow. The model is therefore designed to predict a DEVIATION-aware
estimate: given a cow's recent baseline plus her current feed/milking
inputs, what should today's yield be -- which is exactly what the app's
advice logic needs (comparing actual vs. expected).

CAVEAT: this dataset's breed distribution is spread near-perfectly evenly
across every world region, a synthetic-generation artifact, not real
population geography. Its breed-level ABSOLUTE yield numbers (e.g.
Holstein-Friesian ~17.5L/day) reflect Western intensive systems, not
Rwandan smallholder conditions. The trained model's use of "breed" as a
categorical feature (its SHAPE of influence relative to other features)
is retained, but real Rwandan cold-start defaults (for cows with no log
history yet) come from published local research instead of this dataset
-- see BREED_PRIOR_YIELD_L in app/services/ml_service.py, sourced from
Manzi et al. (2020, 2022), RAB / University of Rwanda.
"""
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

SOURCE_CSV = "global_cattle_milk_yield_prediction_dataset.csv"
OUTPUT_PATH = "milk_yield_model.pkl"

BREED_MAP = {
    "Holstein-Friesian": "holstein_friesian",
    "Ankole": "ankole",
}
BREED_CATEGORIES = ["holstein_friesian", "ankole", "ankole_friesian_cross", "other"]

FEATURES = ["breed", "feed", "milking_times", "recent_avg_yield"]
TARGET = "total_milk"


def map_breed(raw_breed: str) -> str:
    return BREED_MAP.get(raw_breed, "other")


def main():
    print(f"Loading {SOURCE_CSV} ...")
    df = pd.read_csv(SOURCE_CSV)
    print(f"Loaded {len(df):,} rows")

    df["breed"] = df["Breed"].apply(map_breed)
    df["feed"] = df["Feed_Quantity_kg"]
    df["milking_times"] = (24 / df["Milking_Interval_hrs"]).round().astype(int)
    df["recent_avg_yield"] = df["Previous_Week_Avg_Yield"]
    df["total_milk"] = df["Milk_Yield_L"]

    print("\nMapped breed distribution:")
    print(df["breed"].value_counts())

    X = df[FEATURES]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("breed", OneHotEncoder(categories=[BREED_CATEGORIES], handle_unknown="ignore"), ["breed"]),
        ],
        remainder="passthrough",  # feed, milking_times, recent_avg_yield pass through unchanged, in this order
    )

    pipeline = Pipeline([
        ("preprocess", preprocessor),
        ("model", RandomForestRegressor(n_estimators=200, max_depth=12, random_state=42, n_jobs=-1)),
    ])

    print("\nTraining...")
    pipeline.fit(X_train, y_train)

    preds = pipeline.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)
    print(f"\nTest MAE: {mae:.2f} liters")
    print(f"Test R^2: {r2:.3f}")

    test_df = X_test.copy()
    test_df["actual"] = y_test.values
    test_df["predicted"] = preds
    print("\nPer-breed MAE on test set:")
    for breed in BREED_CATEGORIES:
        subset = test_df[test_df["breed"] == breed]
        if len(subset) > 0:
            breed_mae = mean_absolute_error(subset["actual"], subset["predicted"])
            print(f"  {breed}: MAE={breed_mae:.2f}L (n={len(subset)})")

    joblib.dump(pipeline, OUTPUT_PATH)
    print(f"\nModel saved to {OUTPUT_PATH}")
    print(f"Expected feature order at inference time: {FEATURES}")


if __name__ == "__main__":
    main()