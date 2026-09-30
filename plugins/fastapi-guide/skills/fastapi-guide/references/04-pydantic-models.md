# Pydantic 모델 & 스키마 설계

## 1. 커스텀 베이스 모델

공통 설정을 한 곳에서 관리하라:
```python
from pydantic import BaseModel, ConfigDict, field_serializer
from datetime import datetime

class CustomBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,       # ORM 모델 직접 변환
        validate_assignment=True,   # 할당 시 재검증
        str_strip_whitespace=True,  # 문자열 공백 자동 제거
        populate_by_name=True,
    )

    # Pydantic v2: json_encoders 대신 커스텀 serializer 사용
    @field_serializer('created_at', 'updated_at', check_fields=False)
    @classmethod
    def serialize_datetime(cls, v: datetime) -> str:
        return v.strftime("%Y-%m-%dT%H:%M:%S") if v else None

# 모든 스키마가 상속
class UserCreate(CustomBase):
    name: str
    email: str

class UserResponse(CustomBase):
    id: int
    name: str
    email: str
```

## 2. response_model로 자동 직렬화

```python
# ❌ 수동 딕셔너리 구성 (오류 유발 가능)
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    user = get_user_from_db(user_id)
    return {"id": user.id, "name": user.name, "email": user.email}

# ✅ response_model 활용
@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    return get_user_from_db(user_id)  # Pydantic이 자동 처리 + 민감 필드 필터링
```

## 3. Field와 validator 활용

직접 if문으로 검증하지 말고 Pydantic에 맡겨라:
```python
from pydantic import EmailStr, Field, field_validator, AnyUrl

class UserCreate(CustomBase):
    email: EmailStr                               # 자동 이메일 검증
    password: str = Field(min_length=8, max_length=100)
    age: int = Field(ge=18, le=120)               # 범위 검증
    website: AnyUrl | None = None                 # URL 검증
    role: Literal["admin", "user"] = "user"       # 열거형

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('대문자 포함 필요')
        if not any(c.isdigit() for c in v):
            raise ValueError('숫자 포함 필요')
        return v
```

**`@field_validator` 안에서 `ValueError`를 raise하면 FastAPI가 자동으로 HTTP 422로 변환한다.**

## 4. Input/Output 스키마 분리

요청(Input)과 응답(Output) 스키마를 분리하라:
```python
# 생성 요청 — 비밀번호 포함
class UserCreate(CustomBase):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str

# 응답 — 비밀번호 미포함, DB 필드 포함
class UserResponse(CustomBase):
    id: int
    email: str
    name: str
    created_at: datetime

# 수정 요청 — 모든 필드 선택적
class UserUpdate(CustomBase):
    email: EmailStr | None = None
    name: str | None = None
```

## 5. 직렬화 이중 실행 주의

FastAPI는 응답 시 Pydantic 객체를 **두 번** 인스턴스화한다 (dict 변환 → 검증 → 직렬화). `@field_validator`에 사이드 이펙트가 있으면 두 번 실행된다는 점을 인지하라.
