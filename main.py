from enum import Enum
from typing import Annotated

from fastapi import Body, FastAPI, Path, Query
from pydantic import BaseModel, Field, HttpUrl


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


class User(BaseModel):
    username: str
    full_name: str | None = None


app = FastAPI()


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


@app.get("/items/")
async def read_items(filter_query: Annotated[FilterParams, Query()]):
    return filter_query


@app.post("/items/")
async def create_item(user_id: int, item: Annotated[Item, Body(embed=True)]):
    item_dict = item.model_dump()
    result = {"user_id": user_id, **item_dict}
    if item.tax is not None:
        price_with_tax = item.price + item.tax
        result.update({"price_with_tax": price_with_tax})
    return result


@app.put("/items/{item_id}")
async def update_item(
    item_id: Annotated[int, Path(title="The ID of the item to get", ge=0, le=1000)],
    item: Item,
    user: User,
    importance: Annotated[int, Body()] = 1,
    q: str | None = None,
):
    results = {"item_id": item_id, "item": item, "user": user}
    if q:
        results.update({"q": q})
    if importance:
        results.update({"importance": importance})
    return results


@app.get("/items/{item_id}/")
async def read_item(
    item_id: Annotated[
        int,
        Path(title="The ID of the item to get", gt=1, lt=100),
    ],
    key: Annotated[
        str | None, Query(min_length=16, pattern="^api-", title="Api Key")
    ] = None,
    q: Annotated[str | None, Query(alias="item-query")] = None,
    short: bool = False,
):
    item = {"item_id": item_id, "key": key}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {"description": "This is an amazing item that has a long description"}
        )
    return item


@app.get("/users/me/")
async def read_user_me():
    return {"user_id": "the current user"}


@app.get("/users/{user_id}/items/{item_id}/")
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
