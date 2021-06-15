# from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
#
# app = Flask(__name__)
# # app.config['SQALCHEMY_DATABASE_URI'] =
#
# @app.route('/')
# def hello_world():
#     return 'Hello World!'
#
# if __name__ == '__main__':
#     app.run()
import json

import aiopg
from aiohttp import web
from asyncpg.exceptions import UniqueViolationError
from gino import Gino
from datetime import datetime

import config

app = web.Application()
db = Gino()


class BaseModel:

    @classmethod
    async def get_or_404(cls, id):
        instance = await cls.get(id)
        if instance:
            return instance
        raise web.HTTPNotFound()

    @classmethod
    async def create_instance(cls, **kwargs):
        try:
            instance = await cls.create(**kwargs)
        except UniqueViolationError:
            raise web.HTTPBadRequest()
        return instance

    @classmethod
    async def update_instance(cls, id, **kwargs):
        instance = await cls.get(id)
        if instance:
            await instance.update(**kwargs).apply()
        return instance

    @classmethod
    async def delete_instance(cls, id):
        instance = await cls.get(id)
        if instance:
            await instance.delete()
        return instance


class Advertisement(db.Model, BaseModel):

    __tablename__ = 'advertisements'

    id = db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow())
    owner = db.Column(db.String, nullable=False)

    # _idx1 = db.Index('advertisements_user_username', 'username', unique=True)

    def to_dict(self):
        adv_data = super().to_dict()
        adv_data['date'] = str(adv_data['date'])
        return adv_data


async def set_connection():
    return await db.set_bind(config.POSTGRE_URI)


async def disconnect():
    return await db.pop_bind().close()


async def pg_pool(app):
    async with aiopg.create_pool(config.POSTGRE_URI) as pool:
        app['pg_pool'] = pool
        yield
        pool.close()


async def orm_engine(app):
    app['db'] = db
    await set_connection()
    await db.gino.create_all()
    yield
    await disconnect()


class HealthView(web.View):

    async def get(self):
        return web.json_response({'status': 'OK'})


class AdvertisementView(web.View):

    async def post(self):
        post_data = await self.request.json()
        adv = await Advertisement.create_instance(**post_data)
        return web.json_response(adv.to_dict())

    async def get(self):
        adv_id = int(self.request.match_info['adv_id'])
        adv = await Advertisement.get_or_404(adv_id)
        return web.json_response(adv.to_dict())

    async def patch(self):
        adv_id = int(self.request.match_info['adv_id'])
        data = await self.request.json()
        adv = await Advertisement.update_instance(adv_id, **data)
        return web.json_response(adv.to_dict())

    async def delete(self):
        adv_id = int(self.request.match_info['adv_id'])
        adv = await Advertisement.delete_instance(adv_id)
        return web.json_response(adv.to_dict())

# app.cleanup_ctx.append(partial(register_connection_alchemy))
# app.cleanup_ctx.append(partial(register_connection))

# app.router.add_view('/adv/', AdvertisementView)


app.cleanup_ctx.append(orm_engine)
app.cleanup_ctx.append(pg_pool)

app.add_routes([web.get('/', HealthView)])
app.add_routes([web.post('/adv', AdvertisementView)])
app.add_routes([web.get('/adv/{adv_id:\d+}', AdvertisementView)])
app.add_routes([web.patch('/adv/{adv_id:\d+}', AdvertisementView)])
app.add_routes([web.delete('/adv/{adv_id:\d+}', AdvertisementView)])

web.run_app(app, host='127.0.0.1', port=8080)
