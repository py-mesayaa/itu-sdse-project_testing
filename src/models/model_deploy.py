import datetime
import time

from mlflow.tracking.client import MlflowClient

current_date = datetime.datetime.now().strftime("%Y_%B_%d")
model_name = "lead_model"


def wait_for_deployment(model_name, model_version, stage="Staging"):
    """Wait until the model version is in the specified stage."""
    client = MlflowClient()
    status = False
    while not status:
        model_version_details = dict(client.get_model_version(name=model_name, version=model_version))
        if model_version_details["current_stage"] == stage:
            print(f"Transition completed to {stage}")
            status = True
            break
        else:
            time.sleep(2)
    return status


def main(model_version=None):
    """
    Transition a model version to Staging stage.

    Args:
        model_version: The version number of the model to deploy. If None, uses version 1.

    Returns:
        dict: Dictionary containing deployment status information.
    """
    if model_version is None:
        # Get the latest model version if not specified
        client = MlflowClient()
        model_versions = client.search_model_versions(f"name='{model_name}'")
        if model_versions:
            # Get the latest version (highest version number)
            model_version = max(int(mv.version) for mv in model_versions)
        else:
            raise ValueError(f"No model versions found for model '{model_name}'")

    client = MlflowClient()

    model_version_details = dict(client.get_model_version(name=model_name, version=model_version))
    model_status = True

    if model_version_details["current_stage"] != "Staging":
        client.transition_model_version_stage(
            name=model_name,
            version=model_version,
            stage="Staging",
            archive_existing_versions=True,
        )
        model_status = wait_for_deployment(model_name, model_version, "Staging")
    else:
        print("Model already in staging")

    return {
        "model_name": model_name,
        "model_version": model_version,
        "current_stage": model_version_details["current_stage"],
        "deployment_status": model_status,
    }


if __name__ == "__main__":
    main()
