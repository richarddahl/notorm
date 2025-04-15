# Deployment Strategies

The uno Deployment Pipeline supports multiple deployment strategies to accommodate different requirements and risk profiles. This document describes the available strategies and their implementation details.

## Common Deployment Strategies

### Blue-Green Deployment

Blue-green deployment is a technique that reduces downtime and risk by running two identical production environments, "Blue" and "Green". At any time, only one of the environments is live, serving all production traffic. The other environment is idle.

**Implementation Flow:**

1. **Determine the Current Environment**
   - Identify which environment (blue or green) is currently active
   - The inactive environment will be the target for the new deployment

2. **Deploy to Target Environment**
   - Deploy the new version to the inactive environment
   - This allows the new version to be fully deployed and initialized without affecting live traffic

3. **Run Health Checks**
   - Execute comprehensive health checks on the newly deployed environment
   - Verify that the application is responding correctly and all dependencies are working

4. **Switch Traffic**
   - Redirect traffic from the active environment to the newly deployed environment
   - In Kubernetes, this is typically done by updating a Service selector
   - For other platforms, this might involve load balancer configuration or DNS changes

5. **Verify Deployment**
   - Monitor the new environment to ensure it's handling traffic correctly
   - Check error rates, response times, and other key metrics

6. **Rollback (if needed)**
   - If issues are detected, traffic can be immediately switched back to the previous environment
   - This provides a fast and reliable rollback mechanism with zero downtime

**Usage Example:**

```bash
python -m uno.deployment.scripts.blue_green \
  --app-name my-app \
  --namespace my-namespace \
  --image-tag v1.0.0 \
  --health-check-url http://my-app-{env}.example.com/health
```

**Configuration Options:**

- `health_check_url`: URL for health checks (can include `{env}` placeholder)
- `health_check_timeout`: Timeout for health checks in seconds (default: 60)
- `switch_timeout`: Timeout for switching traffic in seconds (default: 300)

### Rolling Deployment

Rolling deployment updates instances of the application incrementally, typically one at a time or in small batches. This approach allows for continuous availability but can lead to having multiple versions running simultaneously.

**Implementation Flow:**

1. **Get Current Instances**
   - Identify all instances of the application that need to be updated

2. **Calculate Batches**
   - Determine the batch size and number of batches
   - Default is to update one instance at a time, but this can be configured

3. **Deploy to Each Batch**
   - Update each batch sequentially
   - For each batch:
     - Update the instances
     - Run health checks
     - Proceed to the next batch if health checks pass

4. **Verify Deployment**
   - After all batches are updated, verify the overall deployment
   - Check that all instances are running the new version and handling traffic correctly

5. **Rollback (if needed)**
   - If issues are detected during the process, affected batches can be rolled back
   - Depending on the failure point, this might involve partial rollback

**Usage Example:**

```bash
python -m uno.deployment.scripts.deploy \
  --app-name my-app \
  --environment prod \
  --platform kubernetes \
  --config-file ./deployment/config.yaml \
  --strategy rolling
```

**Configuration Options:**

- `batch_size`: Number of instances to update in each batch (default: 1)
- `batch_timeout`: Timeout for each batch in seconds (default: 300)

### Canary Deployment

Canary deployment is a technique to reduce risk by slowly rolling out changes to a small subset of users before making them available to everyone.

**Implementation Flow:**

1. **Deploy Canary**
   - Deploy the new version with minimal traffic (e.g., 10%)
   - This exposes the new version to a small subset of users

2. **Run Health Checks**
   - Execute comprehensive health checks on the canary deployment
   - Monitor error rates, response times, and user metrics

3. **Gradually Increase Traffic**
   - If metrics are acceptable, gradually increase traffic to the canary
   - Typical progression: 10% → 25% → 50% → 75% → 100%
   - Wait and evaluate metrics between each increment

4. **Evaluate Metrics**
   - Before each traffic increase, evaluate key metrics against thresholds
   - Metrics might include error rates, latency, CPU usage, etc.

5. **Finalize Deployment**
   - Once the canary is receiving 100% of traffic, finalize the deployment
   - This might involve cleaning up the old version

6. **Rollback (if needed)**
   - If metrics exceed thresholds at any point, immediately roll back
   - Redirect all traffic back to the previous version

**Usage Example:**

```bash
python -m uno.deployment.scripts.deploy \
  --app-name my-app \
  --environment prod \
  --platform kubernetes \
  --config-file ./deployment/config.yaml \
  --strategy canary
```

**Configuration Options:**

- `initial_percentage`: Initial percentage of traffic to route to the canary (default: 10.0)
- `increments`: List of percentage increments (default: [25.0, 50.0, 75.0, 100.0])
- `increment_interval`: Interval between increments in seconds (default: 300)
- `metrics_threshold`: Thresholds for metrics to evaluate the canary

## Strategy Selection

When choosing a deployment strategy, consider the following factors:

### Blue-Green
- **Best for:** Critical applications where downtime is unacceptable
- **Resource requirements:** High (requires double the resources during deployment)
- **Complexity:** Medium
- **Rollback speed:** Immediate
- **Recommended environments:** Production

### Rolling
- **Best for:** Applications with limited resources or where multiple versions can coexist
- **Resource requirements:** Low to medium (depends on batch size)
- **Complexity:** Low
- **Rollback speed:** Medium (depends on batch size)
- **Recommended environments:** Development, testing, staging

### Canary
- **Best for:** Applications with high risk or high impact changes
- **Resource requirements:** Medium
- **Complexity:** High
- **Rollback speed:** Fast
- **Recommended environments:** Production (especially for user-facing applications)

## Default Strategy by Environment

The deployment pipeline automatically selects a default strategy based on the environment:

- **Production:** Blue-Green or Canary
- **Staging:** Blue-Green
- **Testing:** Rolling
- **Development:** Recreate (simple replacement)

You can override these defaults in the configuration file or command-line parameters.

## Custom Strategies

You can create custom deployment strategies by extending the `DeploymentStrategy` base class:

```python
from uno.deployment.strategies import DeploymentStrategy, DeploymentResult

class MyCustomStrategy(DeploymentStrategy):```

def __init__(self, logger=None, **options):```

super().__init__("my-custom", logger)
self.options = options
```
``````

```
```

def deploy(self, context):```

# Implement your deployment logic here
return DeploymentResult(True, "Deployment succeeded")
```
``````

```
```

def rollback(self, context):```

# Implement your rollback logic here
return DeploymentResult(True, "Rollback succeeded")
```
```
```