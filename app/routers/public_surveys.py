from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.survey import SurveyOut, SurveyListItem
from app.models.survey import SurveyStatus
from app.services import survey as svc

router = APIRouter(prefix="/surveys", tags=["Surveys"])


@router.get("", response_model=list[SurveyListItem])
async def list_published_surveys(db: AsyncSession = Depends(get_db)):
    return await svc.list_surveys(db, SurveyStatus.published)


@router.get("/{slug}", response_model=SurveyOut)
async def get_survey_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    return await svc.get_survey_by_slug(db, slug)
