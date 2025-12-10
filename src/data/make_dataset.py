# -*- coding: utf-8 -*-
import click
import logging
import os
import json
import datetime
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from dotenv import find_dotenv, load_dotenv
from sklearn.preprocessing import MinMaxScaler


def describe_numeric_col(x):
    return pd.Series(
        [x.count(), x.isnull().count(), x.mean(), x.min(), x.max()], index=["Count", "Missing", "Mean", "Min", "Max"]
    )


def impute_missing_values(x, method="mean"):
    if (x.dtype == "float64") | (x.dtype == "int64"):
        x = x.fillna(x.mean()) if method == "mean" else x.fillna(x.median())
    else:
        x = x.fillna(x.mode()[0])
    return x


def create_artifact_directory():
    os.makedirs("artifacts", exist_ok=True)


def filter_by_date(data, max_date, min_date):
    if not max_date:
        max_date = pd.to_datetime(datetime.datetime.now().date()).date()
    else:
        max_date = pd.to_datetime(max_date).date()

    min_date = pd.to_datetime(min_date).date()

    data["date_part"] = pd.to_datetime(data["date_part"]).dt.date
    data = data[(data["date_part"] >= min_date) & (data["date_part"] <= max_date)]

    min_date = data["date_part"].min()
    max_date = data["date_part"].max()
    date_limits = {"min_date": str(min_date), "max_date": str(max_date)}
    with open("./artifacts/date_limits.json", "w") as f:
        json.dump(date_limits, f)

    return data, min_date, max_date


def select_features(data):
    data = data.drop(["is_active", "marketing_consent", "first_booking", "existing_customer", "last_seen"], axis=1)
    data = data.drop(["domain", "country", "visited_learn_more_before_booking", "visited_faq"], axis=1)
    return data


def clean_data(data):
    data["lead_indicator"].replace("", np.nan, inplace=True)
    data["lead_id"].replace("", np.nan, inplace=True)
    data["customer_code"].replace("", np.nan, inplace=True)

    data = data.dropna(axis=0, subset=["lead_indicator"])
    data = data.dropna(axis=0, subset=["lead_id"])

    data = data[data.source == "signup"]
    return data


def create_categorical_columns(data):
    vars = ["lead_id", "lead_indicator", "customer_group", "onboarding", "source", "customer_code"]

    for col in vars:
        data[col] = data[col].astype("object")
    return data


def separate_categorical_continuous(data):
    cont_vars = data.loc[:, ((data.dtypes == "float64") | (data.dtypes == "int64"))]
    cat_vars = data.loc[:, (data.dtypes == "object")]
    return cont_vars, cat_vars


def handle_outliers(cont_vars):
    cont_vars = cont_vars.apply(lambda x: x.clip(lower=(x.mean() - 2 * x.std()), upper=(x.mean() + 2 * x.std())))
    outlier_summary = cont_vars.apply(describe_numeric_col).T
    outlier_summary.to_csv("./artifacts/outlier_summary.csv")
    return cont_vars


def impute_categorical_missing(cat_vars):
    cat_missing_impute = cat_vars.mode(numeric_only=False, dropna=True)
    cat_missing_impute.to_csv("./artifacts/cat_missing_impute.csv")
    return cat_missing_impute


def impute_continuous_missing(cont_vars):
    cont_vars = cont_vars.apply(impute_missing_values)
    return cont_vars


def impute_categorical_data(cat_vars):
    cat_vars.loc[cat_vars["customer_code"].isna(), "customer_code"] = "None"
    cat_vars = cat_vars.apply(impute_missing_values)
    return cat_vars


def standardize_data(cont_vars):
    scaler_path = "./artifacts/scaler.pkl"

    scaler = MinMaxScaler()
    scaler.fit(cont_vars)

    joblib.dump(value=scaler, filename=scaler_path)

    cont_vars = pd.DataFrame(scaler.transform(cont_vars), columns=cont_vars.columns)
    return cont_vars


def combine_data(cat_vars, cont_vars):
    cont_vars = cont_vars.reset_index(drop=True)
    cat_vars = cat_vars.reset_index(drop=True)
    data = pd.concat([cat_vars, cont_vars], axis=1)
    return data


def save_data_drift_artifact(data):
    data_columns = list(data.columns)
    with open("./artifacts/columns_drift.json", "w+") as f:
        json.dump(data_columns, f)

    data.to_csv("./artifacts/training_data.csv", index=False)


def bin_source_column(data):
    data["bin_source"] = data["source"]
    values_list = ["li", "organic", "signup", "fb"]
    data.loc[~data["source"].isin(values_list), "bin_source"] = "Others"
    mapping = {"li": "socials", "fb": "socials", "organic": "group1", "signup": "group1"}

    data["bin_source"] = data["source"].map(mapping)
    return data


def save_gold_dataset(data):
    data.to_csv("./artifacts/train_data_gold.csv", index=False)


@click.command()
@click.argument("input_filepath", type=click.Path(exists=True))
@click.argument("output_filepath", type=click.Path())
@click.option("--max-date", default="2024-01-31", help="Maximum date for filtering")
@click.option("--min-date", default="2024-01-01", help="Minimum date for filtering")
def main(input_filepath, output_filepath, max_date, min_date):
    logger = logging.getLogger(__name__)
    logger.info("making final data set from raw data")

    create_artifact_directory()

    data = pd.read_csv(input_filepath)

    data, min_date, max_date = filter_by_date(data, max_date, min_date)

    data = select_features(data)

    data = clean_data(data)

    data = create_categorical_columns(data)

    cont_vars, cat_vars = separate_categorical_continuous(data)

    cont_vars = handle_outliers(cont_vars)

    impute_categorical_missing(cat_vars)

    cont_vars = impute_continuous_missing(cont_vars)

    cat_vars = impute_categorical_data(cat_vars)

    cont_vars = standardize_data(cont_vars)

    data = combine_data(cat_vars, cont_vars)

    save_data_drift_artifact(data)

    data = bin_source_column(data)

    save_gold_dataset(data)


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    project_dir = Path(__file__).resolve().parents[2]

    load_dotenv(find_dotenv())

    main()
