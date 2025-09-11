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
- `./src/infinity_grid/adapters`: Contains exchange and notification adapters
- `./src/infinity_grid/core`: Contains the CLI, bot engine, state machine and
  event bus
- `./src/infinity_grid/infrastructure`: Contains the database table classes
- `./src/infinity_grid/interfaces`: Contains the interfaces for exchanges,
  notification channels, and strategies
- `./src/infinity_grid/models`: Contains schemas, models, and data transfer
  objects
- `./src/infinity_grid/services`: Contains services like Notification service
  and database connectors
- `./src/infinity_grid/strategies`: Contains the implementations of the
  strategies
- `./tests`: Contains the unit, integration, acceptance, etc tests for this
  project.

## Libraries and Frameworks

- Docker and Docker Compose is used for running the trading bot
- The project uses interfaces, adapters, and models to realize an extensible
  framework for allowing to extend and add new strategies and exchanges to the
  project.

## Guidelines

- Best Software Engineering practices like KISS, modularization, and efficiency
  must be followed.
