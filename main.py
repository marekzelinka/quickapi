from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    status,
)
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from pydantic import BaseModel

SECRET_KEY = "4190fc2a5ca3c5813532f5c06a349fff6d3a46290fc55b9809f4ef9b007b5487"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

fake_users_db: dict = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$wagCPXjifgvUFBzq4hqe3w$CYaIb8sB+wtD+Vu/P4uod1+Qof8h+1g7bbDlBID48Rc",
        "disabled": False,
    },
}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str


password_hash = PasswordHash.recommended()

oauth2_schema = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def get_user(db, username: str | None) -> UserInDB | None:
    if username not in db:
        return None

    user_dict = db[username]
    return UserInDB(**user_dict)


def authenticate_user(fake_db: dict, username: str, password: str) -> UserInDB | None:
    user = get_user(fake_db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_schema)]) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.InvalidTokenError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if not user:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


@app.post("/token", response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Beaere"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get("/users/me", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user


@app.get("/users/me/items")
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return [{"item_id": "Foo", "owner": current_user.username}]


# class ModelName(str, Enum):
#     alexnet = "alexnet"
#     resnet = "resnet"
#     lenet = "lenet"


# class OrderBy(str, Enum):
#     created_at = "created_at"
#     updated_at = "updated_at"


# class FilterParams(BaseModel):
#     limit: int = Field(100, gt=0, le=100)
#     offset: int = Field(0, ge=0)
#     order_by: OrderBy = OrderBy.created_at
#     tags: list[str] = []


# class Image(BaseModel):
#     url: HttpUrl
#     name: str


# class Item(BaseModel):
#     name: str
#     description: str | None = Field(
#         None, title="The description of the item", max_length=300
#     )
#     price: float = Field(gt=0, description="The price must be greater than zero")
#     tax: float | None = None
#     tags: set[str] = set()
#     images: list[Image] | None = None

#     model_config = {
#         "json_schema_extra": {
#             "examples": [
#                 {
#                     "name": "Foo",
#                     "description": "A very cool item",
#                     "price": 69.25,
#                     "tax": 3.2,
#                     "tags": ["cool"],
#                 }
#             ]
#         }
#     }


# class Offer(BaseModel):
#     name: str
#     description: str | None = None
#     price: float
#     items: list[Item]


# class BaseUser(BaseModel):
#     username: str
#     email: EmailStr
#     full_name: str | None = None


# class UserIn(BaseUser):
#     password: str
#
# fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]


# class CommonQueryParams:
#     def __init__(self, q: str | None = None, skip: int = 0, limit: int = 100):
#         self.q: str | None = q
#         self.skip: int = skip
#         self.limit: int = limit


# @app.get("/items/")
# async def read_items(commons: Annotated[CommonQueryParams, Depends()]):
#     res = {}
#     if commons.q:
#         res.update({"q": commons.q})
#     items = fake_items_db[commons.skip : commons.skip + commons.limit]
#     res.update({"items": items})
#     return res


# @app.get("/users/")
# async def read_users(commons: Annotated[CommonQueryParams, Depends()]):
#     return commons


# class FormData(BaseModel):
#     username: str
#     password: str


# @app.post("/login/", status_code=status.HTTP_201_CREATED)
# async def login(formData: Annotated[FormData, Form()]):
#     return {"username": formData.username, "password": formData.password}


# @app.post("/signup", status_code=status.HTTP_200_OK)
# async def signup(
#     formData: Annotated[FormData, Form()], avatar: Annotated[UploadFile, File()]
# ):
#     return {
#         "username": formData.username,
#         "password": formData.password,
#         "avatar": avatar.filename,
#     }


# @app.patch("/profile/avatar")
# async def update_avatar_file(
#     file: Annotated[
#         UploadFile | None, File(description="Update profile avatar")
#     ] = None,
# ):
#     if not file:
#         return {"message": "No avatar uploaded"}

#     contents = await file.read()

#     return {"filename": file.filename}


# class UserBase(BaseModel):
#     username: str
#     email: EmailStr
#     full_name: str | None = None


# class UserIn(UserBase):
#     password: str


# class UserOut(UserBase):
#     pass


# class UserInDB(UserBase):
#     hashed_password: str


# async def fake_hash_password(raw_password: str) -> str:
#     await sleep(1)
#     return f"supersecret{raw_password}"


# async def fake_save_user(user_in: UserIn) -> UserInDB:
#     hashed_password = await fake_hash_password(user_in.password)
#     user_in_db = UserInDB(**user_in.model_dump(), hashed_password=hashed_password)
#     print("User saved! Just kidding...")
#     return user_in_db


# @app.post("/user", response_model=UserOut, status_code=status.HTTP_201_CREATED)
# async def create_user(user_in: UserIn):
#     user_saved = await fake_save_user(user_in)
#     return user_saved


# class BaseItem(BaseModel):
#     description: str
#     type: str


# class CarItem(BaseItem):
#     type: str = "car"


# class PlaneItem(BaseItem):
#     type: str = "plane"
#     size: int


# items = {
#     "item1": {"description": "All my friends drive a low rider", "type": "car"},
#     "item2": {
#         "description": "Music is my aeroplane, it's my aeroplane",
#         "type": "plane",
#         "size": 5,
#     },
# }


# @app.get(
#     "/items/{item_id}",
#     response_model=(PlaneItem | CarItem),
# )
# async def read_item(item_id: str):
#     if item_id not in items:
#         raise HTTPException(
#             status_code=404,
#             detail="Item not found",
#             headers={"X-Error": "There goes my error.. welp"},
#         )
#     return items[item_id]


# fake_db = {}


# class Item(BaseModel):
#     name: str | None = None
#     description: str | None = None
#     price: float | None = None
#     tax: float = 10.5
#     tags: list[str] = []


# items = {
#     "foo": {"name": "Foo", "price": 50.2},
#     "bar": {"name": "Bar", "description": "The bartenders", "price": 62, "tax": 20.2},
#     "baz": {"name": "Baz", "description": None, "price": 50.2, "tax": 10.5, "tags": []},
# }


# @app.put("/items/{item_id}", response_model=Item)
# async def update_item(item_id: str, item: Item):
#     update_item_encoded = jsonable_encoder(item)
#     items[item_id] = update_item_encoded
#     return update_item_encoded


# @app.patch("/items/{item_id}", response_model=Item)
# async def update_item(item_id: str, item: Item):
#     stored_item_data = items[item_id]
#     stored_item_model = Item(**stored_item_data)
#     update_data = item.dict(exclude_unset=True)
#     updated_item = stored_item_model.copy(update=update_data)
#     items[item_id] = jsonable_encoder(updated_item)
#     return updated_item


# data = {
#     "isbn-9781529046137": "The Hitchhiker's Guide to the Galaxy",
#     "imdb-tt0371724": "The Hitchhiker's Guide to the Galaxy",
#     "isbn-9781439512982": "Isaac Asimov: The Complete Stories, Vol. 2",
# }


# def check_valid_id(id: str) -> str:
#     if not id.startswith(("isbn-", "imdb-")):
#         raise ValueError('Invalid ID format, it must start with "isbn-" or "imdb-"')
#     return id


# @app.post("/offers/")
# async def create_offer(offer: Offer):
#     return offer


# @app.post("/images/multiple/")
# async def create_multiple_images(images: list[Image]):
#     return images


# @app.post("/users")
# async def create_user(user: UserIn) -> BaseUser:
#     return user


# @app.get("/items")
# async def read_items(
#     # filter_query: Annotated[FilterParams, Query()],
#     # ads_id: Annotated[str | None, Cookie()] = None,
#     # user_agent: Annotated[str | None, Header()] = None,
#     # accept: Annotated[str | None, Header()] = None,
# ) -> list[Item]:
#     # result = {
#     #     "ads_id": ads_id,
#     #     "User-Agent": user_agent,
#     #     "Accept": accept,
#     #     **filter_query.model_dump(),
#     # }
#     # return result
#     return [Item(name="Portal Gun", price=42), Item(name="Plumbus", price=32.5)]


# @app.post("/items")
# async def create_item(user_id: UUID, item: Annotated[Item, Body(embed=True)]) -> Item:
#     item_dict = item.model_dump()
#     result = {"user_id": user_id, **item_dict}
#     if item.tax is not None:
#         price_with_tax = item.price + item.tax
#         result.update({"price_with_tax": price_with_tax})
#     return item


# @app.put("/items/{item_id}")
# async def update_item(
#     item_id: Annotated[UUID, Path(title="The ID of the item to get")],
#     item: Item,
#     user: User,
#     start_datetime: Annotated[datetime, Body()],
#     end_datetime: Annotated[datetime, Body()],
#     process_after: Annotated[timedelta, Body()],
#     repeat_at: Annotated[time | None, Body()] = None,
#     importance: Annotated[int, Body()] = 1,
#     q: str | None = None,
# ):
#     start_process = start_datetime + process_after
#     duration = end_datetime - start_process
#     results = {
#         "item_id": item_id,
#         "item": item,
#         "user": user,
#         "start_datetime": start_datetime,
#         "end_datetime": end_datetime,
#         "process_after": process_after,
#         "repeat_at": repeat_at,
#         "start_process": start_process,
#         "duration": duration,
#         "importance": importance,
#     }
#     if q:
#         results.update({"q": q})
#     return results


# @app.get("/items/{item_id}/")
# async def read_item(
#     item_id: Annotated[
#         UUID,
#         Path(title="The ID of the item to get", gt=1, lt=100),
#     ],
#     key: Annotated[
#         str | None, Query(min_length=16, pattern="^api-", title="Api Key")
#     ] = None,
#     q: Annotated[str | None, Query(alias="item-query")] = None,
#     short: bool = False,
# ):
#     item = {"item_id": item_id, "key": key}
#     if q:
#         item.update({"q": q})
#     if not short:
#         item.update(
#             {"description": "This is an amazing item that has a long description"}
#         )
#     return item


# @app.get("/users/me/")
# async def read_user_me():
#     return {"user_id": "the current user"}


# @app.get("/users/{user_id}/items/{item_id}/")
# async def read_user_item(
#     user_id: UUID, item_id: UUID, q: str | None = None, short: bool = False
# ):
#     item = {"item_id": item_id, "owner_id": user_id}
#     if q:
#         item.update({"q": q})
#     if not short:
#         item.update(
#             {"description": "This is an amazing item that has a long description"}
#         )
#     return item


# @app.get("/models/{model_name}/")
# async def read_model(model_name: ModelName):
#     if model_name is ModelName.alexnet:
#         return {"model_name": model_name, "message": "Deep Learning FTW!"}

#     if model_name is ModelName.lenet:
#         return {"model_name": model_name, "message": "LeCNN all the images"}

#     return {"model_name": model_name, "message": "Have some residuals"}


# @app.get("/files/{file_path:path}/")
# async def read_file(file_path: str):
#     return {"file_path": file_path}
