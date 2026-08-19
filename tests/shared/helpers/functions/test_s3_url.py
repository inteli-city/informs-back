import os

from src.shared.helpers.functions.s3_url import build_s3_url, extract_file_path

os.environ["STAGE"] = "TEST"

FILE_PATH = "2026/system/form-id/sections/2/1/abcdef.jpeg"


class TestExtractFilePath:

    def test_reverte_a_url_construida_por_build_s3_url(self):
        assert extract_file_path(build_s3_url(FILE_PATH)) == FILE_PATH

    def test_ignora_query_string_da_presigned(self):
        url = f"{build_s3_url(FILE_PATH)}?X-Amz-Signature=abc&X-Amz-Expires=3600"

        assert extract_file_path(url) == FILE_PATH

    def test_recusa_url_de_outro_host(self):
        assert extract_file_path("https://atacante.example.com/qualquer.jpeg") is None

    def test_recusa_url_sem_key(self):
        assert extract_file_path(build_s3_url("")) is None

    def test_recusa_valores_nao_string(self):
        assert extract_file_path(None) is None
        assert extract_file_path("") is None
