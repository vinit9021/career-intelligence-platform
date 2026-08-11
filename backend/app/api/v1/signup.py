from functools import (
    lru_cache,
)
from typing import (
    Annotated,
)

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import (
    select,
)

from app.api.dependencies.auth import (
    AuthServiceDependency,
    DbSession,
    SettingsDependency,
)
from app.core.email_config import (
    get_smtp_settings,
)
from app.models import User
from app.schemas.auth import (
    RegisterRequest,
)
from app.schemas.signup import (
    SignupCompleteResponse,
    SignupOtpRequestResponse,
    SignupOtpVerifyRequest,
)
from app.services.auth import (
    EmailAlreadyRegisteredError,
)
from app.services.signup_email import (
    EmailDeliveryError,
    SignupEmailService,
)
from app.services.signup_otp import (
    SignupOtpExpiredError,
    SignupOtpInvalidError,
    SignupOtpRateLimitedError,
    SignupOtpService,
)

router = APIRouter(
    prefix="/auth/signup",
    tags=["authentication"],
)


@lru_cache
def get_signup_otp_service() -> SignupOtpService:
    return SignupOtpService()


@lru_cache
def get_signup_email_service() -> SignupEmailService:
    return SignupEmailService(get_smtp_settings())


SignupOtpDependency = Annotated[
    SignupOtpService,
    Depends(get_signup_otp_service),
]


SignupEmailDependency = Annotated[
    SignupEmailService,
    Depends(get_signup_email_service),
]


def _otp_secret(
    settings: SettingsDependency,
) -> str:
    return settings.jwt_access_secret.get_secret_value()


@router.post(
    "/request-otp",
    response_model=(SignupOtpRequestResponse),
)
async def request_signup_otp(
    payload: RegisterRequest,
    session: DbSession,
    settings: SettingsDependency,
    otp_service: SignupOtpDependency,
    email_service: (SignupEmailDependency),
) -> SignupOtpRequestResponse:
    email = str(payload.email).lower()

    existing_user_id = await session.scalar(select(User.id).where(User.email == email))

    if existing_user_id is not None:
        raise HTTPException(
            status_code=(status.HTTP_409_CONFLICT),
            detail=("An account with this email address already exists."),
        )

    try:
        result = await otp_service.issue(
            payload,
            secret=_otp_secret(settings),
        )

    except SignupOtpRateLimitedError as exc:
        raise HTTPException(
            status_code=(status.HTTP_429_TOO_MANY_REQUESTS),
            detail=("Please wait before requesting another verification code."),
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc

    try:
        await email_service.send_signup_otp(
            recipient=email,
            otp=result.code,
            expires_in=(result.expires_in),
        )

    except EmailDeliveryError as exc:
        await otp_service.clear(email)

        raise HTTPException(
            status_code=(status.HTTP_502_BAD_GATEWAY),
            detail=("We could not send the verification email. Please try again."),
        ) from exc

    return SignupOtpRequestResponse(
        email=result.email,
        expires_in=(result.expires_in),
        resend_in=(result.resend_in),
    )


@router.post(
    "/verify-otp",
    response_model=SignupCompleteResponse,
    status_code=(status.HTTP_201_CREATED),
)
async def verify_signup_otp(
    payload: (SignupOtpVerifyRequest),
    service: (AuthServiceDependency),
    settings: (SettingsDependency),
    otp_service: (SignupOtpDependency),
) -> SignupCompleteResponse:
    try:
        registration = await otp_service.verify(
            str(payload.email),
            payload.otp,
            secret=(_otp_secret(settings)),
        )

    except SignupOtpExpiredError as exc:
        raise HTTPException(
            status_code=(status.HTTP_410_GONE),
            detail=("The verification code has expired. Request a new code."),
        ) from exc

    except SignupOtpInvalidError as exc:
        raise HTTPException(
            status_code=(status.HTTP_400_BAD_REQUEST),
            detail=(f"Invalid verification code. {exc.attempts_remaining} attempts remaining."),
        ) from exc

    try:
        result = await service.register(
            registration,
            is_verified=True,
        )

    except EmailAlreadyRegisteredError as exc:
        await otp_service.clear(str(payload.email))

        raise HTTPException(
            status_code=(status.HTTP_409_CONFLICT),
            detail=("An account with this email address already exists."),
        ) from exc

    return SignupCompleteResponse(
        email=result.user.email,
        message="Account created successfully. Please sign in.",
    )
