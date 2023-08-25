#######################
Network Class Backend
#######################

.. image:: https://img.shields.io/badge/python-3.11.4-blue
    :alt: Supported python versions
**Network Class Backend** is a backend part of the Student-Labs-2023 project called Network Classroom, written based on the
`FastAPI <https://fastapi.tiangolo.com>`_  web framework in Python 3.11.4.

=========
Preliminary actions before launch
=========

**In order to run the project, you need to run PostgreSQL locally:**

#. Download and install `PostgreSQL <https://www.postgresql.org/download/>`_ versions 14.9
#. When installing, you specify the password and port, remember them
#. Next, you need to run pgAdmin 4 and connect to the server that you will have in the list
#. Next, you need to download backup.sql, according to the following `link <https://disk.yandex.com.am/d/iEIfZrBjmlbWJQ>`_.
#. Next, you need to expand the tab Databases and right-click on the postgres database
#. Next, select Restore and in the window that opens, next to the inscription Filename choose backup.sql
#. Press the button Restore
#. Make sure that you have added the necessary tables for testing
#. You can start launching the project!

=========
How to launch
=========

#. Install the required Python version, namely Python 3.11.4
#. Clone Repository
  .. code-block:: python

      git clone -b develop-after-rebase https://github.com/Student-Labs-2023/network-class-backend
3. Go to the root folder of the project
  .. code-block:: python

      cd network-class-backend
4. Install the necessary dependencies
  .. code-block:: python

      pip install -r requirements.txt
5. Создайте в корне проекта файл .env и поместите туда следующую информацию:
  .. code-block:: python

      DB_HOST=localhost
      DB_PORT=5432 <- Здесь вы указываете порт, который указали при установки PostgreSQL
      DB_NAME=postgres
      DB_USER=postgres
      DB_PASS=postgres <- Здесь вместо postgres вы указываете пароль, который указали при установки PostgreSQL

6. To start the project, use the following command
  .. code-block:: python

       gunicorn src.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind=0.0.0.0:8000

