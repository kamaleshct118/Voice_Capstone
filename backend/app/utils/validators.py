from fastapi import UploadFile, HTTPException

ALLOWED_AUDIO_TYPES = {
    "audio/webm", "audio/wav", "audio/mpeg",
    "audio/ogg", "audio/mp4", "audio/x-wav",
}
ALLOWED_IMAGE_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/gif",
}
MAX_FILE_SIZE_MB = 10
MAX_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def validate_audio_file(file: UploadFile) -> None:
    ct = (file.content_type or "").split(";")[0].strip()
    if ct not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio type: {ct}. Allowed: {ALLOWED_AUDIO_TYPES}",
        )


def validate_image_file(file: UploadFile) -> None:
    ct = (file.content_type or "").split(";")[0].strip()
    if ct not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type: {ct}. Allowed: {ALLOWED_IMAGE_TYPES}",
        )


async def read_and_validate_audio(file: UploadFile) -> bytes:
    validate_audio_file(file)
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max {MAX_FILE_SIZE_MB}MB.",
        )
    return data


async def read_and_validate_image(file: UploadFile) -> bytes:
    validate_image_file(file)
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Image too large. Max {MAX_FILE_SIZE_MB}MB.",
        )
    return data
