from typing import Optional

from src.shared.environments import Environments

def build_s3_url(file_path: str) -> str:
    envs = Environments.get_envs()
    if envs.s3_endpoint_url:
        base = envs.s3_endpoint_url.rstrip("/")
        return f"{base}/{envs.bucket_name}/{file_path}"
    return f"https://{envs.bucket_name}.s3.sa-east-1.amazonaws.com/{file_path}"


def extract_file_path(file_url: str) -> Optional[str]:
    """
    Inverso de build_s3_url: recupera a key do S3 a partir da URL gravada no
    formulário. Permite re-assinar a URL de um arquivo já registrado sem gerar
    uma key nova (o que criaria órfão no bucket e reescreveria o DynamoDB).

    Devolve None quando a URL não pertence ao bucket configurado — o chamador
    trata isso como arquivo desconhecido, nunca como key válida.
    """
    if not isinstance(file_url, str) or not file_url:
        return None

    envs = Environments.get_envs()
    prefixes = [f"https://{envs.bucket_name}.s3.sa-east-1.amazonaws.com/"]
    if envs.s3_endpoint_url:
        prefixes.append(f'{envs.s3_endpoint_url.rstrip("/")}/{envs.bucket_name}/')

    for prefix in prefixes:
        if file_url.startswith(prefix):
            file_path = file_url[len(prefix):].split("?")[0]
            return file_path or None

    return None
