from importlib import import_module

from src.shared.domain.repositories.file_repository_interface import IFileRepository
from src.shared.environments import Environments
from src.shared.helpers.errors.usecase_errors import ErrorWithFile
from src.shared.helpers.functions.exception_message import get_exception_message


def _build_s3_config():
    config_module = import_module("botocore.config")
    return config_module.Config(s3={"addressing_style": "path"})


def _create_s3_client(region_name: str, endpoint_url: str = None, config=None):
    boto3 = import_module("boto3")
    return boto3.client(
        "s3",
        region_name=region_name,
        endpoint_url=endpoint_url,
        config=config,
    )


class FileRepositoryS3(IFileRepository):
    def __init__(self):
        envs = Environments.get_envs()
        config = _build_s3_config() if envs.s3_endpoint_url else None
        self.client = _create_s3_client(
            region_name=envs.region,
            endpoint_url=envs.s3_endpoint_url,
            config=config,
        )

    def generate_presigned_url(self, file_path: str, mimetype: str, expires_in: int = 3600) -> str:
        try:
            return self.client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": Environments.get_envs().bucket_name,
                    "Key": file_path,
                    "ContentType": mimetype,
                },
                ExpiresIn=expires_in,
                HttpMethod="PUT",
            )
        except Exception as err:
            raise ErrorWithFile(get_exception_message(err))
