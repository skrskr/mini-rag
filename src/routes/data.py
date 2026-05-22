from fastapi import FastAPI, APIRouter, UploadFile, Depends, status
from fastapi.responses import JSONResponse
import os
import aiofiles
from models import ResponseSignal

from controllers import DataController, ProjectController, ProcessController

from helpers.config import get_settings, Settings

import logging

from .schemes.data import ProcessRequest

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
            "signal": result_signal,
            "file_id": file_id
        }
    )

@data_router.post('/process/{project_id}')
async def process_endpoint(project_id:str, process_request: ProcessRequest):
    
    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    chunk_overlap = process_request.overlap_size

    process_controller = ProcessController(project_id=project_id)
    file_content = process_controller.get_file_content(file_id=file_id)

    file_chunks = process_controller.process_file_content(
        file_id=file_id,
        file_content=file_content,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    if file_chunks is None or len(file_chunks) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.PROCESS_FAILED.value
            }
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseSignal.PROCESS_SUCCESS.value,
            "chunks": [
                {"page_content": chunk.page_content, "metadata": chunk.metadata}
                for chunk in file_chunks
            ]
        }
    )

    