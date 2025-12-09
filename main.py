from enum import Enum
from typing import TypedDict

from fastapi import FastAPI
from pydantic import BaseModel


class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


app = FastAPI()


class FakeItem(TypedDict):
    item_name: str


fake_items_db: list[FakeItem] = [
    {"item_name": "Foo"},
    {"item_name": "Bar"},
    {"item_name": "Baz"},
]


@app.get("/items")
async def read_items(key: str, skip: int = 0, limit: int = 10):
    return {"key": key, "items": fake_items_db[skip : skip + limit]}


class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None


@app.post("/items")
async def create_item(item: Item):
    item_dict = item.model_dump()
    if item.tax is not None:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax": price_with_tax})
    return item_dict


@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item, key: str | None = None):
    result = {"item_id": item_id}
    if key is not None:
        result.update(**item.model_dump())
    return result


@app.get("/items/{item_id}")
async def read_item(item_id: int, key: str, q: str | None = None, short: bool = False):
    item = {"item_id": item_id, "key": key}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {"description": "This is an amazing item that has a long description"}
        )
    return item


@app.get("/users/me")
async def read_user_me():
    return {"user_id": "the current user"}


@app.get("/users/{user_id}/items/{item_id}")
async def read_user_item(
    user_id: int, item_id: int, q: str | None = None, short: bool = False
):
    item = {"item_id": item_id, "owner_id": user_id}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {"description": "This is an amazing item that has a long description"}
        )
    return item


@app.get("/models/{model_name}")
async def read_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}

    if model_name is ModelName.lenet:
        return {"model_name": model_name, "message": "LeCNN all the images"}

    return {"model_name": model_name, "message": "Have some residuals"}


@app.get("/files/{file_path:path}")
async def read_file(file_path: str):
    return {"file_path": file_path}
