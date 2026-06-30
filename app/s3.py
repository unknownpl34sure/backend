import aioboto3
from botocore.exceptions import ClientError
import os
import json
from dotenv import load_dotenv
from fastapi import UploadFile
import uuid


load_dotenv()

S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_PUBLIC_URL = os.getenv("S3_PUBLIC_URL")

session = aioboto3.Session()

async def create_bucket_if_not_exists():
    async with session.client(
            "s3",
            endpoint_url=S3_ENDPOINT_URL,
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY,
            region_name="us-east-1"
    ) as s3_client:
        try:
            await s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
            print(f"Бакет {S3_BUCKET_NAME} уже существует")
        except ClientError:
            try:
                await s3_client.create_bucket(Bucket=S3_BUCKET_NAME)
                print(f"Бакет {S3_BUCKET_NAME} создан")
            except Exception as e:
                print(f"Ошибка создания бакета: {e}")

        await _set_public_read_policy(s3_client)


async def _set_public_read_policy(s3_client):
    """Открывает анонимный доступ на чтение объектов бакета.

    Без этой политики MinIO отдаёт AccessDenied при обращении к файлам
    по прямой публичной ссылке (S3_PUBLIC_URL).
    """
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ["*"]},
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{S3_BUCKET_NAME}/*"],
            }
        ],
    }
    try:
        await s3_client.put_bucket_policy(
            Bucket=S3_BUCKET_NAME,
            Policy=json.dumps(policy),
        )
        print(f"Политика публичного чтения применена к бакету {S3_BUCKET_NAME}")
    except Exception as e:
        print(f"Ошибка установки политики бакета: {e}")


async def upload_file_to_s3(file: UploadFile, folder: str = "avatars") -> str:
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    file_id = f"{folder}/{uuid.uuid4()}.{ext}"

    try:
        content = await file.read()
        async with session.client(
                "s3",
                endpoint_url=S3_ENDPOINT_URL,
                aws_access_key_id=S3_ACCESS_KEY,
                aws_secret_access_key=S3_SECRET_KEY,
                region_name="us-east-1"
        ) as s3_client:
            await s3_client.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=file_id,
                Body=content,
                ContentType=file.content_type or "application/octet-stream",
            )
        return file_id
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        raise


def get_file_url(file_id: str) -> str | None:
    if not file_id:
        return None
    if file_id.startswith("http://") or file_id.startswith("https://"):
        return file_id
    # Возвращаем путь к прокси-эндпоинту, а не прямой URL к S3
    return f"/files/{file_id}"


async def delete_file_from_s3(file_id: str):
    try:
        async with session.client(
                "s3",
                endpoint_url=S3_ENDPOINT_URL,
                aws_access_key_id=S3_ACCESS_KEY,
                aws_secret_access_key=S3_SECRET_KEY,
                region_name="us-east-1"
        ) as s3_client:
            await s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=file_id)
        return True
    except Exception as e:
        print(f"Ошибка удаления: {e}")
        return False