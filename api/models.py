from typing import Optional, Dict
from pydantic import BaseModel, Extra, constr

from db.db import Products
from flask import Request


class PostProductRequest(BaseModel):
    name: constr(max_length=100)
    description: Optional[str]
    price: float


class PutProductRequest(BaseModel):
    name: Optional[constr(max_length=100)]
    description: Optional[str]
    price: Optional[float]


class ErrorModel(BaseModel):
    source: str
    type: str
    description: str


class ProductModel(BaseModel):
    name: constr(max_length=100)
    price: float
    sales: int
    description: Optional[str]
    _links: Dict[str, Dict[str, str]]
    _embedded: Dict[str, Dict[str, Dict[str, str]]]

    class Config:
        extra = Extra.allow

    @staticmethod
    def create(product: Products, request: Request) -> 'ProductModel':
        """Creates ProductModel object from product and flask request

        Args:
            product (Products): database product object.
            request (Request): flask request object.

        Returns:
            ProductModel: pydantic model object.
        """
        item = ProductModel(
            name=product.name,
            price=product.price,
            sales=product.sales,
            _links=dict(
                self=dict(
                    href=(request.root_url +
                          f'api/v1/products/{product.name}')
                ),
                reviews=dict(
                    href=(request.url_root +
                          f'api/v1/products/{product.name}/reviews')
                ),
                orders=dict(
                    href=(request.url_root +
                          f'api/v1/products/{product.name}/reviews')
                )
            ),
            _embedded=dict(
                image=dict(
                    _links=dict(
                        self=(request.root_url +
                              product.image_url[1:])
                    )
                )
            )
        )
        if product.description:
            item.description = product.description

        return item


class ReviewModel(BaseModel):
    text: Optional[str]
    rating: int
    _links: Dict[str, Dict[str, str]]
    _embedded: Dict[str, Dict[str, Dict[str, str]]]

    class Config:
        extra = Extra.allow
