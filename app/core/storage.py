import shutil
from pathlib import Path
from fastapi import UploadFile

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def save_upload_file(upload_file: UploadFile, folder: str = "equipment") -> str:
    dest_folder = UPLOAD_DIR / folder
    dest_folder.mkdir(exist_ok=True)
    
    file_path = dest_folder / upload_file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
        
    return str(file_path)
