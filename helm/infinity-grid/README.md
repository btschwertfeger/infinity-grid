# Infinity Grid Helm Chart

A Helm chart for deploying the Infinity Grid Trading Bot on Kubernetes.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.2.0+
- **External PostgreSQL database** (required)

## Important Notes

⚠️ **SCALING LIMITATION**: The Infinity Grid trading bot **cannot be scaled
horizontally**. It must always run as a single instance (1 replica). Multiple
instances would:

- Conflict with each other's trading decisions
- Place duplicate or conflicting orders
- Cause database consistency issues
- Violate exchange API rate limits

The chart enforces `replicas: 1` and does not support autoscaling.

## Installation

### 1. Prepare your PostgreSQL Database

Before installing the Infinity Grid, you need to have a PostgreSQL database
ready. The database should:

- Be accessible from your Kubernetes cluster.
- Have a database created for the infinity-grid application. The DB name must
  match the name when starting the infinity-grid (e.g. via option `--db-name`).
- Have appropriate user credentials with read/write permissions.

### 2. Install the Chart

Create a `values.yaml` file:

```yaml
# Trading configuration
infinityGrid:
  strategy: "GridHODL"
  name: "My Kubernetes Trading Bot"
  exchange: "Kraken"
  baseCurrency: "BTC"
  quoteCurrency: "USD"
  amountPerGrid: 20
  interval: 0.02
  nOpenBuyOrders: 3
  maxInvestment: 1000
  userref: 1756394883 # Change this for each instance!

  # API credentials (required)
  apiPublicKey: "your-api-public-key" # set via --set-string
  apiSecretKey: "your-api-secret-key" # set via --set-string

  # Optional: Telegram notifications
  telegram:
    token: "your-telegram-bot-token" # set via --set-string
    chatId: "your-telegram-chat-id"
    threadId: "your-telegram-thread-id"

# Database configuration (required)
database:
  host: "your-postgres-host.example.com" # "your-cloud-postgres.amazonaws.com"
  port: 5432
  username: "infinity_grid"
  password: "your-secure-password" # set via --set-string
  database: "infinity_grid"
```

Then install:

```bash
git clone https://github.com/btschwertfeger/infinity-grid
cd infinity-grid

# Install with required credentials
helm install infinity-grid helm/infinity-grid \
  --version <chart version> \
  --values values.yaml \
  --set database.password="your-secure-password" \
  --set infinityGrid.apiPublicKey="your-api-public-key" \
  --set infinityGrid.apiSecretKey="your-api-secret-key"
```

## Configuration

### Required Configuration

| Parameter                   | Description             | Default           |
| --------------------------- | ----------------------- | ----------------- |
| `database.host`             | PostgreSQL host address | `""` (required)   |
| `database.port`             | PostgreSQL port         | `5432` (required) |
| `database.username`         | Database username       | `""` (required)   |
| `database.password`         | Database password       | `""` (required)   |
| `database.database`         | Database name           | `""` (required)   |
| `infinityGrid.apiPublicKey` | Exchange API public key | `""` (required)   |
| `infinityGrid.apiSecretKey` | Exchange API secret key | `""` (required)   |

### Infinity Grid Bot Configuration

| Parameter                     | Description                                        | Sample                     |
| ----------------------------- | -------------------------------------------------- | -------------------------- |
| `infinityGrid.strategy`       | Trading strategy (cDCA, GridHODL, GridSell, SWING) | `"GridHODL"`               |
| `infinityGrid.name`           | Bot instance name                                  | `"Kubernetes Trading Bot"` |
| `infinityGrid.exchange`       | Exchange to use                                    | `"Kraken"`                 |
| `infinityGrid.baseCurrency`   | Base currency                                      | `"BTC"`                    |
| `infinityGrid.quoteCurrency`  | Quote currency                                     | `"USD"`                    |
| `infinityGrid.amountPerGrid`  | Amount per grid order                              | `20`                       |
| `infinityGrid.interval`       | Grid interval percentage                           | `0.02`                     |
| `infinityGrid.nOpenBuyOrders` | Number of open buy orders                          | `3`                        |
| `infinityGrid.maxInvestment`  | Maximum investment amount                          | `1000`                     |
| `infinityGrid.userref`        | Unique user reference ID                           | `1756394883`               |

## Security Considerations

1. **Never commit secrets to version control**
2. **Use Kubernetes secrets for sensitive data**
3. **Enable SSL/TLS for database connections**
4. **Restrict network access to your database**
5. **Use strong, unique passwords**
6. **Regularly rotate API keys and passwords**

## Troubleshooting

### View Logs

```bash
# View application logs
kubectl logs deployment/infinity-grid

# Follow logs in real-time
kubectl logs -f deployment/infinity-grid
```

### Check Configuration

```bash
# Check if secrets are properly created
kubectl get secrets
kubectl describe secret infinity-grid-db
kubectl describe secret infinity-grid-secrets

# Check environment variables
kubectl exec deployment/infinity-grid -- env | grep INFINITY_GRID
```

## Uninstalling

```bash
helm uninstall infinity-grid
```

Note: This will not delete your PostgreSQL database or its data.

## Support

- GitHub Issues: https://github.com/btschwertfeger/infinity-grid/issues
- Documentation: https://infinity-grid.readthedocs.io/
