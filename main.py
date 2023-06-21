import os
from dotenv import load_dotenv
from fastapi import FastAPI, status, Request
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import firestore, initialize_app, credentials
import json

load_dotenv()
app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
    "https://frontend-ruby-rho.vercel.app",
    "https://magic-chat.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

#---------------------
# Environment
#---------------------
cred = credentials.Certificate("magic-chat-ddf75-e3484fe17c32.json")
initialize_app(cred)
db = firestore.client()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get('/get-subs')
async def get_subs(user_id):
    """GET Subscription Balance"""
    try:
        doc_ref = db.collection('users').document(user_id)
        doc = doc_ref.get()
        current_balance = doc.to_dict()['currBalance']

        return {"data": current_balance}
    except BaseException as error:
        return {"message": str(error)}

@app.get('/update-subs')
async def update_subs(user_id:str, consumption:str, current_balance:str):
    try:
        print(user_id)
        doc_ref = db.collection('users').document(user_id)

        new_balance = float(current_balance) - int(consumption)*0.002921
        print(new_balance)
        doc_ref.update({
            'currBalance': new_balance
        })

        return {"message": "success"}
    except BaseException as error:
        return {"message": str(error)}