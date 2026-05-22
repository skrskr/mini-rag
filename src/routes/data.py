from fastapi import FastAPI, APIRouter, UploadFile, Depends, status
from fastapi.responses import JSONResponse
import os
import aiofiles
from models import ResponseSignal

from controllers import DataController, ProjectController

from helpers.config import get_settings, Settings

import logging

logger = logging.getLogger('uvicorn.error')

data_router=APIRouter(
    prefix="/api/v1",
    tags=["api_v1", "data"],
)

@data_router.get('/upload/{project_id}')
async def upload_data(project_id:str, file: UploadFile, app_settings: Settings = Depends(get_settings)):
    
    data_controller = DataController()
    is_valid, result_signal = data_controller.validate_upload_file(file)
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": result_signal
            }
        )
    
    project_dir_path = ProjectController().get_project_path(project_id)

    file_path, file_id = data_controller.generate_unique_filepath(file.filename, project_id)

    try: 
        async with aiofiles.open(file_path, mode='wb') as f:
            while chuck := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chuck)
    except Exception as e:
        
        logger.error(f"Error while uploading file: {e}")

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.FILE_UPLOAD_FAILED.value
            }
        )
    

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": result_signal
        }
    )