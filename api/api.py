from flask import current_app, request, jsonify, Blueprint

import os
from pydantic import ValidationError
from werkzeug.utils import secure_filename

from db.db import Products, Reviews, Orders, db
from .tools import check_jwt, check_image
from .models import (ProductModel, ErrorModel,
                     PostProductRequest, PutProductRequest, ReviewModel)


api = Blueprint("api", __name__)


@api.before_request
def before_request():
    if not check_jwt(request.headers.get('Authorization', '')
                     .replace('Bearer ', ''),
                     current_app.config['SECRET_KEY'],
                     current_app.config['API_PASS']
                     ):
        return jsonify([
            ErrorModel(
                source='token',
                type='value_error.missing',
                message=('value is not '
                         'specified, expired or contains wrong data')
            ).dict()
        ])


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
            item = ProductModel.create(product, request)
            items.append(item.dict(by_alias=True, exclude_unset=True))

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

        image_error = check_image(image)
        image_error and custom_errors.append(image_error)

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

        item = ProductModel(product, request)

        return jsonify(item.dict(by_alias=True, exclude_unset=True))


@api.route('/products/<name>', methods=['GET', 'DELETE', 'PUT'])
def single_product(name):
    product = Products.query.filter_by(name=name).first_or_404()

    if request.method == 'GET':
        item = ProductModel.create(product, request)
        return jsonify(item.dict())

    elif request.method == 'DELETE':
        try:
            Reviews.query.filter_by(
                product_id=product.id).delete(synchronize_session=False)
            Orders.query.filter_by(
                product_id=product.id).delete(synchronize_session=False)
            db.session.delete(product)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f'ERROR WHILE DELETE PRODUCT BY API: {e}')

            db.session.rollback()
            return jsonify([
                ErrorModel(
                    source='server',
                    type='server_error.database',
                    description='Error with the database.'
                ).dict()
            ])

        return jsonify(
            status='Successfuly'
        )

    elif request.method == 'PUT':
        custom_errors = []

        try:
            prod = PutProductRequest(**request.form)
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

        image_error = check_image(image)
        image_error and custom_errors.append(image_error)

        if custom_errors:
            return jsonify(custom_errors)

        try:
            for k, v in prod:
                if v:
                    setattr(product, k, v)

            if image:
                old_image_url = product.image_url
                filename = secure_filename(image.filename)
                pictures = os.path.join(current_app.instance_path, 'pictures')
                image.save(os.path.join(pictures, filename))
                product.image_url = f'/pictures/{filename}'
                ('/static/images/notfound.png' != old_image_url
                 and os.remove(current_app.instance_path + old_image_url))

            db.session.add(product)
            db.session.commit()

        except Exception as e:
            current_app.logger.error(f'ERROR WHILE UPDATE PRODUCT BY API: {e}')

            db.session.rollback()
            return jsonify([
                ErrorModel(
                    source='server',
                    type='server_error.database',
                    description='Error with the database.'
                ).dict()
            ])

        item = ProductModel.create(product, request)
        return jsonify(item.dict(by_alias=True, exclude_unset=True))


@api.route('/products/<name>/reviews', methods=['GET', 'POST'])
def product_reviews(name):
    reviews = (Products.query.filter_by(name=name)
               .first_or_404()
               .reviews)

    sort_type = request.args.get('sort')
    if sort_type == 'asc_rating':
        reviews = reviews.order_by(Reviews.rating)
    elif sort_type == 'desc_rating':
        reviews = reviews.order_by(Reviews.rating.desc())

    reviews = reviews.all()

    # Limit borders
    start = (int(request.args.get('start', ''))
             if request.args.get('start', '').isdigit() else 1)
    end = (int(request.args.get('end', ''))
           if request.args.get('end', '').isdigit() else len(reviews))

    if request.method == 'GET':
        items = []
        for review in reviews[start-1:end]:
            item = ReviewModel(
                rating=review.rating,
                _links=dict(
                    self=dict(
                        href=request.url
                    ),
                    owner=dict(
                        href=(request.root_url +
                              f'api/v1/users/{review.owner_id}')
                    ),
                    product=dict(
                        href=(request.root_url +
                              f'api/v1/products/{name}')
                    )
                )
            )

            if review.text:
                item.text = review.text
            if review.image_url:
                item.embedded = dict(
                    image=dict(
                        _links=dict(
                            self=(request.root_url +
                                  review.image_url[1:])
                        )
                    )
                )

            items.append(item.dict(by_alias=True, exclude_unset=True))

        return jsonify(items)
