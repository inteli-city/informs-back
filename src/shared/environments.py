from enum import Enum
import os
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.domain.repositories.image_repository_interface import IImageRepository
from src.shared.domain.repositories.template_repository_interface import ITemplateRepository

class STAGE(Enum):
    DOTENV = "DOTENV"
    DEV = "DEV"
    HOMOLOG = "HOMOLOG"
    PROD = "PROD"
    TEST = "TEST"

class Environments:
    """
    Defines the environment variables for the application. You should not instantiate this class directly. Please use Environments.get_envs() method instead.

    Usage:

    """
    stage: STAGE
    region: str
    endpoint_url: str = None
    dynamo_table_name: str
    dynamo_partition_key: str
    dynamo_sort_key: str
    client_id: str
    bucket_name: str

    def _configure_local(self):
        from dotenv import load_dotenv
        load_dotenv()
        os.environ["STAGE"] = os.environ.get("STAGE") or STAGE.DOTENV.value

    def load_envs(self):
        if "STAGE" not in os.environ:
            self._configure_local()

        self.stage = STAGE[os.environ.get("STAGE")]

        if self.stage == STAGE.TEST:
            self.region = "sa-east-1"
            self.endpoint_url = "http://localhost:8000"
            self.dynamo_table_name = "formularios-table"
            self.dynamo_partition_key = "PK"
            self.dynamo_sort_key = "SK"
            self.client_id = "test"
            self.bucket_name = "test"
        else:
            self.region = os.environ.get("AWS_REGION")
            self.endpoint_url = os.environ.get("ENDPOINT_URL")
            self.dynamo_table_name = os.environ.get("DYNAMO_TABLE_NAME")
            self.dynamo_partition_key = os.environ.get("DYNAMO_PARTITION_KEY")
            self.dynamo_sort_key = os.environ.get("DYNAMO_SORT_KEY")
            self.user_pool_id = os.environ.get("USER_POOL_ID")
            self.client_id = os.environ.get("APP_CLIENT_ID")
            self.bucket_name = os.environ.get("BUCKET_NAME")

    @staticmethod
    def get_form_repo() -> IFormRepository:
        if Environments.get_envs().stage in [STAGE.TEST, STAGE.DOTENV]:
            from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
            return FormRepositoryMock
        elif Environments.get_envs().stage in [STAGE.PROD, STAGE.DEV, STAGE.HOMOLOG]:
            from src.shared.infra.repositories.form_repository_dynamo import FormRepositoryDynamo
            return FormRepositoryDynamo
        else:
            raise Exception("No repository found for this stage")

    @staticmethod
    def get_image_repo() -> IImageRepository:
        if Environments.get_envs().stage in [STAGE.TEST, STAGE.DOTENV]:
            from src.shared.infra.repositories.image_repository_mock import ImageRepositoryMock
            return ImageRepositoryMock
        elif Environments.get_envs().stage in [STAGE.PROD, STAGE.DEV, STAGE.HOMOLOG]:
            from src.shared.infra.repositories.image_repository_s3 import ImageRepositoryS3
            return ImageRepositoryS3
        else:
            raise Exception("No repository found for this stage")

    @staticmethod
    def get_template_repo() -> ITemplateRepository:
        if Environments.get_envs().stage in [STAGE.TEST, STAGE.DOTENV]:
            from src.shared.infra.repositories.template_repository_mock import TemplateRepositoryMock
            return TemplateRepositoryMock
        else:
            raise Exception("No template repository configured for this stage")

    @staticmethod
    def get_envs() -> "Environments":
        envs = Environments()
        envs.load_envs()
        return envs

    def __repr__(self):
        return self.__dict__
