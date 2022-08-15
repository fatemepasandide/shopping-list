from datetime import datetime
from xml.etree.ElementInclude import include
from tortoise import Model, fields
from pydantic import BaseModel
from tortoise.contrib.pydantic import pydantic_model_creator

class User(Model):
    id = fields.IntField(pk = True, index = True)
    username = fields.CharField(max_length = 10 , null= False ,unique = True)
    is_admin = fields.BooleanField(default=False)
    #email = fields.CharField(unique = True, max_length=20, null = False)
    password = fields.CharField(max_length = 100, null = False)
    #is_verified = fields.BooleanField(default= False)

class Product(Model):
    id = fields.IntField(pk = True, index = True)
    name = fields.CharField(max_length = 20, null = False, index = True)
    price = fields.DecimalField(max_digits= 10, decimal_places=2, null = False)
    description = fields.TextField(max_length=300)

class Order(Model):
    id = fields.IntField(pk = True, index = True)
    user = fields.ForeignKeyField("models.User" , related_name="orders")
    product = fields.ForeignKeyField("models.Product" , related_name="orders")
    order_time = fields.DateField(default= datetime.utcnow)


user_pydantic = pydantic_model_creator(User, name ="User")
user_pydantic_in = pydantic_model_creator(User, name="UserIN", exclude_readonly=True,
                                        include=("username","password"))
user_pydantic_out = pydantic_model_creator(User, name="UserOUT", exclude=("password",))

product_pydantic = pydantic_model_creator(Product, name ="Product" )
product_pydantic_in = pydantic_model_creator(Product, name="ProductIN", exclude=("id",))

order_pydantic = pydantic_model_creator(Order, name ="Order")#, include=("user", "product"))
order_pydantic_in = pydantic_model_creator(Order, name="OrderIN",
                                        exclude=("id","order_time"))


    