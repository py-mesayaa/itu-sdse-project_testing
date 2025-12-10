import os
from typing import Optional, Union

import joblib
import pandas as pd

MODEL_PATH = "./artifacts/lead_model_lr.pkl"
X_TEST_PATH = "./artifacts/X_test.csv"
Y_TEST_PATH = "./artifacts/y_test.csv"


def load_model(model_path: str = MODEL_PATH):
    """
    Load a trained model from disk.

    Args:
        model_path: Path to the saved model file.

    Returns:
        The loaded model object.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    with open(model_path, "rb") as f:
        model = joblib.load(f)
    return model


def load_test_data(X_path: str = X_TEST_PATH, y_path: Optional[str] = Y_TEST_PATH):
    """
    Load test data for inference.

    Args:
        X_path: Path to the test features CSV file.
        y_path: Optional path to the test labels CSV file.

    Returns:
        Tuple of (X, y) if y_path is provided, otherwise just X.
    """
    X = pd.read_csv(X_path)
    
    if y_path is not None and os.path.exists(y_path):
        y = pd.read_csv(y_path)
        return X, y
    return X


def predict(model, X: pd.DataFrame, return_proba: bool = False) -> Union[pd.Series, pd.DataFrame]:
    """
    Make predictions using the trained model.

    Args:
        model: The trained model object.
        X: Features dataframe.
        return_proba: If True, return probability predictions instead of class predictions.

    Returns:
        Predictions as a pandas Series or DataFrame.
    """
    if return_proba:
        return pd.DataFrame(model.predict_proba(X), columns=model.classes_)
    return pd.Series(model.predict(X), name="predictions")


def main():
    """
    Main function to load model and test data, then make predictions.
    """
    print("Loading model...")
    model = load_model()
    
    print("Loading test data...")
    try:
        X, y = load_test_data()
        print(f"Test data shape: {X.shape}")
        
        print("Making predictions...")
        predictions = predict(model, X.head(5))
        
        print("\nPredictions:")
        print(predictions)
        print("\nActual values:")
        print(y.head(5))
        
    except FileNotFoundError:
        # If y_test.csv doesn't exist, just make predictions on X
        X = load_test_data(y_path=None)
        print(f"Test data shape: {X.shape}")
        
        print("Making predictions...")
        predictions = predict(model, X.head(5))
        
        print("\nPredictions:")
        print(predictions)


if __name__ == "__main__":
    main()

