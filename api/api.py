from flask import current_app, request, jsonify, Blueprint

import jwt
import os
from typing import Optional, Dict
from pydantic import BaseModel, ValidationError, Extra, constr
from werkzeug.utils import secure_filename

from db.db import Products, db


api = Blueprint("api", __name__)


class PostProductRequest(BaseModel):
    name: constr(max_length=100)
    description: Optional[str]
    price: float


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


def is_allowed(filename: str) -> bool:
    """Check image extension and return boolean

    Args:
        filename (str): name of file

    Returns:
        bool: filename is valid image (png or jpg)
    """
    _, ext = os.path.splitext(filename.lower())
    if ext[1:] in ['png', 'jpg']:
        return True
    return False


def check_jwt(token: str) -> bool:
    """Check jwt token and return boolean

    Args:
        token (str): token to check
    Returns:
        bool: token is valid
    """
    try:
        data = jwt.decode(
            token, current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )

        assert data['password'] == current_app.config['API_PASS']

    except Exception:
        return False
    return True


@api.before_request
def before_request():
    if not check_jwt(request.headers.get('Authorization', '')
                     .replace('Bearer ', '')):
        return jsonify([
            ErrorModel(
                source='token',
                type='value_error.missing',
                message=('value is not '
                         'specified, expired or contains wrong data')
            ).dict()
        ])


def new_func():
    return 'source'


@api.route('/products', methods=['GET', 'POST'])
def products():
    if request.method == 'GET':
        sort_type = request.args.get('sort', '')

        # Match/case was replaced to support older python versions
        if sort_type == 'desc_price':
            products = Products.query.order_by(Products.price.desc()).all()
        elif sort_type == 'asc_price':
            products = Products.query.order_by(Products.price).all()
        elif sort_type == 'popular':
            products = Products.query.order_by(Products.sales.desc()).all()
        elif sort_type == 'alphabet':
            products = Products.query.order_by(Products.name).all()
        else:
            products = Products.query.all()

        # Limit borders
        start = (int(request.args.get('start', ''))
                 if request.args.get('start', '').isdigit() else 1)
        end = (int(request.args.get('end', ''))
               if request.args.get('end', '').isdigit() else len(products))

        items = []
        for product in products[start-1:end]:
            item = ProductModel(
                name=product.name,
                price=product.price,
                sales=product.sales,
                _links=dict(
                    self=dict(
                        href=(request.root_url +
                              f'/v1/products/{product.name}')
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

            items.append(item.dict())

        return jsonify(total=len(products),
                       items_count=len(items), items=items)

    elif request.method == 'POST':
        custom_errors = []

        try:
            prod = PostProductRequest(**request.form)
        except ValidationError as errors:
            errors = errors.errors()
            for e in errors:
                custom_errors.append(
                    ErrorModel(
                        source=e['loc'][0],
                        type=e['type'],
                        description=e['msg']
                    ).dict()
                )

        # If user specified image field, but not load file
        image = request.files.get('image')
        if image and not image.filename:
            image = None

        elif image and not is_allowed(image.filename):
            custom_errors.append(
                ErrorModel(
                    source='image',
                    type='type_error.image',
                    description=('extension is not allowed.'
                                 ' Please upload only .png or .jpg files.')
                ).dict()
            )

        if custom_errors:
            return jsonify(custom_errors)

        name = prod.name
        description = prod.description
        price = prod.price

        try:
            product = Products(name=name, price=price,
                               description=description)
            if image:
                filename = secure_filename(image.filename)
                pictures = os.path.join(current_app.instance_path, 'pictures')
                image.save(os.path.join(pictures, filename))
                product.image_url = f'/pictures/{filename}'

            db.session.add(product)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f'ERROR WHILE ADDING PRODUCT BY API: {e}')

            db.session.rollback()
            return jsonify([
                ErrorModel(
                    source='server',
                    type='server_error.database',
                    description='Error with the database.'
                ).dict()
            ])

        item = ProductModel(
            name=product.name,
            price=product.price,
            sales=product.sales,
            _links=dict(
                self=dict(
                    href=(request.root_url +
                          f'/v1/products/{product.name}')
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
        if description:
            item.description = description

        return jsonify(item.dict())
