# notorm

[![PyPI - Version](https://img.shields.io/pypi/v/notorm.svg)](https://pypi.org/project/notorm)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/notorm.svg)](https://pypi.org/project/notorm)

-----

## Table of Contents

- [Installation](#installation)
- [License](#license)
- [Introduction](#introduction)

## Installation

```console
pip install notorm
```

## License

`notorm` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

## Introduction

Why `notorm`

"uno" is already a project at pypi, the actual name of this library is UNO, and UNO is NOT an ORM.

It's meant as an homage to GNU of course.

It also represents the limited nature of the project at its genesis.

It really is more of an app framework at this point, going well beyond its original intent, but the name stuck.

## File Structure

Within UNO, the term "Entity" refers to a type of information that exists within an application.  

Entities are defined by the following:

- UnoModel
- UnoBase
- Generally one or more UnoEndpoint

A deliberate attempt has been made to couple as little as possible within UNO.  

Each of the Entity definition classes isolate the functionality required within and have defined interfaces for interaction with the other functionality.  This was not intentional at the beginning of the project, but this level of isolation soon became necessary for my little brain to keep track of what was being done where.  

`UnoModel` is a subclass of pydantic BaseModel with a number of class variables in addition to the fields associated with the Entities. This is where all of your business logic is processed and the data to be presented to a user or persisted is validated.

`UnoBase` is a subclass of sqlalchemy ORM DeclarativeBase that defines the data structure of the Entities.  This handles all querying and editing of the data.

`UnoEndpoint` is a subclass of pydantic BaseModel that defines FastAPI CRUD routers.  This obviously facilitates user IO.

Each of these classes are built to be completely independent of one another.  In theory at least.  Care has been taking during development to ensure this is the case.  It should be relatively easy to switch out the SQL Alchemy ORM base for a json object used with a NoSQL database or pickle to save the records to the filesystem.  The FastAPI based endpoints could be switched out to use a native application running on a host.  etc...   

The structure of the project:

| uno  
&nbsp;&nbsp;&nbsp;&nbsp;
| api - Code required to use FastAPI to serve an app using UNO  
&nbsp;&nbsp;&nbsp;&nbsp;
    | apps  - The built in modules:  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        | attr - Entities to associate user-defined information to Uno entities  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        | auth - Entities to manage users and access  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        | fltr - Entities support the automatic filtering of the database  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        | meta - Entities to manage relationships between entities  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        | msg - Entities to communicate between users  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        | rprt - Entities to produce reports on entities  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        | val - Entities to associate attributes, filters, messages, and reports to thier respective Entities  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        | wkflw - Entities to track actions that must be executed by based on state changes and real-world events  
&nbsp;&nbsp;&nbsp;&nbsp;
    | db - Defines the UnoBase (persistant data structure) and SQLEmitter (emits custom sql) and the methods to communicate with the database.  
&nbsp;&nbsp;&nbsp;&nbsp;
    | model - Defines UnoModel, the business logic executor  

## Starting the db with Docker

`cd to notorm/docker`
`docker build -t pg16_uno .`
`docker-compose up`
