import base64
import io
from uuid import UUID, uuid4

import boto3
from PIL import Image

HD_WIDTH = 1280
HD_HEIGHT = 720
BUCKET_NAME = "mldc-pictures"
SPACES_REGION = "fra1"
SPACES_ENDPOINT = f"https://{SPACES_REGION}.digitaloceanspaces.com"


def _get_s3_client() -> boto3.client:
    # DigitalOcean Spaces offers an S3-compatible API; boto3 handles authentication via AWS env vars
    return boto3.client(
        "s3",
        region_name=SPACES_REGION,
        endpoint_url=SPACES_ENDPOINT,
    )


def _bucket_base_url(bucket_name: str) -> str:
    return f"https://{bucket_name}.{SPACES_REGION}.digitaloceanspaces.com"


def delete_blob_from_url(blob_url: str, bucket_name: str = BUCKET_NAME) -> None:
    base_url = f"{_bucket_base_url(bucket_name)}/"
    if not blob_url.startswith(base_url):
        raise ValueError("Invalid blob URL")

    blob_name = blob_url[len(base_url) :]

    s3_client = _get_s3_client()
    s3_client.delete_object(Bucket=bucket_name, Key=blob_name)


def upload_blob(
    content: bytes,
    destination_blob_name: UUID | str | None = None,
    old_blob_id: str | None = None,
    bucket_name: str = BUCKET_NAME,
) -> str:
    object_key = str(destination_blob_name or uuid4())

    s3_client = _get_s3_client()
    s3_client.put_object(
        Bucket=bucket_name,
        Key=object_key,
        Body=content,
        ContentType="image/jpeg",
        ACL="public-read",
    )

    if old_blob_id:
        s3_client.delete_object(Bucket=bucket_name, Key=str(old_blob_id))

    return f"{_bucket_base_url(bucket_name)}/{object_key}"


def download_blob_into_memory(
    blob_name: UUID | str, bucket_name: str = BUCKET_NAME
) -> bytes:
    s3_client = _get_s3_client()
    response = s3_client.get_object(Bucket=bucket_name, Key=str(blob_name))

    return response["Body"].read()


def scale_to_hd(image: io.IOBase) -> io.BytesIO:
    input_image = Image.open(io.BytesIO(image.read()))

    if input_image.mode == "RGBA":
        background = Image.new("RGB", input_image.size, (255, 255, 255))
        background.paste(input_image, mask=input_image.split()[3])
        input_image = background.convert("RGB")

    width, height = input_image.size

    if width > HD_WIDTH or height > HD_HEIGHT:
        aspect_ratio = width / height

        if aspect_ratio > 1:
            new_width = HD_WIDTH
            new_height = int(new_width / aspect_ratio)
        else:
            new_height = HD_HEIGHT
            new_width = int(new_height * aspect_ratio)

        input_image = input_image.resize((new_width, new_height))

    output_image = io.BytesIO()
    input_image.save(output_image, format="JPEG")
    output_image.seek(0)

    return output_image


def load_picture(picture_uuid):
    if not picture_uuid:
        return False

    picture = download_blob_into_memory(picture_uuid)
    picture_base64 = base64.b64encode(picture).decode("utf-8")

    return picture_base64


def upload_picture(picture):
    if not picture or picture == "" or picture == "None":
        raise ValueError("No picture provided")

    resized_picture = scale_to_hd(picture)
    picture_url = upload_blob(resized_picture.read())
    return picture_url
