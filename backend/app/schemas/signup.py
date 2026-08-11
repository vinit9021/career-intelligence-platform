from pydantic import (
    BaseModel,
    EmailStr,
    Field,
)


class SignupOtpRequestResponse(BaseModel):
    email: EmailStr

    expires_in: int = Field(ge=1)

    resend_in: int = Field(ge=0)


class SignupOtpVerifyRequest(BaseModel):
    email: EmailStr

    otp: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
    )


class SignupCompleteResponse(BaseModel):
    email: EmailStr
    message: str
