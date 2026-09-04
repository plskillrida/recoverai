from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from dotenv import load_dotenv

load_dotenv()

from .database import initialize_database
from .routes import router
from .webhooks import router as webhook_router
from .dashboard import router as dashboard_router
from .recoveries import router as recoveries_router
from .recovery_verification import (
    router as recovery_verification_router
)
from .auth import (
    router as auth_router,
    initialize_admin_user,
)


app = FastAPI(
    title="RecoverAI",
    description="AI-powered revenue recovery agent",
    version="0.2.0",
)


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

initialize_database()
initialize_admin_user()


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# AUTHENTICATION MIDDLEWARE
# --------------------------------------------------

PUBLIC_PATHS = {
    "/",
    "/health",
    "/auth/login",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/webhooks/razorpay",
}


@app.middleware("http")
async def authentication_middleware(
    request: Request,
    call_next,
):

    path = request.url.path

    # Allow CORS preflight
    if request.method == "OPTIONS":

        return await call_next(request)

    # Public endpoints
    if path in PUBLIC_PATHS:

        return await call_next(request)

    # Swagger internal assets / OpenAPI
    if path.startswith("/docs"):

        return await call_next(request)

    # Import here to avoid circular imports
    from .auth import get_current_user

    try:

        get_current_user(request)

    except Exception as error:

        if hasattr(error, "status_code"):

            return JSONResponse(
                status_code=error.status_code,
                content={
                    "detail": error.detail
                },
            )

        return JSONResponse(
            status_code=401,
            content={
                "detail": "Authentication required"
            },
        )

    return await call_next(request)


# --------------------------------------------------
# ROUTERS
# --------------------------------------------------

app.include_router(auth_router)

app.include_router(router)

app.include_router(webhook_router)

app.include_router(dashboard_router)

app.include_router(recoveries_router)

app.include_router(
    recovery_verification_router
)


# --------------------------------------------------
# ROOT
# --------------------------------------------------

@app.get("/")
def root():

    return {
        "name": "RecoverAI",
        "status": "running",
        "version": "0.2.0",
    }


# --------------------------------------------------
# HEALTH
# --------------------------------------------------

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }