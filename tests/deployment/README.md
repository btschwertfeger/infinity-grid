# Test Deployments

> ⚠️ Do not use this configuration files for a production setup. Always use
> strong passwords and never expose them publicly!

This subdirectory contains the necessary resources to deploy the infinity-grid
using the provided Helm Chart to Kubernetes for testing purposes during the
CI/CD of the infinity-grid.

- `values.yaml`: Minimal configuration for the infinity-grid application.
- `postgresql-values.yaml`: Minimal configuration for the required PostgreSQL
  instance.

Only the infinity-grid application is deployed during CI/CD, the PostgreSQL
instance is assumed to be existing i.e., must be deployed before CI/CD.
