from fastapi import APIRouter, Depends
import src.dependencies as deps


router = APIRouter(
    prefix="/economy",
    tags=["economy"],
    dependencies=[Depends(deps.verify_session)],
)
