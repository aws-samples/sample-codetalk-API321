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

### Demo 4: Nested Cross-Account Execution (`4-nested-xa/`)

**Purpose**: Demonstrates cross-account Step Functions execution with nested workflows for review analysis.

**Architecture Components**:
- **Account A**: Parent state machine that initiates cross-account execution
- **Account B**: Child state machine that processes review data using Amazon Bedrock
- **Cross-Account IAM**: Role-based access with external ID validation
- **AI Integration**: Amazon Nova Micro model for review classification

**Workflow**:
1. **Parent State Machine (Account A)**: Starts synchronous execution of child state machine in Account B
2. **Child State Machine (Account B)**:
   - **InvokeBedrockAPI**: Analyzes review text using Amazon Nova Micro model
   - **ClassifyReview**: Routes based on "fake" or "real" classification
   - **PublishToEventBridge**: Sends fake review alerts to EventBridge
   - **CallHTTPEndpoint**: Makes HTTP call for real reviews with retry logic

**Key Features**:
- Cross-account execution with secure role assumption
- AI-powered review classification
- Conditional routing based on AI analysis
- EventBridge integration for alerting
- HTTP endpoint integration with retry patterns

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

### Demo 4: Nested Cross-Account Execution

```bash
cd 4-nested-xa/

# Deploy to Account B first
sam deploy -t account-b.yaml --guided

# Deploy to Account A (requires Account B state machine ARN)
sam deploy -t account-a.yaml --guided
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

### Demo 4: Cross-Account Review Analysis Execution

```bash
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:REGION:ACCOUNT-A:stateMachine:demo4-parent-statemachine \
  --input '{"asin": "232423","helpful": [0,0],"overall": 5,"reviewText": "I enjoy vintage books and movies so I enjoyed reading this book. The plot was unusual. Don't think killing someone in self-defense but leaving the scene and the body without notifying the police or hitting someone in the jaw to knock them out would wash today. Still it was a good read for me.","reviewTime": "05 5, 2014","reviewerID": "A1F6404F1VG29J","reviewerName": "Avidreader", "summary": "Nice vintage story","unixReviewTime": 1399248000}'
```



**Expected Behavior**:
- Parent state machine in Account A calls child state machine in Account B
- Bedrock analyzes review text and classifies as fake or real
- Fake reviews trigger EventBridge notifications
- Real reviews make HTTP endpoint calls
- Cross-account execution completes synchronously


## Cleanup

To avoid ongoing charges, delete the CloudFormation stacks:

```bash
# Delete Demo 1
sam delete --stack-name sam-app

# Delete Demo 3  
sam delete --stack-name sam-app

# Delete Demo 4
sam delete --stack-name sam-app  # Account A
sam delete --stack-name sam-app  # Account B
```

**Note**: Manually delete S3 buckets if they contain data, as CloudFormation cannot delete non-empty buckets.