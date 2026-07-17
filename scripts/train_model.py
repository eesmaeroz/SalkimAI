import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import r2_score, mean_squared_error
from xgboost import XGBRegressor

def main():
    print("Loading data...")
    df = pd.read_csv("data/raw/greenhouse_dataset.csv")

    features = [
        'crop_type', 'variety', 'avg_temperature_C', 'min_temperature_C', 
        'max_temperature_C', 'humidity_percent', 'co2_ppm', 'light_intensity_lux', 
        'photoperiod_hours', 'irrigation_mm', 'fertilizer_N_kg_ha', 
        'fertilizer_P_kg_ha', 'fertilizer_K_kg_ha', 'pest_severity', 'soil_pH'
    ]
    
    target_maturity = 'days_to_maturity'
    target_yield = 'yield_kg_per_m2'

    X = df[features]
    y_mat = df[target_maturity]
    y_yld = df[target_yield]

    categorical_features = ['crop_type', 'variety']
    numeric_features = [f for f in features if f not in categorical_features]

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ])

    print("Training Maturity Model...")
    pipeline_mat = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('model', XGBRegressor(n_estimators=100, random_state=42))
    ])

    X_train, X_test, y_train, y_test = train_test_split(X, y_mat, test_size=0.2, random_state=42)
    pipeline_mat.fit(X_train, y_train)
    y_pred = pipeline_mat.predict(X_test)
    print(f"Maturity Model R2: {r2_score(y_test, y_pred):.3f}")

    print("Training Yield Model...")
    pipeline_yld = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('model', XGBRegressor(n_estimators=100, random_state=42))
    ])

    X_train, X_test, y_train, y_test = train_test_split(X, y_yld, test_size=0.2, random_state=42)
    pipeline_yld.fit(X_train, y_train)
    y_pred = pipeline_yld.predict(X_test)
    print(f"Yield Model R2: {r2_score(y_test, y_pred):.3f}")

    joblib.dump(pipeline_mat, "models/maturity_model.pkl")
    joblib.dump(pipeline_yld, "models/yield_model.pkl")
    print("Models saved successfully in models/ directory.")

if __name__ == "__main__":
    main()
