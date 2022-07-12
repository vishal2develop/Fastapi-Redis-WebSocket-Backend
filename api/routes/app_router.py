from fastapi import APIRouter

from . import example_router
# from .import example_router

router = APIRouter()


@router.get("/")
def service_health():
    # Used in health check of a service.
    return {'data': 'Root'}



router.include_router(router=example_router.router)
