#Steps to run the application
# Features Available
    - API Versioning
    - Token Authentication (PyJWT)
    - Proper Logging (Request, Response and Timestamp)
    - Documnetation (Swagger)
    - No hardcoding values (used Config file)
    - Testcases using pytest

### Create virtual environment
    pip install virtualwrapper-win
                    or
    python3 -m venv <virtualenv path and venv name>
                    or
    sudo apt-get install virtualenv
    virtualenv <name>
            or
    mkvirtualenv <name>


### Install packages
    pip3 install -r requirements.txt
    
### database tables creation and updation

Initiate a migration folder using init command for alembic to perform the migrations.

    alembic init alembic
Create a migration script from the detected changes in the model using the migrate command. This doesn’t affect the database yet
    
    alembic revision --autogenerate -m "Initial migration"
Apply the migration script to the database by using the upgrade command

    alembic upgrade head

**Each time the database model changes, repeat the migrate and upgrade commands**


### The development server
default port of development server is 8000
    
    uvicorn main:app --reload

If you want to change the port then use following command

    uvicorn main:app --reload --host 0.0.0.0 --port <portnumber>


### Run all test cases
    pytest <test filename>


### Open docs in browser using link
    http://127.0.0.1:8000/docs

# Docker process
  # Docker running command
    Create docker-compose.yml file

    For building the containers run the below command
      ---> docker-compose up --build