# DB Service Kit

<div align="center">
    <img src="readme_resources/README.png" alt="AWS Utils" width="200"/>
</div>

## Overview
Utility modules to use for the DB Service calls. 

## Language
- Python

## Project Structure
```
db-service-kit/
      ├── db_services/   # Main package for DB services
      │     ├── db_modules          # Subpackage for database modules
      │     │     ├── __init__.py   # Initialize the db_modules subpackage
      │     │     └── postgres_db_module.py    # Module for PostgreSQL database interactions
      │     │
      │     ├── helper_utils   # Subpackage for helper utilities
      │     │     ├── __init__.py   # Initialize the helper_utils subpackage
      │     │     ├── utils.py      # General utility functions for DB services
      │     │     └── variables.py  # Module for defining constants and variables used across DB services
      │     │  
      │     └── __init__.py    # Initialize the db_services package
      │
      ├── tests/           # Directory for unit tests
      │     ├── unit_tests/   # Subdirectory for unit tests 
      │     │      ├── test_db_modules/   # Subdirectory for testing database modules
      │     │      │        ├── __init__.py     # Initialize the test_db_modules subpackage
      │     │      │        ├── conftest.py     # Configuration file for pytest fixtures
      │     │      │        └── test_postgres_db_module.py   # Unit tests for PostgreSQL database module
      │     │      │
      │     │      └── __init__.py  # Initialize the unit_tests subpackage
      │     │ 
      │     └── __init__.py   # Initialize the tests package
      │
      ├──readme_resources
      │     └── README.png    # Picture for the Read me file   
      │
      ├── .gitignore    # Git ignore file to exclude unnecessary files from version control
      ├── README.md     # README file for project documentation
      └── requirements.txt  # File to list project dependencies
```

## Benefits:
A standardized, battle-tested wrapper for Postgres designed to bridge the gap between simple database connectivity 
and production-grade persistence layers.
- **Robust & Resilient Operations:** 
    Ensures high reliability with thread-safe execution, automated retry logic for transient failures, and 
    standardized exception handling to manage database errors gracefully.
- **Optimized Performance:** 
    Boosts application speed and reduces database load through efficient connection pooling.
- **Production-Ready Security & Quality:** 
    Follows industry best practices by default, including parameterized queries for SQL injection protection, 
    structured logging for observability, and a comprehensive unit-testing suite.
- **Scalable Modular Architecture:** 
    Features a clean separation of concerns and modular design, allowing developers to focus on core business logic 
    while providing a foundation that is easy to extend, maintain, and reuse across projects.

### Note: 
- The default port is set to 5439 in the code for redshift compatibility (pass the port based on your DB).

## Conclusion:
The DB Service Kit provides a production-ready foundation for database management, combining standardized interfaces 
with built-in resilience and performance optimizations. By abstracting the complexities of connectivity, it empowers 
developers to prioritize core application logic while ensuring long-term maintainability and scalability.
