import os
from dotenv import load_dotenv
from fastapi import FastAPI, status, Request
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import firestore, initialize_app, credentials
import json
import stripe

load_dotenv()
app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
    "https://frontend-ruby-rho.vercel.app",
    "https://magic-chat.com",
    "hooks.stripe.com",
    "api.stripe.com"
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
stripe_api_key = os.getenv('stripe_api_key')
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
        doc_ref = db.collection('users').document(user_id)

        new_balance = float(current_balance) - int(consumption)*0.002921
        print(new_balance)
        doc_ref.update({
            'currBalance': new_balance
        })

        return {"message": "success"}
    except BaseException as error:
        return {"message": str(error)}

@app.post("/stripe_payment")
async def stripe_payment(request: Request):
    """Stripe Payment Webhook, and update account details"""
    payload = await request.body()
    event = None

    try:
        event = stripe.Event.construct_from(
            json.loads(payload), stripe_api_key
        )
    except ValueError as e:
        # Invalid payload
        return JSONResponse(content={},status_code=400)

    # Handle the event
    if event.type == 'payment_intent.succeeded':
        payment_intent = event.data.object # contains a stripe.PaymentIntent
        # Then define and call a method to handle the successful payment intent.
        handle_payment_intent_succeeded(payment_intent)
    elif event.type == 'payment_method.attached':
        payment_method = event.data.object # contains a stripe.PaymentMethod
        # Then define and call a method to handle the successful attachment of a PaymentMethod.
        # handle_payment_method_attached(payment_method)
    # ... handle other event types
    else:
        print('Unhandled event type {}'.format(event.type))

    return JSONResponse(content={}, status_code=200)

def handle_payment_intent_succeeded(payment_intent):
    """Handle Successful payment"""
    user_id = payment_intent.metadata.user_id
    doc_ref = db.collection('users').document(user_id)

    doc = doc_ref.get()
    current_balance = doc.to_dict()['currBalance']
    print(payment_intent.amount/100)
    new_balance = float(current_balance) + float(payment_intent.amount/100)
    print(new_balance)
    doc_ref.update({
        'currBalance': new_balance
    })