import os
import sys

sys.path.append(os.getcwd())

import pytest

from src.shared.helpers.errors.usecase_errors import ErrorWithImage
from src.shared.infra.repositories.image_repository_s3 import ImageRepositoryS3


class FakeS3Client:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail
        self.calls = []

    def put_object(self, **kwargs):
        if self.should_fail:
            raise RuntimeError("boom")
        self.calls.append(kwargs)
        return {"ok": True}

    def generate_presigned_url(self, **kwargs):
        if self.should_fail:
            raise RuntimeError("boom")
        self.calls.append(kwargs)
        return "https://presigned.example/test"


def test_image_repository_s3_generate_presigned_url(monkeypatch):
    os.environ["STAGE"] = "TEST"
    client = FakeS3Client()
    monkeypatch.setattr("boto3.client", lambda *args, **kwargs: client)

    repo = ImageRepositoryS3()
    url = repo.generate_presigned_url(image_path="path/file.jpg", mimetype="image/jpeg", expires_in=1200)

    assert url == "https://presigned.example/test"
    assert client.calls
    call = client.calls[0]
    assert call["ClientMethod"] == "put_object"
    assert call["Params"]["Key"] == "path/file.jpg"
    assert call["Params"]["ContentType"] == "image/jpeg"
    assert call["ExpiresIn"] == 1200
    assert call["HttpMethod"] == "PUT"


def test_image_repository_s3_generate_presigned_url_error(monkeypatch):
    os.environ["STAGE"] = "TEST"
    client = FakeS3Client(should_fail=True)
    monkeypatch.setattr("boto3.client", lambda *args, **kwargs: client)

    repo = ImageRepositoryS3()

    with pytest.raises(ErrorWithImage):
        repo.generate_presigned_url(image_path="path/file.jpg", mimetype="image/jpeg", expires_in=1200)
