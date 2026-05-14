from enum import Enum
from typing import Optional
import os
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.domain.repositories.origin_repository_interface import IOriginRepository
from src.shared.domain.repositories.file_repository_interface import IFileRepository
from src.shared.domain.repositories.profile_repository_interface import IProfileRepository
from src.shared.domain.repositories.template_repository_interface import ITemplateRepository
from src.shared.domain.repositories.sync_state_repository_interface import ISyncStateRepository
from src.shared.domain.repositories.sync_error_form_repository_interface import ISyncErrorFormRepository

class Stage(Enum):
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
    NO_REPOSITORY_FOUND_ERROR = "No repository found for this stage"
    
    stage: Stage
    region: str
    endpoint_url: Optional[str]
    dynamo_table_name: str
    dynamo_partition_key: str
    dynamo_sort_key: str
    dynamo_profile_table_name: str
    dynamo_profile_partition_key: str
    dynamo_profile_sort_key: str
    client_id: str
    bucket_name: str
    sqs_endpoint_url: Optional[str]
    s3_endpoint_url: Optional[str]
    sync_forms_page_limit: int
    sync_forms_window_minutes: int
    sync_forms_first_run_full_sync: bool

    @staticmethod
    def _parse_bool(value) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        return str(value).strip().lower() in {"1", "true", "t", "yes", "y", "on"}


    def _configure_local(self):
        from dotenv import load_dotenv
        load_dotenv()
        os.environ["STAGE"] = os.environ.get("STAGE") or Stage.DOTENV.value

    def load_envs(self):
        if "STAGE" not in os.environ:
            self._configure_local()

        self.stage = Stage[os.environ.get("STAGE")]

        if self.stage == Stage.TEST:
            self.region = "sa-east-1"
            self.endpoint_url = "http://localhost:8000"
            self.dynamo_table_name = "formularios-table"
            self.dynamo_partition_key = "PK"
            self.dynamo_sort_key = "SK"
            self.dynamo_profile_table_name = "formularios-profile-test"
            self.dynamo_profile_partition_key = "PK"
            self.dynamo_profile_sort_key = "SK"
            self.client_id = "test"
            self.bucket_name = "test"
            self.sqs_endpoint_url = "http://localhost:4566"
            self.s3_endpoint_url = None
            self.sync_forms_page_limit = 100
            self.sync_forms_window_minutes = 10
            self.sync_forms_first_run_full_sync = False
        else:
            self.region = os.environ.get("REGION")
            self.endpoint_url = os.environ.get("ENDPOINT_URL")
            self.dynamo_table_name = os.environ.get("DYNAMO_TABLE_NAME")
            self.dynamo_partition_key = os.environ.get("DYNAMO_PARTITION_KEY")
            self.dynamo_sort_key = os.environ.get("DYNAMO_SORT_KEY")
            self.dynamo_profile_table_name = os.environ.get("DYNAMO_PROFILE_TABLE_NAME")
            self.dynamo_profile_partition_key = os.environ.get("DYNAMO_PROFILE_PARTITION_KEY", "PK")
            self.dynamo_profile_sort_key = os.environ.get("DYNAMO_PROFILE_SORT_KEY", "SK")
            self.user_pool_id = os.environ.get("USER_POOL_ID")
            self.client_id = os.environ.get("APP_CLIENT_ID")
            self.bucket_name = os.environ.get("BUCKET_NAME")
            self.sqs_endpoint_url = os.environ.get("AWS_SQS_ENDPOINT_URL")
            self.s3_endpoint_url = os.environ.get("S3_ENDPOINT_URL")
            self.sync_forms_page_limit = int(os.environ.get("SYNC_FORMS_PAGE_LIMIT", "100"))
            self.sync_forms_window_minutes = int(os.environ.get("SYNC_FORMS_WINDOW_MINUTES", "10"))
            self.sync_forms_first_run_full_sync = self._parse_bool(os.environ.get("SYNC_FORMS_FIRST_RUN_FULL_SYNC"))

    @staticmethod
    def get_form_repo() -> IFormRepository:
        if Environments.get_envs().stage in [Stage.TEST, Stage.DOTENV]:
            from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
            return FormRepositoryMock()
        elif Environments.get_envs().stage in [Stage.PROD, Stage.DEV, Stage.HOMOLOG]:
            from src.shared.infra.repositories.form_repository_dynamo import FormRepositoryDynamo
            return FormRepositoryDynamo()
        else:
            raise ValueError(Environments.NO_REPOSITORY_FOUND_ERROR)
    
    @staticmethod
    def get_file_repo() -> IFileRepository:
        if Environments.get_envs().stage in [Stage.TEST, Stage.DOTENV]:
            from src.shared.infra.repositories.file_repository_mock import FileRepositoryMock
            return FileRepositoryMock()
        elif Environments.get_envs().stage in [Stage.PROD, Stage.DEV, Stage.HOMOLOG]:
            from src.shared.infra.repositories.file_repository_s3 import FileRepositoryS3
            return FileRepositoryS3()
        else:
            raise ValueError(Environments.NO_REPOSITORY_FOUND_ERROR)

    @staticmethod
    def get_profile_repo() -> IProfileRepository:
        if Environments.get_envs().stage in [Stage.TEST, Stage.DOTENV]:
            from src.shared.infra.repositories.profile_repository_mock import ProfileRepositoryMock
            return ProfileRepositoryMock()
        elif Environments.get_envs().stage in [Stage.PROD, Stage.DEV, Stage.HOMOLOG]:
            from src.shared.infra.repositories.profile_repository_dynamo import ProfileRepositoryDynamo
            return ProfileRepositoryDynamo()
        else:
            raise ValueError(Environments.NO_REPOSITORY_FOUND_ERROR)

    @staticmethod
    def get_template_repo() -> ITemplateRepository:
        if Environments.get_envs().stage in [Stage.TEST, Stage.DOTENV]:
            from src.shared.infra.repositories.template_repository_mock import TemplateRepositoryMock
            return TemplateRepositoryMock()
        elif Environments.get_envs().stage in [Stage.PROD, Stage.DEV, Stage.HOMOLOG]:
            from src.shared.infra.repositories.template_repository_dynamo import TemplateRepositoryDynamo
            return TemplateRepositoryDynamo()
        else:
            raise ValueError(Environments.NO_REPOSITORY_FOUND_ERROR)

    @staticmethod
    def get_origin_repo() -> IOriginRepository:
        if Environments.get_envs().stage in [Stage.TEST, Stage.DOTENV]:
            from src.shared.infra.repositories.origin_repository_mock import OriginRepositoryMock
            return OriginRepositoryMock()
        elif Environments.get_envs().stage in [Stage.PROD, Stage.DEV, Stage.HOMOLOG]:
            from src.shared.infra.repositories.origin_repository_apex import OriginRepositoryApex
            return OriginRepositoryApex()
        else:
            raise ValueError(Environments.NO_REPOSITORY_FOUND_ERROR)

    @staticmethod
    def get_sync_state_repo() -> ISyncStateRepository:
        if Environments.get_envs().stage in [Stage.TEST, Stage.DOTENV]:
            from src.shared.infra.repositories.sync_state_repository_mock import SyncStateRepositoryMock
            return SyncStateRepositoryMock()
        elif Environments.get_envs().stage in [Stage.PROD, Stage.DEV, Stage.HOMOLOG]:
            from src.shared.infra.repositories.sync_state_repository_dynamo import SyncStateRepositoryDynamo
            return SyncStateRepositoryDynamo()
        else:
            raise ValueError(Environments.NO_REPOSITORY_FOUND_ERROR)

    @staticmethod
    def get_sync_error_form_repo() -> ISyncErrorFormRepository:
        if Environments.get_envs().stage in [Stage.TEST, Stage.DOTENV]:
            from src.shared.infra.repositories.sync_error_form_repository_mock import SyncErrorFormRepositoryMock
            return SyncErrorFormRepositoryMock()
        elif Environments.get_envs().stage in [Stage.PROD, Stage.DEV, Stage.HOMOLOG]:
            from src.shared.infra.repositories.sync_error_form_repository_dynamo import SyncErrorFormRepositoryDynamo
            return SyncErrorFormRepositoryDynamo()
        else:
            raise ValueError(Environments.NO_REPOSITORY_FOUND_ERROR)

    _instance: Optional["Environments"] = None

    @staticmethod
    def get_envs() -> "Environments":
        current_stage = os.environ.get("STAGE")
        should_reload = (
            Environments._instance is None
            or (
                current_stage is not None
                and Environments._instance.stage.name != current_stage
            )
        )
        if should_reload:
            envs = Environments()
            envs.load_envs()
            Environments._instance = envs
        return Environments._instance

    @staticmethod
    def _reset_instance():
        """Reset cached instance. For use in tests only."""
        Environments._instance = None

    def __repr__(self):
        return self.__dict__
