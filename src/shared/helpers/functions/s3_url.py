from src.shared.environments import Environments

def build_s3_url(file_path: str) -> str:
    envs = Environments.get_envs()
    if envs.s3_endpoint_url:
        base = envs.s3_endpoint_url.rstrip("/")
        return f"{base}/{envs.bucket_name}/{file_path}"
    return f"https://{envs.bucket_name}.s3.sa-east-1.amazonaws.com/{file_path}"
