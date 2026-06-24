import aioboto3
from botocore.exceptions import ClientError
import os
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
                ContentType=file.content_type or "application/octet-stream"
            )
        return file_id
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        raise


def get_file_url(file_id: str) -> str:
    return f"{S3_PUBLIC_URL}/{file_id}"


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