import os
import shutil
from pathlib import Path
import subprocess
import sys

IAC_DIRECTORY_NAME = "iac"
SOURCE_DIRECTORY_NAME = "src"
LAMBDA_LAYER_PREFIX = os.path.join("python", "src")
LAMBDA_LAYER_REQUIREMENTS_FILE = "lambda_layer_requirements.txt"


def adjust_layer_directory(shared_dir_name: str, destination: str):
    # Get the root directory of the source directory
    root_directory = Path(__file__).parent.parent
    iac_directory = os.path.join(root_directory, IAC_DIRECTORY_NAME)

    print(f"Root directory: {root_directory}")
    print(f"Root direcotry files: {os.listdir(root_directory)}")
    print(f"IaC directory: {iac_directory}")
    print(f"IaC directory files: {os.listdir(iac_directory)}")


    # Get the destination and source directory
    destination_directory = os.path.join(root_directory, IAC_DIRECTORY_NAME, destination)
    source_directory = os.path.join(root_directory, SOURCE_DIRECTORY_NAME, shared_dir_name)

    # Delete the destination directory if it exists
    if os.path.exists(destination_directory):
        shutil.rmtree(destination_directory)

    # Copy the shared source code to the layer
    shutil.copytree(source_directory, os.path.join(destination_directory, LAMBDA_LAYER_PREFIX, shared_dir_name))
    print(
        f"Copying files from {source_directory} to {os.path.join(destination_directory, LAMBDA_LAYER_PREFIX, shared_dir_name)}")

    # Install runtime dependencies used by Lambdas into the layer root (/opt/python)
    layer_python_directory = os.path.join(destination_directory, "python")
    requirements_path = os.path.join(iac_directory, LAMBDA_LAYER_REQUIREMENTS_FILE)
    if os.path.exists(requirements_path):
        print(f"Installing layer dependencies from {requirements_path} to {layer_python_directory}")
        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            requirements_path,
            "-t",
            layer_python_directory,
            "--no-deps",
            "--upgrade",
        ])
    else:
        print(f"Requirements file not found for layer dependencies: {requirements_path}")


if __name__ == '__main__':
    adjust_layer_directory(shared_dir_name="shared", destination="lambda_layer_out_temp")
