"""API Implementation"""
import json
from datetime import datetime
from functools import wraps
from logging.config import dictConfig
import logging
import jwt
from fastapi import Depends, FastAPI,status,HTTPException, Request, Form,UploadFile,File,Query
from sqlalchemy.orm import Session
from db import LoginRequest, StudentCreate,TokenSchema,ChangePasswordSchema,employee,ClientCreate, TechStackCreate, Client_RequisitionCreate, RequiredPositionCreate
from deps import JWTBearer
from utils import create_access_token,create_refresh_token, get_hashed_password, verify_password,JWT_SECRET_KEY,ALGORITHM 
from config import engine,SessionLocal,Base,User,TokenTable ,Client, TechStack, Client_Requisition,employeedata
from loggers import LogConfig
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, List
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from exchangelib import Credentials, Account, Message, DELEGATE, HTMLBody
from exchangelib.attachments import FileAttachment
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from collections import defaultdict
 

templates = Jinja2Templates(directory="templates")



dictConfig(LogConfig().dict())
logger = logging.getLogger("mycoolapp")
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
Base.metadata.create_all(engine)

def get_db():
    """Session DB"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

#decorator required to access data
def token_required(func):
    """Token required decorator"""
    @wraps(func)
    def wrapper(**kwargs):
        payload = jwt.decode(kwargs['dependencies'], JWT_SECRET_KEY, ALGORITHM)
        user_id = payload['sub']
        data= kwargs['db'].query(TokenTable).filter_by(user_id=user_id,access_toke=kwargs['dependencies'],status=True).first()
        if data:
            return func(kwargs['dependencies'],kwargs['db'])
        else:
            return {'msg': "Token blocked"}    
    return wrapper


@app.get("/students/all")
def get_students(db: Session = Depends(get_db)):
    """get all user"""
    try:
        students = db.query(User).all()
        logger.info("details fetched successfully")
        return students
    except Exception as e:
        logger.error("An error occurred: %s", str(e))
        return {"error": "Internal server error"}



@app.post("/students/")
def signup(student: StudentCreate, db: Session = Depends(get_db)):
    """Signup API"""
    try:
        existing_user = db.query(User).filter(User.email == student.email).first()
        if existing_user:
            logger.warning("exist email Warning")
            return {"message": "Email already exists"}
            
        
        # encrypted_password = hashpw(student.password.encode('utf-8'), gensalt())
        hashed_password=get_hashed_password(student.password)
        new_user = User(lname=student.lname, fname=student.fname, email=student.email, password=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info("User created successfully")
        return {"message": "User created successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
 
 
@app.post('/login' ,response_model=TokenSchema)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login API"""
    user = db.query(User).filter(User.email == request.email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email")
    hashed_pass = user.password
    if not verify_password(request.password, hashed_pass):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )
    
    access=create_access_token(user.id)
    refresh = create_refresh_token(user.id)

    token_db = TokenTable(user_id=user.id,  access_toke=access,  refresh_toke=refresh, status=True)
    db.add(token_db)
    db.commit()
    db.refresh(token_db)
    return {
        "access_token": access,
        "refresh_token": refresh,
    }
    

@app.post("/changepassword")
def change_password(request: ChangePasswordSchema, dependencies=Depends((JWTBearer())), db: Session = Depends(get_db)):
    """Change Password API"""
    try:
        user = db.query(User).filter(User.email == request.email).first()
        if user is None:
            logger.error("Dummy Error")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        if not verify_password(request.old_password, user.password):
            # return {"message": "Invalid password"}
            logger.error("Dummy Error")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect old password")
        encrypted_password = get_hashed_password(request.new_password)
        user.password = encrypted_password
        db.commit()
        logger.info("Dummy Info")
        return {"message": "Password changed successfully"}
    except HTTPException as http_exception:
        raise http_exception
    except Exception as e:
        logger.error("An error occurred: %s", str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while changing password") from e


@app.post('/logout')
@token_required
def logout(dependencies=Depends(JWTBearer()), db: Session = Depends(get_db)):
    """Logout API"""
    try:
        token=dependencies
        payload = jwt.decode(token, JWT_SECRET_KEY, ALGORITHM)
        user_id = payload['sub']
        token_record = db.query(TokenTable).all()
        info=[]
        for record in token_record :
            print("record",record)
            if (datetime.utcnow() - record.created_date).days >1:
                info.append(record.user_id)
        if info:
            existing_token = db.query( TokenTable).where(TokenTable.user_id.in_(info)).delete()
            db.commit()
            
        existing_token = db.query( TokenTable).filter( TokenTable.user_id == user_id,  TokenTable.access_toke==token).first()
        if existing_token:
            existing_token.status=False
            db.add(existing_token)
            db.commit()
            db.refresh(existing_token)
        return {"message":"Logout Successfully"} 
    except Exception as e:
        logger.error("An error occurred: %s", str(e))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authenticated") from e

# ------------------------------------------------------------------------------------------------
# client 

@app.get("/base", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/add_client/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    client_list = {"client_list": db.query(Client).all()}
    return templates.TemplateResponse("client_form.html", {"request": request, **client_list})

@app.post("/add_client/")
def create_client(request: Request, name: str = Form(),
                  email: str = Form(),
                  address: str = Form(),
                  db: Session = Depends(get_db)):
    client_list = {"client_list": db.query(Client).all()}
    new_user = Client(name=name, email=email, address=address)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    message = {"message": "Client created successfully"}
    return templates.TemplateResponse("client_form.html", {"request": request, **message, **client_list})

@app.get("/clients/")
def get_clients(name: Optional[str] = None, client_id: Optional[int] = None, db: Session = Depends(get_db)):
    if client_id is not None:
        client = db.query(Client).filter(Client.id == client_id).first()
        if client is None:
            raise HTTPException(status_code=404, detail="Client not found")
        return [client]

    if name is not None:
        clients = db.query(Client).filter(Client.name == name).all()
    else:
        clients = db.query(Client).all()

    return clients

# =========================================================================================================================
# client_requisitions


@app.get("/requisition", response_class=HTMLResponse)
async def required_position(request: Request, db: Session = Depends(get_db)):
    client_list = {"client_list": db.query(Client).all()}
    tech_list = {"tech_list": db.query(TechStack).all()}
    return templates.TemplateResponse("requisition.html", {"request": request, **client_list, **tech_list})


@app.post("/client_requisitions/")
def create_client_requisition(request: Request, client_name: str = Form(), tech_stack: List[str] = Form(),
                              jdstatus: bool = Form(default=None), position_request: str = Form(default=None),
                              reference_email: str = Form(default=None), requestby: str = Form(default=None),
                              status: str = Form(default=None),
                              resource_provided: bool = Form(default=None),
                              profile_shared_count: int = Form(default=None),
                              accepted_count: int = Form(default=None), rejected_count: int = Form(default=None),
                              comments: str = Form(default=None), db: Session = Depends(get_db)):
    tech_list = {"tech_list": db.query(TechStack).all()}
    tech_stack_str = ",".join(map(str, tech_stack))
    client_list = {"client_list": db.query(Client).all()}
    client_object = db.query(Client).filter(Client.name == client_name).first()
    client_id = client_object.id
    if profile_shared_count == accepted_count + rejected_count and accepted_count >= 0 and rejected_count >= 0:
        new_client_requisition = Client_Requisition(client_id=client_id, tech_stack_str=tech_stack_str,
                                                    jdstatus=jdstatus, position_request=position_request,
                                                    reference_email=reference_email,
                                                    requestby=requestby, status=status,
                                                    resource_provided=resource_provided,
                                                    profile_shared_count=profile_shared_count,
                                                    accepted_count=accepted_count,
                                                    rejected_count=rejected_count, comments=comments)
        db.add(new_client_requisition)
        db.commit()
        db.refresh(new_client_requisition)
        message = {"message": "Client Requisition created successfully"}
        return templates.TemplateResponse("requisition.html",
                                          {"request": request, **client_list, **tech_list, **message})
    else:
        return templates.TemplateResponse("invalid.html", {"request": request})

@app.get("/client-requisitions/")
def get_client_requisitions(db: Session = Depends(get_db)):
    requisitions = db.query(Client_Requisition).all()
    return requisitions


@app.get("/requisition_table")
def get_client_requisitions(request: Request, client_requisition_id: Optional[int] = None,
                            db: Session = Depends(get_db)):
    if client_requisition_id is not None:
        requisition = db.query(Client_Requisition).filter(Client_Requisition.id == client_requisition_id).first()
        if requisition is None:
            raise HTTPException(status_code=404, detail="Client Requisition not found")
        return [requisition]
    requisitions = db.query(Client_Requisition).all()
    requisitions_with_client = []
    for requisition in requisitions:
        client = db.query(Client).filter(Client.id == requisition.client_id).first()
        if client:
            client_name = client.name
            requisition_dict = requisition.__dict__
            requisition_dict['client_name'] = client_name
            requisitions_with_client.append(requisition_dict)
    requisitions = {"requisitions": db.query(Client_Requisition).filter(Client_Requisition.delete_status=="activate").all()}
    return templates.TemplateResponse("client_requisition_table.html", {"request": request, **requisitions})





# @app.get("/")
# def get_client_requisitions(request: Request, client_requisition_id: Optional[int] = None,
#                             db: Session = Depends(get_db)):
#     if client_requisition_id is not None:
#         requisition = db.query(Client_Requisition).filter(Client_Requisition.id == client_requisition_id).first()
#         if requisition is None:
#             raise HTTPException(status_code=404, detail="Client Requisition not found")
#         return [requisition]
#     requisitions = db.query(Client_Requisition).all()
#     requisitions_with_client = []
#     for requisition in requisitions:
#         client = db.query(Client).filter(Client.id == requisition.client_id).first()
#         if client:
#             client_name = client.name
#             requisition_dict = requisition.__dict__
#             requisition_dict['client_name'] = client_name
#             requisitions_with_client.append(requisition_dict)
#     requisitions = {"requisitions": db.query(Client_Requisition).filter(Client_Requisition.delete_status == "active").all()}
#     return templates.TemplateResponse("client_requisition_table.html", {"request": request, **requisitions})


@app.get("/client_requisition/{requisition_id}", response_class=HTMLResponse)
def update_client_requisition(requisition_id: int, request: Request, db: Session = Depends(get_db)):
    requisition = db.query(Client_Requisition).get(requisition_id)
    client_name = {"client_name": db.query(Client).get(requisition.client_id)}
    requisition_data = {"requisition_data": requisition}
    client_list = {"client_list": db.query(Client).all()}
    tech_list = {"tech_list": db.query(TechStack).all()}
    return templates.TemplateResponse("update_client_requisition.html",
                                      {"request": request, **requisition_data, **client_list, **tech_list,
                                       **client_name})


@app.post("/client_requisition_upd/{requisition_id}")
def update_client_requisition(
        request: Request,
        requisition_id: int,
        client_name: str = Form(),
        tech_stack: List[str] = Form(),
        jdstatus: bool = Form(default=None),
        position_request: str = Form(default=None),
        reference_email: str = Form(default=None),
        requestby: str = Form(default=None),
        status: str = Form(default=None),
        resource_provided: bool = Form(default=None),
        profile_shared_count: int = Form(default=None),
        accepted_count: int = Form(default=None),
        rejected_count: int = Form(default=None),
        comments: str = Form(default=None),
        db: Session = Depends(get_db)):

    print("****************",tech_stack)
    tech_stack_str = ",".join(map(str, tech_stack))
    print("****************",tech_stack_str)


    client_object = db.query(Client).filter(Client.name == client_name).first()
    if client_object is None:
        return {"error": "Client not found"}

    existing_requisition = db.query(Client_Requisition).filter(Client_Requisition.id == requisition_id).first()
    if existing_requisition is None:
        return {"error": "Client Requisition not found"}

    existing_requisition.client_id = client_object.id
    existing_requisition.tech_stack_str = tech_stack_str
    existing_requisition.jdstatus = jdstatus
    existing_requisition.position_request = position_request
    existing_requisition.reference_email = reference_email
    existing_requisition.requestby = requestby
    existing_requisition.status = status
    existing_requisition.resource_provided = resource_provided
    existing_requisition.profile_shared_count = profile_shared_count
    existing_requisition.accepted_count = accepted_count
    existing_requisition.rejected_count = rejected_count
    existing_requisition.comments = comments

    db.commit()

    requisitions = {"requisitions": db.query(Client_Requisition).all()}
    return RedirectResponse(url="http://127.0.0.1:8000",status_code=303)
    # return templates.TemplateResponse("home.html", {"request": request, **requisitions})


@app.get("/client_requisitions_put/{requisition_id}/")
def update_client_requisition(request: Request,
        requisition_id: int,
        delete_status: str = Form(default="inactive"),
        db: Session = Depends(get_db)):
    requisition = db.query(Client_Requisition).get(requisition_id)
    if requisition is None:
        raise HTTPException(status_code=404, detail="Requisition not found")
    requisition.delete_status = delete_status
    db.commit()
    return RedirectResponse(url="http://127.0.0.1:8000")

# @app.get("data_filter/")
# def allrecords():



# ===============================================================================================================
# TechStack

@app.get("/tech", response_class=HTMLResponse)
async def tech(request: Request, db: Session = Depends(get_db)):
    tech_1 = {"tech_1": db.query(TechStack).all()}
    return templates.TemplateResponse("tech_stack.html", {"request": request,**tech_1})


@app.post("/tech_stack/")
def create_tech_stack(request: Request, technology: str = Form(), db: Session = Depends(get_db)):
    new_tech_stack = TechStack(technology=technology)
    db.add(new_tech_stack)
    db.commit()
    db.refresh(new_tech_stack)
    message = {"message": "Tech stack created successfully"}
    tech_1 = {"tech_1": db.query(TechStack).all()}
    return templates.TemplateResponse("tech_stack.html", {"request": request, **message,**tech_1})


# @app.get("/tech/")
# def get_client_requisitions(db: Session = Depends(get_db)):
#     tech_1 = db.query(TechStack).all()
#     return tech_1


# @app.get("/tech_stack/", response_class=HTMLResponse)
# async def home(request: Request, db: Session = Depends(get_db)):
    # tech_1 = {"tech_1": db.query(TechStack).all()}
#     return templates.TemplateResponse("tech_stack.html", {"request": request, **tech_1})

# -------------------------------------------------------------------------------------------
# email Api

from cache import *
@app.get("/email_thread_data/{subject}", response_class=HTMLResponse)
def reply_to_thread_data(request: Request, subject):
    if subject in cache:
        email_thread_data = cache[subject]

    else:
        email_thread_data = get_email_thread_data(subject)
        cache[subject] = email_thread_data


    # main_credentials = Credentials("chnarsimha986@outlook.com", "Narsimha123@#$")
    # main_account = Account("chnarsimha986@outlook.com", credentials=main_credentials, autodiscover=True, access_type=DELEGATE)
    # inbox = main_account.inbox
    # emails = inbox.filter(subject__icontains=subject)
    # email_thread_data = []
    #
    # for email in emails:
    #     formatted_timestamp = email.datetime_sent.date()
    #     clean_subject = email.subject.strip()
    #     while clean_subject.startswith("Re:"):
    #         clean_subject = clean_subject[3:].strip()
    #     table_data_list = []
    #     text_data = ''
    #     soup = BeautifulSoup(email.body, 'html.parser')
    #     tables = soup.find_all('table')
    #     texts = soup.find_all('p')
    #
    #     for text in texts:
    #         text_data = text.text
    #
    #     for table in tables:
    #         table_data = []
    #         rows = table.find_all('tr')
    #         for row in rows:
    #             cells = row.find_all(['td', 'th'])
    #             row_data = [cell.get_text().strip() for cell in cells]
    #             table_data.append(row_data)
    #         if table_data:
    #             headers = table_data[0]
    #             table_data = table_data[1:]
    #             table_data_list = [dict(zip(headers, row)) for row in table_data]
    #
    #     # table_data_json = json.dumps(table_data_list, indent=4)
    #
    #     thread_data = {
    #         "subject": clean_subject,
    #         "sender": email.sender.email_address,
    #         "recipients": ", ".join([to.email_address for to in email.to_recipients]),
    #         "receiver": email.receiver.email_address if hasattr(email, 'receiver') else "",
    #         "cc": [cc.email_address for cc in email.cc_recipients] if email.cc_recipients else [],
    #         "timestamp": formatted_timestamp,
    #         "time": email.datetime_sent.strftime("%H:%M:%S %p"),
    #         "text": text_data,
    #         "table": table_data_list,
    #         "has_attachments": bool(email.attachments),
    #     }
    #     if email.attachments:
    #         attachments = []
    #         for attachment in email.attachments:
    #             attachment_info = {
    #                 "filename": attachment.name,
    #                 "content_type": attachment.content_type,
    #                 "size": attachment.size,
    #             }
    #             attachments.append(attachment_info)
    #         thread_data["attachments"] = attachments
    #     email_thread_data.append(thread_data)
    return templates.TemplateResponse("email.html", {"request": request, "email_thread_data": email_thread_data,"subject": subject})


@app.get("/reply", response_class=HTMLResponse)
async def show_form(
        request: Request,
        subject: str = Query(default=None),
        selected_ids: str = Query(default=None), reply_email1: str = Form(default=None),
        db: Session = Depends(get_db)):
    if subject in cache:
        email_thread_data = cache[subject]
    else:
        email_thread_data = get_email_thread_data(subject)
        cache[subject] = email_thread_data
        cache[subject][0]['recipients'].append(cache[subject][0]['sender'])
        cache[subject][0]['recipients'] = list(set(cache[subject][0]['recipients']))



    # main_credentials = Credentials("databasedb123@outlook.com", "Abhi@7671")
    # main_account = Account("databasedb123@outlook.com", credentials=main_credentials, autodiscover=True,
    #                        access_type=DELEGATE)
    # inbox = main_account.inbox
    # emails = inbox.filter(subject__icontains=subject)
    # from_addresses = {email.sender.email_address for email in emails}
    # to_recipients = {r.email_address for email in emails for r in email.to_recipients}
    # # print(to_recipients,"**************")
    # cc_recipients = {r.email_address for email in emails for r in (email.cc_recipients or [])}
    # # Combine all unique participants
    # all_participants = list(from_addresses | to_recipients | cc_recipients)
    # participants = list(set(all_participants))
    # # print("participants - ",participants)
    # parting = participants
    employees_info = []
    table = None
    email_text = ''
    if selected_ids:
        selected_ids_list = selected_ids.split(",")
        for emp_id in selected_ids_list:
            employee = db.query(employeedata).filter(employeedata.emp_id == int(emp_id)).first()
            if employee:
                employees_info.append(employee)
    if employees_info:
        table = """
        <table class="table table-striped text-center" id="myTable" style="margin-bottom: 0rem; font-size: 15px;border-bottom-color: #e4f3ee00">
            <thead>
                <tr>
                    <th><b>ID</b></th>
                    <th><b>emp_id</b></th>
                    <th><b>associate_name</b></th>
                    <th><b>department</b></th>
                    <th><b>reporting_manager</b></th>
                    <th><b>digital_lead</b></th>
                    <th><b>tech_stack</b></th>
                    <th><b>experience</b></th>
                    <th><b>competency</b></th>
                </tr>
            </thead>
            <tbody>
        """
        for emp in employees_info:
            table += f"""
            <tr>
                <td>{emp.id}</td>
                <td>{emp.emp_id}</td>
                <td>{emp.associate_name}</td>
                <td>{emp.department}</td>
                <td>{emp.reporting_manager}</td>
                <td>{emp.digital_lead}</td>
                <td>{emp.tech_stack}</td>
                <td>{emp.experience}</td>
                <td>{emp.competency}</td>
            </tr>
            """
        table += """
            </tbody>
        </table>
        """
        email_text = """Hello,
I hope this email finds you well. I wanted to follow up on our recent discussion and let you know that our team,
consisting of the following associates:\n"""

        for emp in employees_info:
            email_text += f"""\n{emp.associate_name}"""

        email_text +="""\n\nhas been diligently working on identifying potential candidates for your open positions.
We have taken the next step in our search and have now shared these candidate profiles with you.
Please take a moment to review the attached profiles and provide us with your feedback."""
    # return HTMLResponse(content=html_content)
    return templates.TemplateResponse(
        "send_email_1.html",
        {"request": request, "default_subject": subject, "employees_info": employees_info, "selected_ids": selected_ids,
         'table': table, "email_thread_data": email_thread_data, 'email_text': email_text}
    )

@app.post("/emailThread/")
async def reply_to_thread(request: Request, reply_email1: List[str] = Form(default=None),
                          subject1: str = Form(default=None),
                          comments: str = Form(default=None), myListItems: List[str] = Form(default=None),
                          attachment: UploadFile = File(default=None), selected_ids: str = Form(default=None),
                          db: Session = Depends(get_db)):
    print(reply_email1, "**********888")
    employees_info = []
    if selected_ids != 'None':
        selected_ids_list = selected_ids.split(",")
        for emp_id in selected_ids_list:
            employee = db.query(employeedata).filter(employeedata.emp_id == int(emp_id)).first()
            if employee:
                employees_info.append(employee)
    data = f"""
                <p> {comments} </p>
                <br>
                """
    if employees_info:
        info = []
        for employee in employees_info:
            order = {"emp_id": employee.emp_id, "associate_name": employee.associate_name,
                     "department": employee.department, "reporting_manager": employee.reporting_manager,
                     "digital_lead": employee.digital_lead, "tech_stack": employee.tech_stack,
                     "experience": employee.experience, "competency": employee.competency}
            info.append(order)
        data += """
            <style>
                table, th, td {
                    border: 1px solid #000;
                }
            </style>
            <br>
            <br>
            <table class="table table-striped text-center" id="myTable">
                <thead>
                    <tr>
                        <th><b>ID</b></th>
                        <th><b>emp_id</b></th>
                        <th><b>associate_name</b></th>
                        <th><b>department</b></th>
                        <th><b>reporting_manager</b></th>
                        <th><b>digital_lead</b></th>
                        <th><b>tech_stack</b></th>
                        <th><b>experience</b></th>
                        <th><b>competency</b></th>
                    </tr>
                </thead>
                <tbody>
            """
        for emp in employees_info:
            data += f"""
                <tr>
                    <td>{emp.id}</td>
                    <td>{emp.emp_id}</td>
                    <td>{emp.associate_name}</td>
                    <td>{emp.department}</td>
                    <td>{emp.reporting_manager}</td>
                    <td>{emp.digital_lead}</td>
                    <td>{emp.tech_stack}</td>
                    <td>{emp.experience}</td>
                    <td>{emp.competency}</td>
                </tr>
                """
        data += """
                </tbody>
            </table>
            """
    main_credentials = Credentials("rammouri123@outlook.com", "Abhi@7671")
    main_account = Account("rammouri123@outlook.com", credentials=main_credentials, autodiscover=True,
                           access_type=DELEGATE)
    inbox = main_account.inbox
    emails = inbox.filter(subject__icontains=subject1)
    for email in emails:
        pass
    reply_text = comments
    reply_account = reply_email1
    print(reply_account, "To Addresss")
    print(type(reply_account))
    participants = list(set(myListItems))
    print(type(participants))
    for toadd in reply_account:
        if toadd in participants:
            participants.remove(toadd)
    print("Updated_particiapents___________", participants)
    # if reply_account in participants:
    #     participants.remove(reply_account)
    email_data_body = f"\n\n{data}"
    parting = participants
    reply = Message(
        account=main_account,
        folder=main_account.inbox,
        # subject=f"Re: {email.subject}",
        subject=(email.subject),
        body=HTMLBody(email_data_body),
        to_recipients=reply_account,
        cc_recipients=participants,
        references=email.message_id,
        in_reply_to=email.message_id,
    )
    if attachment and attachment.filename:
        attachment_data = attachment.file.read()
        attachment_obj = FileAttachment(name=attachment.filename, content=attachment_data)
        reply.attach(attachment_obj)
    reply.send()
    print("Replied to:", email.subject)
    return RedirectResponse(url="http://127.0.0.1:8000", status_code=303)


# @app.get("/reply", response_class=HTMLResponse)
# async def show_form(
#         request: Request,
#         subject: str = Query(default=None),
#         selected_ids: str = Query(default=None), reply_email1:str = Form(default=None),
#         db: Session = Depends(get_db)):
#
#     main_credentials = Credentials("chnarsimha986@outlook.com", "Narsimha123@#$")
#     main_account = Account("chnarsimha986@outlook.com", credentials=main_credentials, autodiscover=True,
#                            access_type=DELEGATE)
#     inbox = main_account.inbox
#     emails = inbox.filter(subject__icontains=subject)
#     from_addresses = {email.sender.email_address for email in emails}
#     to_recipients = {r.email_address for email in emails for r in email.to_recipients}
#     cc_recipients = {r.email_address for email in emails for r in (email.cc_recipients or [])}
#     # Combine all unique participants
#     all_participants = list(from_addresses | to_recipients | cc_recipients)
#     participants = list(set(all_participants))
#     parting = participants
#
#
#     employees_info = []
#     table = None
#     if selected_ids:
#         selected_ids_list = selected_ids.split(",")
#         for emp_id in selected_ids_list:
#             employee = db.query(employeedata).filter(employeedata.emp_id == int(emp_id)).first()
#             if employee:
#                 employees_info.append(employee)
#     if employees_info:
#         table = """
#         <table class="table table-striped text-center" id="myTable">
#             <thead>
#                 <tr>
#                     <th><b>ID</b></th>
#                     <th><b>emp_id</b></th>
#                     <th><b>associate_name</b></th>
#                     <th><b>department</b></th>
#                     <th><b>reporting_manager</b></th>
#                     <th><b>digital_lead</b></th>
#                     <th><b>tech_stack</b></th>
#                     <th><b>experience</b></th>
#                     <th><b>competency</b></th>
#                 </tr>
#             </thead>
#             <tbody>
#         """
#         for emp in employees_info:
#             table += f"""
#             <tr>
#                 <td>{emp.id}</td>
#                 <td>{emp.emp_id}</td>
#                 <td>{emp.associate_name}</td>
#                 <td>{emp.department}</td>
#                 <td>{emp.reporting_manager}</td>
#                 <td>{emp.digital_lead}</td>
#                 <td>{emp.tech_stack}</td>
#                 <td>{emp.experience}</td>
#                 <td>{emp.competency}</td>
#             </tr>
#             """
#         table += """
#             </tbody>
#         </table>
#         """
#     # return HTMLResponse(content=html_content)
#     return templates.TemplateResponse(
#         "send_email.html",
#         {"request": request, "default_subject": subject, "employees_info": employees_info, "selected_ids": selected_ids,
#          'table': table,"participants":parting}
#     )


# @app.post("/emailThread/")
# async def reply_to_thread(request: Request, reply_email1: str = Form(default=None),
#                           subject1: str = Form(default=None),
#                           reply_text1: str = Form(default=None), myListItems: List[str] = Form(default=None),
#                           attachment: UploadFile = File(default=None), selected_ids: str = Form(default=None),
#                           db: Session = Depends(get_db)):
#     print("cc_recipients*************",myListItems)
#     employees_info = []
#     if selected_ids != 'None':
#         selected_ids_list = selected_ids.split(",")
#         for emp_id in selected_ids_list:
#             employee = db.query(employeedata).filter(employeedata.emp_id == int(emp_id)).first()
#             if employee:
#                 employees_info.append(employee)
#     data = f"""
#                 <p> {reply_text1} </p>
#                 <br>
#                 """
#     if employees_info:
#         info = []
#         for employee in employees_info:
#             order = {"emp_id": employee.emp_id, "associate_name": employee.associate_name,
#                      "department": employee.department, "reporting_manager": employee.reporting_manager,
#                      "digital_lead": employee.digital_lead, "tech_stack": employee.tech_stack,
#                      "experience": employee.experience, "competency": employee.competency}
#             info.append(order)
#         data += """
#             <style>
#                 table, th, td {
#                     border: 1px solid #000;
#                 }
#             </style>
#             <br>
#             <br>
#             <table class="table table-striped text-center" id="myTable">
#                 <thead>
#                     <tr>
#                         <th><b>ID</b></th>
#                         <th><b>emp_id</b></th>
#                         <th><b>associate_name</b></th>
#                         <th><b>department</b></th>
#                         <th><b>reporting_manager</b></th>
#                         <th><b>digital_lead</b></th>
#                         <th><b>tech_stack</b></th>
#                         <th><b>experience</b></th>
#                         <th><b>competency</b></th>
#                     </tr>
#                 </thead>
#                 <tbody>
#             """
#         for emp in employees_info:
#             data += f"""
#                 <tr>
#                     <td>{emp.id}</td>
#                     <td>{emp.emp_id}</td>
#                     <td>{emp.associate_name}</td>
#                     <td>{emp.department}</td>
#                     <td>{emp.reporting_manager}</td>
#                     <td>{emp.digital_lead}</td>
#                     <td>{emp.tech_stack}</td>
#                     <td>{emp.experience}</td>
#                     <td>{emp.competency}</td>
#                 </tr>
#                 """
#         data += """
#                 </tbody>
#             </table>
#             """
#     main_credentials = Credentials("chnarsimha986@outlook.com", "Narsimha123@#$")
#     main_account = Account("chnarsimha986@outlook.com", credentials=main_credentials, autodiscover=True,
#                            access_type=DELEGATE)
#     inbox = main_account.inbox
#     emails = inbox.filter(subject__icontains=subject1)
#     for email in emails:
#         pass
#     reply_text = reply_text1
#     reply_account = reply_email1
#     print("reply_account******************",reply_account)
#     print(type(reply_account))
#     participants = list(set(myListItems))
#     print("participants***********************",participants)
#     print(type(participants))
#     if reply_account in participants:
#         participants.remove(reply_account)
#     print("Updated participants______",participants)
#     email_data_body = f"\n\n{data}"
#     parting = participants
#     reply = Message(
#         account=main_account,
#         folder=main_account.inbox,
#         subject=f"Re: {email.subject}",
#         body=HTMLBody(email_data_body),
#         to_recipients=[reply_account],
#         cc_recipients=participants,
#         references=email.message_id,
#         in_reply_to=email.message_id,
#     )
#     if attachment and attachment.filename:
#         attachment_data = attachment.file.read()
#         attachment_obj = FileAttachment(name=attachment.filename, content=attachment_data)
#         reply.attach(attachment_obj)
#     reply.send()
#     print("Replied to:", email.subject)
#     # return {'msg':'mail send successfully ! '}
#     return RedirectResponse(url="http://127.0.0.1:8000", status_code=303)

 


@app.get("/emp", response_class=HTMLResponse)
async def employpost(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("employee_post.html", {"request": request})

@app.post('/employpost')
def emp(request: Request, emp_id: int = Form(default=None), associate_name: str = Form(), department: str = Form(), reporting_manager: str = Form(),
        digital_lead: str = Form(), tech_stack: str = Form(), experience: int = Form(default=None), competency: str = Form(), db: Session = Depends(get_db)):
    employee_record = employeedata(
        emp_id=emp_id,
        associate_name=associate_name,
        department=department,
        reporting_manager=reporting_manager,
        digital_lead=digital_lead,
        tech_stack=tech_stack,
        experience=experience,
        competency=competency)
    db.add(employee_record)
    db.commit()
    db.refresh(employee_record)
    message = {'msg':"Employee '{associate_name}' created successfully"}
    # return RedirectResponse(url="http://127.0.0.1:8000")
    return templates.TemplateResponse("employee_post.html", {"request": request, **message})

@app.get('/emp_data/{subject}')
def employee_details(subject:str,request: Request,db: Session = Depends(get_db)):
    employees = db.query(employeedata).all()
    sub = subject
    return templates.TemplateResponse("emp_data.html",{"request": request,"data":employees, "subb":sub})







@app.get("/")
def generate_pie_graph(request: Request, db: Session = Depends(get_db), client_id: int = None):
    requisitions = db.query(Client_Requisition).filter(Client_Requisition.delete_status == "activate").all()
    client_data = defaultdict(lambda: {"count": 0, "name": ""})
    for requisition in requisitions:
        client_data[requisition.client_id]["count"] += 1
    client_ids = [client_id for client_id, data in client_data.items()]
    clients = db.query(Client).filter(Client.id.in_(client_ids)).all()
    for client in clients:
        client_data[client.id]["name"] = client.name
    pie_data = [{"client_name": data["name"], "client_count": data["count"], "client_id": client_id} for client_id, data
                in client_data.items()]
    pie_data_json = json.dumps(pie_data)
    # Check if client_id is provided and fetch the monthly data
    if client_id is not None:
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        requisitions = db.query(Client_Requisition).filter(
            Client_Requisition.client_id == client_id,
            Client_Requisition.delete_status == "activate"
        ).all()
        month_counts = defaultdict(int)
        for requisition in requisitions:
            requisition_date = requisition.date
            month_name = requisition_date.strftime("%B %Y")
            month_counts[month_name] += 1
        sorted_month_counts = dict(sorted(month_counts.items(), key=lambda x: datetime.strptime(x[0], "%B %Y")))
        pie_data_month = [{"month": month, "count": count} for month, count in sorted_month_counts.items()]
        pie_data_json_month = json.dumps(pie_data_month)
    else:
        pie_data_json_month = "[]"



    client_data1 = defaultdict(
        lambda: {"count": 0, "name": "", "profile_shared_count": 0, "accepted_count": 0, "rejected_count": 0})
    for req in requisitions:
        client_id = req.client_id
        client_data1[client_id]["count"] += 1
        client_data1[client_id]["profile_shared_count"] += req.profile_shared_count
        client_data1[client_id]["accepted_count"] += req.accepted_count
        client_data1[client_id]["rejected_count"] += req.rejected_count
    client_ids1 = [client_id for client_id, data in client_data1.items()]
    clients1 = db.query(Client).filter(Client.id.in_(client_ids1)).all()
    for cli in clients1:
        client_id = cli.id
        client_data1[client_id]["name"] = cli.name
    pie_data1 = [
        {
            "client_name": data["name"],
            "profile_shared_count": data["profile_shared_count"],
            "accepted_count": data["accepted_count"],
            "rejected_count": data["rejected_count"],
            "client_id": client_id
        }
        for client_id, data in client_data1.items()
    ]
    pie_data_json1 = json.dumps(pie_data1)


    tech_data_all_months = defaultdict(lambda: defaultdict(int))
    for requisition in requisitions:
        requisition_month = requisition.date.strftime("%B %Y")
        for tech_stack in requisition.tech_stack_str.split(','):
            tech_data_all_months[requisition_month][tech_stack.strip()] += 1
    tech_data = {
        "months": sorted(set(tech_data_all_months.keys()), key=lambda x: datetime.strptime(x, "%B %Y")),
        "data": {}
    }
    for month, stack_counts in tech_data_all_months.items():
        for tech_stack, count in stack_counts.items():
            if tech_stack not in tech_data["data"]:
                tech_data["data"][tech_stack] = []
            tech_data["data"][tech_stack].append({"month": month, "count": count})
    for techStack, data in tech_data["data"].items():
        for item in data:
            if "count" not in item:
                item["count"] = 0

    

    total_profile_shared_count = sum(requisition.profile_shared_count for requisition in requisitions)
    total_accepted_count = sum(requisition.accepted_count for requisition in requisitions)
    total_rejected_count = sum(requisition.rejected_count for requisition in requisitions)
    
    # Calculate the total count
    total_count = total_accepted_count + total_rejected_count
    
    pie_data = {
        "Profile Shared": total_profile_shared_count,
        "Accepted": total_accepted_count,
        "Rejected": total_rejected_count,
        "Inprogress": total_count,
    }

    return templates.TemplateResponse(
        "pie_chart.html",
        {"request": request, "pie_data_json": pie_data_json, "pie_data_json_month": pie_data_json_month, "pie_data_json1": pie_data_json1, "tech_data": tech_data, "pie_data":pie_data}
    )












@app.get("/pie_tech/{selected_month}")
def generate_pie_tech_chart(selected_month: str, request: Request, db: Session = Depends(get_db)):
    requisitions = db.query(Client_Requisition).filter(
        Client_Requisition.delete_status == "activate"
    ).all()
    tech_count = defaultdict(int)
    for requisition in requisitions:
        requisition_month = requisition.date.strftime("%B %Y")
        if requisition_month == selected_month:
            tech_count[requisition.tech_stack_str] += 1
    tech_data = [{"tech_stack": tech, "count": count} for tech, count in tech_count.items()]
    tech_data_json = json.dumps(tech_data)
    return templates.TemplateResponse(
        "pie_tech.html",
        {"request": request, "tech_data_json": tech_data_json, "selected_month": selected_month}
    )

@app.get("/tech_data_all_months", response_model=dict)
async def get_tech_data_all_months(request: Request, db: Session = Depends(get_db)):
    requisitions = db.query(Client_Requisition).filter(Client_Requisition.delete_status == "activate").all()
    tech_data_all_months = defaultdict(lambda: defaultdict(int))
    for requisition in requisitions:
        requisition_month = requisition.date.strftime("%B %Y")
        for tech_stack in requisition.tech_stack_str.split(','):
            tech_data_all_months[requisition_month][tech_stack.strip()] += 1
    tech_data = {
        "months": sorted(set(tech_data_all_months.keys()), key=lambda x: datetime.strptime(x, "%B %Y")),
        "data": {}
    }
    for month, stack_counts in tech_data_all_months.items():
        for tech_stack, count in stack_counts.items():
            if tech_stack not in tech_data["data"]:
                tech_data["data"][tech_stack] = []
            tech_data["data"][tech_stack].append({"month": month, "count": count})
    for techStack, data in tech_data["data"].items():
        for item in data:
            if "count" not in item:
                item["count"] = 0
    return templates.TemplateResponse("tech_data_all.html", {"request": request, "tech_data": tech_data})






@app.get("/return", response_class=HTMLResponse)
async def get_pie_data(request: Request, db: Session = Depends(get_db)):
    requisitions = db.query(Client_Requisition).filter(
        Client_Requisition.delete_status == "activate"
    ).all()
    total_profile_shared_count = sum(requisition.profile_shared_count for requisition in requisitions)
    total_accepted_count = sum(requisition.accepted_count for requisition in requisitions)
    total_rejected_count = sum(requisition.rejected_count for requisition in requisitions)
    
    # Calculate the total count
    total_count = total_accepted_count + total_rejected_count
    
    pie_data = {
        "Profile Shared": total_profile_shared_count,
        "Accepted": total_accepted_count,
        "Rejected": total_rejected_count,
        "Inprogress": total_count,
    }
    
    # Render the HTML template with the pie chart data
    return templates.TemplateResponse("accept.html", {"request": request, "pie_data": pie_data})









         

@app.get("/data_filter")
def data_filter_all(type: str = Query(..., description="Type filter (shared/selected/rejected/all)"), db: Session = Depends(get_db)):
    requisitions = db.query(Client_Requisition).filter(
        Client_Requisition.delete_status == "activate"
    ).all()

    response_data = {}  

    if type == "shared":
        client_info = {}   
        for req in requisitions:
            client_id = req.client_id
            if client_id not in client_info:
                client_info[client_id] = {
                    "name": None,  
                    "shared_count": 0   
                }

            client_info[client_id]["shared_count"] += req.profile_shared_count

        for client_id, info in client_info.items():
            client = db.query(Client).filter(Client.id == client_id).first()
            if client:
                info["name"] = client.name

        client_shared_counts = {
            info["name"]: info["shared_count"]
            for client_id, info in client_info.items()
            if info["name"]
        }

        response_data = {
            "shared_count": sum(info["shared_count"] for info in client_info.values()),
            "clients": client_shared_counts   
        }

    elif type == "selected":
        selected_count = {}   
        for req in requisitions:
            client_id = req.client_id
            if client_id not in selected_count:
                selected_count[client_id] = {
                    "name": None,  
                    "selected_count": 0   
                }
            
            selected_count[client_id]["selected_count"] += req.accepted_count
        
        for client_id, info in selected_count.items():
            client = db.query(Client).filter(Client.id == client_id).first()
            if client:
                info["name"] = client.name

        client_selected_counts = {
            info["name"]: info["selected_count"]
            for client_id, info in selected_count.items()
            if info["name"]
        }

        response_data = {
            "selected_count": sum(info["selected_count"] for info in selected_count.values()),
            "clients": client_selected_counts
        }

    elif type == "rejected":
        rejected_count = {}   
        for req in requisitions:
            client_id = req.client_id
            if client_id not in rejected_count:
                rejected_count[client_id] = {
                    "name": None,  
                    "rejected_count": 0   
                }
            
            rejected_count[client_id]["rejected_count"] += req.rejected_count
        
        for client_id, info in rejected_count.items():
            client = db.query(Client).filter(Client.id == client_id).first()
            if client:
                info["name"] = client.name

        client_rejected_counts = {
            info["name"]: info["rejected_count"]
            for client_id, info in rejected_count.items()
            if info["name"]
        }

        response_data = {
            "rejected_count": sum(info["rejected_count"] for info in rejected_count.values()),
            "clients": client_rejected_counts
        }

    elif type == "all":
        client_info = {}   
        for req in requisitions:
            client_id = req.client_id
            if client_id not in client_info:
                client_info[client_id] = {
                    "name": None,
                    "shared_count": 0,
                    "rejected_count": 0,
                    "accepted_count": 0
                }

            client_info[client_id]["shared_count"] += req.profile_shared_count
            client_info[client_id]["rejected_count"] += req.rejected_count
            client_info[client_id]["accepted_count"] += req.accepted_count
        
        for client_id, info in client_info.items():
            client = db.query(Client).filter(Client.id == client_id).first()
            if client:
                info["name"] = client.name

        clients_data = {}
        for client_id, info in client_info.items():
            if info["name"]:
                clients_data[info["name"]] = {
                    "shared_count": info["shared_count"],
                    "rejected_count": info["rejected_count"],
                    "accepted_count": info["accepted_count"]
                }

        response_data = clients_data
    else:
        response_data = {"error": "Invalid type specified"}

    return response_data

         

