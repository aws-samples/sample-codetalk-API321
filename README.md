# AWS Step Functions Demo Project

This repository contains AWS Step Functions demonstrations showcasing distributed map processing and state transition throttling patterns.

## Architecture Overview

### Demo 1: Distributed Map Wind Analysis (`1-dmap-wind-analysis/`)

**Purpose**: Analyzes NOAA weather data to find weather stations with highest average wind speeds by month using distributed map processing.

**Architecture Components**:
- **Data Source**: [NOAA Global Summary of the Day](https://registry.opendata.aws/noaa-gsod/) (GSOD) public dataset
- **Processing Pipeline**: 
  - S3 data copying from public NOAA bucket
  - Distributed map processing with Lambda functions
  - Results aggregation and storage
- **Storage**: S3 buckets for raw data and results, DynamoDB for final aggregated data

**Workflow**:
1. `CopyNOAAS3DataStateMachine` - Copies NOAA data from public bucket to private S3 bucket
2. `NOAAWindSpeedStateMachine` - Processes data using distributed map:
   - **ItemReader**: Lists objects from S3 bucket
   - **ItemProcessor**: Lambda function analyzes wind speed data per file
   - **ResultWriter**: Stores intermediate results in S3
   - **Reducer**: Aggregates results and writes to DynamoDB/S3

**Key Features**:
- Distributed processing with up to 3000 concurrent executions
- 5% tolerated failure rate
- Batch processing (500 items per batch)
- Express execution mode for performance

### Demo 3: State Transition Throttles (`3-state-transition-throttles/`)

**Purpose**: Demonstrates state transition throttling behavior through parallel loop execution.

**Architecture Components**:
- **State Machine**: Creates multiple parallel branches with loop behavior
- **Throttling Pattern**: Each branch executes identical loop logic to generate high state transition volume

**Workflow**:
- 5 parallel branches each executing a countdown loop (10 iterations)
- Uses JSONata query language for conditional logic
- Designed to trigger state transition throttling limits

## Prerequisites

- AWS CLI configured with appropriate permissions
- AWS SAM CLI installed
- Python 3.13 runtime support
- IAM permissions for Step Functions, Lambda, S3, DynamoDB, and CloudWatch

## Deployment Instructions

### Demo 1: Wind Analysis

```bash
cd 1-dmap-wind-analysis/

# Build the application
sam build

# Deploy with guided configuration
sam deploy --guided

# Or deploy with existing configuration
sam deploy
```


### Demo 3: State Transition Throttles

```bash
cd 3-state-transition-throttles/

# Build and deploy
sam build
sam deploy --guided
```

## Execution Instructions

### Demo 1: Wind Analysis Execution

1. **Copy NOAA Data** (First-time setup):
   ```bash
   aws stepfunctions start-execution \
     --state-machine-arn arn:aws:states:REGION:ACCOUNT:stateMachine:CopyNOAAS3DataStateMachine \
     --input '{}'
   ```

2. **Run Wind Speed Analysis**:
   ```bash
   aws stepfunctions start-execution \
     --state-machine-arn arn:aws:states:REGION:ACCOUNT:stateMachine:demo1-windspeed-statemachine \
     --input '{}'
   ```

3. **Monitor Execution**:
   - Check CloudWatch Logs for detailed execution logs
   - View results in DynamoDB table (output from deployment)
   - Check S3 results bucket for intermediate and final results

4. **Cleanup Data** (Optional):
   ```bash
   aws stepfunctions start-execution \
     --state-machine-arn arn:aws:states:REGION:ACCOUNT:stateMachine:DeleteNOAADataStateMachine \
     --input '{"Bucket": "YOUR_NOAA_BUCKET_NAME"}'
   ```

### Demo 3: State Transition Throttles Execution

```bash
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:REGION:ACCOUNT:stateMachine:demo3-state-transitions \
  --input '{}'
```

**Expected Behavior**: 
- Multiple parallel executions create high state transition volume
- Monitor CloudWatch metrics for throttling events
- Execution may experience delays due to throttling limits


## Cleanup

To avoid ongoing charges, delete the CloudFormation stacks:

```bash
# Delete Demo 1
sam delete --stack-name sam-app

# Delete Demo 3  
sam delete --stack-name sam-app
```

**Note**: Manually delete S3 buckets if they contain data, as CloudFormation cannot delete non-empty buckets.