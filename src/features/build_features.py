# -*- coding: utf-8 -*-
import click
import logging
import pandas as pd
from pathlib import Path
from dotenv import find_dotenv, load_dotenv


def create_dummy_cols(df, col):
    """Create one-hot encoded columns for categorical variables.

    Parameters:
        df (pd.DataFrame): DataFrame containing the column to encode
        col (str): Column name to create dummy variables for

    Returns:
        pd.DataFrame: DataFrame with dummy variables created and original column dropped
    """
    df_dummies = pd.get_dummies(df[col], prefix=col, drop_first=True)
    new_df = pd.concat([df, df_dummies], axis=1)
    new_df = new_df.drop(col, axis=1)
    return new_df


@click.command()
@click.argument("input_filepath", type=click.Path(exists=True))
@click.argument("output_filepath", type=click.Path())
def main(input_filepath, output_filepath):
    """Build features from processed dataset.

    Takes the processed dataset from make_dataset.py and performs additional
    feature engineering including:
    - Dropping columns not needed for modeling
    - Creating dummy variables for categorical columns
    - Converting all columns to float64 for modeling
    """
    logger = logging.getLogger(__name__)
    logger.info("building features from processed data")

    # Load the processed data from make_dataset.py
    data = pd.read_csv(input_filepath)
    logger.info(f"Loaded data with shape: {data.shape}")

    # Drop columns not needed for modeling (exact match to notebook)
    data = data.drop(["lead_id", "customer_code", "date_part"], axis=1)

    # Separate categorical columns (exact match to notebook)
    cat_cols = ["customer_group", "onboarding", "bin_source", "source"]
    cat_vars = data[cat_cols]
    other_vars = data.drop(cat_cols, axis=1)

    # Create dummy variables for categorical columns (exact match to notebook)
    for col in cat_vars:
        cat_vars[col] = cat_vars[col].astype("category")
        cat_vars = create_dummy_cols(cat_vars, col)

    # Combine and convert all columns to float64 (exact match to notebook)
    data = pd.concat([other_vars, cat_vars], axis=1)
    for col in data:
        data[col] = data[col].astype("float64")

    logger.info(f"Converted all columns to float64. Final shape: {data.shape}")

    # Ensure output directory exists
    output_path = Path(output_filepath)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save final features
    data.to_csv(output_filepath, index=False)
    logger.info(f"Features saved to {output_filepath}")


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    project_dir = Path(__file__).resolve().parents[2]

    load_dotenv(find_dotenv())

    main()
