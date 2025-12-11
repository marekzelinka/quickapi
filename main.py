from enum import Enum
from typing import Annotated
from uuid import UUID

from anyio import sleep
from fastapi import Body, FastAPI, File, Form, UploadFile, status
from pydantic import BaseModel, EmailStr, Field, HttpUrl


class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


class OrderBy(str, Enum):
    created_at = "created_at"
    updated_at = "updated_at"


class FilterParams(BaseModel):
    limit: int = Field(100, gt=0, le=100)
    offset: int = Field(0, ge=0)
    order_by: OrderBy = OrderBy.created_at
    tags: list[str] = []


class Image(BaseModel):
    url: HttpUrl
    name: str


class Item(BaseModel):
    name: str
    description: str | None = Field(
        None, title="The description of the item", max_length=300
    )
    price: float = Field(gt=0, description="The price must be greater than zero")
    tax: float | None = None
    tags: set[str] = set()
    images: list[Image] | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Foo",
                    "description": "A very cool item",
                    "price": 69.25,
                    "tax": 3.2,
                    "tags": ["cool"],
                }
            ]
        }
    }


class Offer(BaseModel):
    name: str
    description: str | None = None
    price: float
    items: list[Item]


# class BaseUser(BaseModel):
#     username: str
#     email: EmailStr
#     full_name: str | None = None


# class UserIn(BaseUser):
#     password: str


app = FastAPI()


class FormData(BaseModel):
    username: str
    password: str


@app.post("/login/", status_code=status.HTTP_201_CREATED)
async def login(formData: Annotated[FormData, Form()]):
    return {"username": formData.username, "password": formData.password}


@app.patch("/profile/avatar")
async def update_avatar_file(
    file: Annotated[
        UploadFile | None, File(description="Update profile avatar")
    ] = None,
):
    if not file:
        return {"message": "No avatar uploaded"}

    contents = await file.read()

    return {"filename": file.filename}


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None


class UserIn(UserBase):
    password: str


class UserOut(UserBase):
    pass


class UserInDB(UserBase):
    hashed_password: str


async def fake_hash_password(raw_password: str) -> str:
    await sleep(1)
    return f"supersecret{raw_password}"


async def fake_save_user(user_in: UserIn) -> UserInDB:
    hashed_password = await fake_hash_password(user_in.password)
    user_in_db = UserInDB(**user_in.model_dump(), hashed_password=hashed_password)
    print("User saved! Just kidding...")
    return user_in_db


@app.post("/user", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserIn):
    user_saved = await fake_save_user(user_in)
    return user_saved


class BaseItem(BaseModel):
    description: str
    type: str


class CarItem(BaseItem):
    type: str = "car"


class PlaneItem(BaseItem):
    type: str = "plane"
    size: int


items = {
    "item1": {"description": "All my friends drive a low rider", "type": "car"},
    "item2": {
        "description": "Music is my aeroplane, it's my aeroplane",
        "type": "plane",
        "size": 5,
    },
}


@app.get(
    "/items/{item_id}",
    response_model=(PlaneItem | CarItem),
    status_code=status.HTTP_200_OK,
)
async def read_item(item_id: str):
    return items[item_id]


data = {
    "isbn-9781529046137": "The Hitchhiker's Guide to the Galaxy",
    "imdb-tt0371724": "The Hitchhiker's Guide to the Galaxy",
    "isbn-9781439512982": "Isaac Asimov: The Complete Stories, Vol. 2",
}


def check_valid_id(id: str) -> str:
    if not id.startswith(("isbn-", "imdb-")):
        raise ValueError('Invalid ID format, it must start with "isbn-" or "imdb-"')
    return id


@app.post("/offers/")
async def create_offer(offer: Offer):
    return offer


@app.post("/images/multiple/")
async def create_multiple_images(images: list[Image]):
    return images


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


@app.post("/items")
async def create_item(user_id: UUID, item: Annotated[Item, Body(embed=True)]) -> Item:
    item_dict = item.model_dump()
    result = {"user_id": user_id, **item_dict}
    if item.tax is not None:
        price_with_tax = item.price + item.tax
        result.update({"price_with_tax": price_with_tax})
    return item


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


@app.get("/users/me/")
async def read_user_me():
    return {"user_id": "the current user"}


@app.get("/users/{user_id}/items/{item_id}/")
async def read_user_item(
    user_id: UUID, item_id: UUID, q: str | None = None, short: bool = False
):
    item = {"item_id": item_id, "owner_id": user_id}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {"description": "This is an amazing item that has a long description"}
        )
    return item


@app.get("/models/{model_name}/")
async def read_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}

    if model_name is ModelName.lenet:
        return {"model_name": model_name, "message": "LeCNN all the images"}

    return {"model_name": model_name, "message": "Have some residuals"}


@app.get("/files/{file_path:path}/")
async def read_file(file_path: str):
    return {"file_path": file_path}
