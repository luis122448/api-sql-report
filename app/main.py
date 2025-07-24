from fastapi import FastAPI
from routers import extract_router, metadata_router, analytics_router, auth_router, usage_router
from fastapi.middleware.cors import CORSMiddleware
from middlewares.error_handler import ExceptionHandlerMiddleware, http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException
from scheduling.scheduler import start_scheduler, stop_scheduler

app = FastAPI()


app.title = "App ETL And Analytics API for Oracle"
app.version = "1.0.0"
app.description = "ETL And Analytics API"
app.docs_url = "/docs"

origins = ["*"] 

# Add middleware
# app.add_middleware(ExceptionHandlerMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Exception Handler
# app.add_exception_handler(StarletteHTTPException, http_exception_handler)

app.include_router(extract_router.router, prefix="/api")
app.include_router(metadata_router.router, prefix="/api")
app.include_router(analytics_router.router, prefix="/api")
app.include_router(auth_router.router, prefix="/auth")
app.include_router(usage_router.router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    start_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    stop_scheduler()