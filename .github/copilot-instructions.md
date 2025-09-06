# Project Overview

This project is named infinity-grid and is a Python-based trading bot allowing
to run one of many tradings strategies on an exchange of a choice. The trading
bot is designed to run in a containerized environment.

## Folder Structure

- `./github`: Contains GitHub Actions specific files as well as repository
  configuration.
- `./doc`: Contains documentation for the project, including how to set it up,
  develop with, and concepts to extend the project.
- `./src`: Contains the source code for the trading bot.
- `./tests`: Contains the unit, integration, acceptance, etc tests for this
  project.

## Libraries and Frameworks

- Docker and Docker Compose is used for running the trading bot
- The project uses interfaces, adapters, and models to realize an extensible
  framework for allowing to extend and add new strategies and exchanges to the
  project.

## Coding Standards

- Use black for formatting Python code.
- Pre-commit hooks must pass before committing
