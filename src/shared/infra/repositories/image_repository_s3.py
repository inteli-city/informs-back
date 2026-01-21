
from src.shared.domain.repositories.image_repository_interface import IImageRepository
from src.shared.environments import Environments
import boto3
from botocore.config import Config

from src.shared.helpers.errors.usecase_errors import ErrorWithImage


class ImageRepositoryS3(IImageRepository):

    def __init__(self):
        envs = Environments.get_envs()
        config = None
        if envs.s3_endpoint_url:
            config = Config(s3={"addressing_style": "path"})
        self.client = boto3.client(
            's3',
            region_name=envs.region,
            endpoint_url=envs.s3_endpoint_url,
            config=config,
        )
        
    def generate_presigned_url(self, image_path: str, mimetype: str, expires_in: int = 3600) -> str:
        try:
            return self.client.generate_presigned_url(
                ClientMethod='put_object',
                Params={
                    "Bucket": Environments.get_envs().bucket_name,
                    "Key": image_path,
                    "ContentType": mimetype,
                },
                ExpiresIn=expires_in,
                HttpMethod="PUT",
            )
        except Exception as e:
            message = e.args[0] if e.args else str(e)
            raise ErrorWithImage(message)
