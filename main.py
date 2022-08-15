from itertools import product
from urllib import response
from fastapi import FastAPI , Depends, status, HTTPException
from tortoise import models
from tortoise.contrib.fastapi import register_tortoise
from models import *
from authentication import hash_pass, token_generator
import jwt
from dotenv import dotenv_values
from fastapi.security import (OAuth2PasswordBearer,
                             OAuth2PasswordRequestForm
                             )

config_credentials = dict(dotenv_values(".env"))

app = FastAPI()

oath2_scheme = OAuth2PasswordBearer(tokenUrl='token')


#user 

@app.post("/token")
async def generate_token(request_form : OAuth2PasswordRequestForm = Depends()):
    token = await token_generator(request_form.username, request_form.password)
    return {"access_token": token,
            "token type" : "bearer"
            }


async def get_current_user(token: str = Depends(oath2_scheme)):
    try:
        payload = jwt.decode(token, "secret", algorithms = ['HS256'])
        user = await User.get(id = payload.get("id"))
    except:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED, 
            detail = "Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await user


@app.post("/user/login")
async def user_login(user : user_pydantic_in = Depends(get_current_user)):
    order = await Order.get(user = user)
    shopping = order.product
    date = order.order_time

    return {"status" : "ok", 
            "data" : 
                {
                    "username" : user.username,
                    "shopping card" : shopping,
                    "date" : date
                    
                }
            }


@app.post('/user/registration')
async def user_registration(user: user_pydantic_in):
    '''
    Creation new user.
    Input : username , password.
    Your username have to be unique.
    New users are not admin as default, If you are admin check DB :)
    '''
    user_info = user.dict(exclude_unset=True)
    user_info['password'] = hash_pass(user_info['password'])
    user_obj = await User.create(**user_info)
    new_user = await user_pydantic.from_tortoise_orm(user_obj)
 
    return {"status" : "ok", 
            "data" : 
                f"Hello {new_user.username}"
                
            }

#product CRUD

@app.post("/product-add")
async def add_product(product : product_pydantic_in,
                      user : user_pydantic = Depends(get_current_user)
                      ):
    '''
    If you are admin you can add product.
    '''              
    if user.is_admin :
        product = product.dict(exclude_unset= True)
        product_obj = await Product.create(**product)
        product_obj = await product_pydantic.from_tortoise_orm(product_obj)
        return {
            "status" : 'ok',
            "data" : product_obj
        }
    else:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED, 
            detail = "Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.get("/product")
async def list_product():
    '''
    List of all product.
    '''
    response = await product_pydantic.from_queryset(Product.all())
    return {
        "status" : "ok",
        "data" : response
    }

@app.get("/product/{id}")
async def detail_product(id):
    '''
    Enter product Id from Product List.
    '''
    response = await product_pydantic.from_queryset_single(Product.get(id = id))
    print(type(response))
    return {"status" : "ok",
            "data" : 
                    {
                        "product_details" : response,

                    }
            }

@app.delete("/product-delete/{id}") 
async def delete_product(id: int,
                        user : user_pydantic = Depends(get_current_user)    
                        ):
    '''
    If you are admin, Enter product ID that you want to delete.
    '''
    if user.is_admin:
        deleted_product = await Product.filter(id=id).delete()
        if not deleted_product:
            raise HTTPException(status_code=404, detail=f"User {id} not found")
        return {
        "status" : "ok",
        "message" : f"Deleted product {id}"
        }
    
    else:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED, 
            detail = "Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
         )

@app.put("/product-update/{id}")
async def update_product(id:int,
                        product_info : product_pydantic_in,
                        user : user_pydantic = Depends(get_current_user)
                        ):
    '''
    If you are admin, Enter product ID that you want to update and change Request body.
    '''
    if user.is_admin :
        await Product.filter(id=id).update(**product_info.dict(exclude_unset=True))
        return await product_pydantic.from_queryset_single(Product.get(id=id))
    else:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED, 
            detail = "Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
         )

# order 

@app.post("/order")
async def create_order(product_id : int,
                    order : order_pydantic_in,
                    user : user_pydantic = Depends(get_current_user)
                    ):
    '''
    Choose product Id as order.(find product ID from product list)
    '''
    product = await product_pydantic.from_queryset(Product.filter(id=product_id))
    if not bool(product):
        raise HTTPException(status_code=404, detail="Item not found")
    order = await Order.create(user_id = user.id ,product_id= product_id)
    return {
            "status" : 'ok',
            "data" : order
        }


@app.get("/order-list")
async def list_order(user : user_pydantic = Depends(get_current_user)):
    '''
    List of your orders.
    ''' 
    order_list = await Order.filter(user_id=user.id)
    product_list = []
    for prdc in order_list:
        prdc_id = prdc.product_id
        _ = await Product.filter(id=prdc_id)
        product_list.append(_)

    if not bool(product_list):
        raise HTTPException(status_code=404, detail="You have not any Item")
    else:
        return {
            "status" : "ok",
            "data" : product_list
        
            }


@app.delete("/order-delete/{id}") 
async def delete_order(id: int,
                        user : user_pydantic = Depends(get_current_user) 
                        ):
    '''
    Enter order Id to delete.
    '''
    order_list = await Order.filter(user_id=user.id)
    for idx in range(len(order_list)): 
        if order_list[idx].id == id :
            deleted_order = await Order.filter(id=id).delete()
            return {
            "status" : "ok",
            "data" : deleted_order
            }
    else :
        raise HTTPException(status_code=404, detail="Item not found")

           


register_tortoise(
    app,
    db_url="sqlite://database.sqlite3",
    modules={"models":["models"]},
    generate_schemas=True,
    add_exception_handlers=True
)