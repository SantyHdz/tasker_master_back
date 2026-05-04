# N8N Workflow Configuration Guide

## Overview
This guide explains how to configure the "Task Reminder" workflow in n8n to work with the Tasker Master API.

## Problems with Original Workflow

The original workflow had several critical issues:

1. **Direct Database Access**: Accessed PostgreSQL directly instead of using the API
2. **Timezone Issues**: JavaScript date comparisons didn't handle UTC correctly
3. **Obsolete Field**: Referenced `notified` field that no longer exists
4. **Strict Time Logic**: No time windows, causing missed notifications
5. **Incorrect Structure**: IF nodes were chained instead of parallel
6. **No Error Handling**: Failed requests could cause duplicate notifications

## Corrected Workflow Architecture

The corrected workflow uses the API endpoints and follows a proper structure:

```
Schedule Trigger (5 min)
    ↓
Get Pending Tasks (API call)
    ↓
    ├─→ Check 24h → Set Tasks → Split Batches → Send Telegram → Mark Sent
    ├─→ Check 1h  → Set Tasks → Split Batches → Send Telegram → Mark Sent
    └─→ Check 10m → Set Tasks → Split Batches → Send Telegram → Mark Sent
```

## New API Endpoints for N8N

### 1. Get Pending Notifications
**Endpoint:** `GET /tasks/notifications/pending`

Returns tasks that need notifications based on their due dates:

```json
{
  "24h": [
    {
      "id": "uuid",
      "title": "Task title",
      "description": "Task description",
      "priority_id": 1,
      "due_date": "2026-05-05T15:00:00Z",
      "is_completed": false,
      "created_at": "2026-05-04T15:00:00Z",
      "notified_24h": false,
      "notified_1h": false,
      "notified_10m": false
    }
  ],
  "1h": [],
  "10m": [],
  "current_time": "2026-05-04T14:00:00Z"
}
```

**Time Windows:**
- **24h**: Tasks due in 23-25 hours
- **1h**: Tasks due in 55-65 minutes
- **10m**: Tasks due in 8-12 minutes

### 2. Mark Notification as Sent
**Endpoint:** `PATCH /tasks/{task_id}/notifications/{notification_type}`

Marks a notification as sent for a specific task.

**Parameters:**
- `task_id`: UUID of the task
- `notification_type`: One of "24h", "1h", "10m"

**Response:**
```json
{
  "message": "Notification 24h marked as sent",
  "task": {
    "id": "uuid",
    "title": "Task title",
    "notified_24h": true,
    "notified_1h": false,
    "notified_10m": false,
    ...
  }
}
```

## N8N Workflow Setup

### Step 1: Schedule Trigger
- **Node Type:** Schedule Trigger
- **Interval:** Every 5 minutes
- **Cron Expression:** `*/5 * * * *`

### Step 2: HTTP Request - Get Pending Tasks
- **Node Type:** HTTP Request
- **Method:** GET
- **URL:** `{{API_BASE_URL}}/tasks/notifications/pending`
- **Authentication:** None (or add if you secure the endpoint)
- **Response Format:** JSON

### Step 3: Process Each Notification Type
Create three parallel branches for each notification type:

#### Branch 1: 24h Notifications
- **Node Type:** IF
- **Condition:** Length of `$json.24h` > 0

**Then:**
- **Node Type:** Split In Batches
- **Node Type:** Loop Over Items (for each task in 24h array)
- **Node Type:** HTTP Request (Send notification)
  - **Method:** POST
  - **URL:** Your notification service (email, SMS, etc.)
  - **Body:** Task details
- **Node Type:** HTTP Request (Mark as sent)
  - **Method:** PATCH
  - **URL:** `{{API_BASE_URL}}/tasks/{{$json.id}}/notifications/24h`

#### Branch 2: 1h Notifications
- Same structure as Branch 1, but use `$json.1h` array and notification type "1h"

#### Branch 3: 10m Notifications
- Same structure as Branch 1, but use `$json.10m` array and notification type "10m"

### Step 4: Error Handling
- **Node Type:** Error Trigger
- **Node Type:** Send Email (or log error)
- **Node Type:** Stop Workflow

## Environment Variables

Set these in your n8n environment or workflow credentials:

```
API_BASE_URL=http://your-api-domain.com
```

## Authentication Setup

The corrected workflow uses HTTP Header Auth for API calls:

1. **Create API Credentials** in n8n:
   - Go to Credentials → New Credential
   - Select "Header Auth"
   - Name: "API Auth"
   - Header Name: "Authorization"
   - Header Value: "Bearer YOUR_API_TOKEN" (if using JWT)
   - Or use a custom header for API key authentication

2. **Update Workflow Credentials**:
   - Replace "your-http-header-auth-id" with your actual credential ID
   - The workflow uses this for all API calls

## Importing the Corrected Workflow

1. **Copy the corrected workflow JSON** from `N8N_WORKFLOW_CORRECTED.json`
2. **Import in n8n**:
   - Go to Workflows → Import from File/URL
   - Paste the JSON or upload the file
   - Click "Import"

3. **Configure credentials**:
   - Update the Telegram API credential ID (already set to your existing one)
   - Update the HTTP Header Auth credential ID
   - Set the `API_BASE_URL` environment variable

## Workflow Node Details

### 1. Schedule Trigger
- **Type**: Schedule Trigger
- **Interval**: Every 5 minutes
- **Purpose**: Triggers the workflow periodically

### 2. Get Pending Tasks
- **Type**: HTTP Request
- **Method**: GET
- **URL**: `{{ $env.API_BASE_URL }}/tasks/notifications/pending`
- **Authentication**: HTTP Header Auth
- **Purpose**: Gets tasks needing notifications from API

### 3. Check Notification Nodes (3 parallel branches)
Each branch checks if there are tasks for a specific time window:

**Check 24h Notifications**:
- **Type**: IF
- **Condition**: `{{ $json['24h'].length }} > 0`
- **Purpose**: Determines if 24h notifications are needed

**Check 1h Notifications**:
- **Type**: IF
- **Condition**: `{{ $json['1h'].length }} > 0`
- **Purpose**: Determines if 1h notifications are needed

**Check 10m Notifications**:
- **Type**: IF
- **Condition**: `{{ $json['10m'].length }} > 0`
- **Purpose**: Determines if 10m notifications are needed

### 4. Set Tasks Nodes
Extract the task arrays for processing:

**Set 24h Tasks**:
- **Type**: Set
- **Assignments**: `tasks_24h = {{ $json['24h'] }}`

**Set 1h Tasks**:
- **Type**: Set
- **Assignments**: `tasks_1h = {{ $json['1h'] }}`

**Set 10m Tasks**:
- **Type**: Set
- **Assignments**: `tasks_10m = {{ $json['10m'] }}`

### 5. Split Batches Nodes
Process tasks one at a time:

**Split 24h Batches**:
- **Type**: Split In Batches
- **Batch Size**: 1

**Split 1h Batches**:
- **Type**: Split In Batches
- **Batch Size**: 1

**Split 10m Batches**:
- **Type**: Split In Batches
- **Batch Size**: 1

### 6. Send Telegram Nodes
Send notifications to Telegram:

**Send Telegram 24h**:
- **Type**: Telegram
- **Chat ID**: 5550201252
- **Message**: 🚨 Tarea próxima a vencer en 24h

**Send Telegram 1h**:
- **Type**: Telegram
- **Chat ID**: 5550201252
- **Message**: ⚠️ Tarea en 1 hora

**Send Telegram 10m**:
- **Type**: Telegram
- **Chat ID**: 5550201252
- **Message**: 🔥 URGENTE - 10 minutos

### 7. Mark Sent Nodes
Mark notifications as sent in the API:

**Mark 24h Sent**:
- **Type**: HTTP Request
- **Method**: PATCH
- **URL**: `{{ $env.API_BASE_URL }}/tasks/{{ $json.id }}/notifications/24h`

**Mark 1h Sent**:
- **Type**: HTTP Request
- **Method**: PATCH
- **URL**: `{{ $env.API_BASE_URL }}/tasks/{{ $json.id }}/notifications/1h`

**Mark 10m Sent**:
- **Type**: HTTP Request
- **Method**: PATCH
- **URL**: `{{ $env.API_BASE_URL }}/tasks/{{ $json.id }}/notifications/10m`

## Timezone Handling

The API now properly handles timezones:
- All `due_date` values must be timezone-aware
- The API returns times in UTC
- N8N should handle timezone conversion for local notifications

## Example N8N Workflow JSON Structure

```json
{
  "name": "Task Reminder",
  "nodes": [
    {
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "minutes",
              "minutesInterval": 5
            }
          ]
        }
      }
    },
    {
      "name": "Get Pending Tasks",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "GET",
        "url": "={{$env.API_BASE_URL}}/tasks/notifications/pending"
      }
    },
    {
      "name": "Check 24h Notifications",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "={{$json.24h.length}}",
              "operation": "larger",
              "value2": "0"
            }
          ]
        }
      }
    }
  ]
}
```

## Testing the Workflow

1. **Create a test task** with a due date in the notification window
2. **Run the workflow manually** to verify it picks up the task
3. **Check the notification flags** are updated correctly
4. **Verify notifications are sent** to the user

## Troubleshooting

### No tasks returned
- Check that tasks have `due_date` set
- Verify `is_completed` is false
- Ensure notification flags are false
- Check timezone of due_date (must be UTC)
- Verify API endpoint is accessible
- Check authentication credentials

### Notifications sent multiple times
- Verify the PATCH request is successful
- Check that notification flags are being updated
- Ensure the workflow completes successfully
- Check for errors in the "Mark Sent" nodes

### Timezone issues
- All dates in API are UTC
- Convert to local timezone in n8n before sending notifications
- Use n8n's timezone functions for display
- The workflow uses `toLocaleString('es-ES', { timeZone: 'UTC' })` for proper display

### Workflow not triggering
- Check the Schedule Trigger is active
- Verify the interval is set correctly (5 minutes)
- Check n8n is running and accessible
- Review workflow execution logs

### API connection errors
- Verify `API_BASE_URL` environment variable is set
- Check authentication credentials are correct
- Ensure API server is running
- Test API endpoints manually first

### Telegram messages not sending
- Verify Telegram API credentials
- Check chat ID is correct (5550201252)
- Ensure Telegram bot has permission to send messages
- Test Telegram node independently

## Comparison: Original vs Corrected Workflow

| Aspect | Original Workflow | Corrected Workflow |
|--------|------------------|-------------------|
| **Data Access** | Direct PostgreSQL | API endpoints |
| **Timezone Handling** | JavaScript Date (incorrect) | UTC-aware API |
| **Time Windows** | Exact times (no windows) | Proper time windows |
| **Structure** | Chained IF nodes | Parallel branches |
| **Error Handling** | None | Built-in error handling |
| **Notification Flags** | Obsolete `notified` field | Correct `notified_24h/1h/10m` |
| **Scalability** | Limited | Better with API |
| **Maintenance** | Harder | Easier with API |

## Security Considerations

### Current Setup
- The corrected workflow uses HTTP Header Auth
- Credentials are stored securely in n8n
- API endpoints can be secured further

### Recommended Enhancements
1. **API Key Authentication**:
   - Create a service account in your API
   - Use API key instead of JWT for n8n
   - Add rate limiting for notification endpoints

2. **IP Whitelisting**:
   - Restrict API access to n8n server IP
   - Add firewall rules for additional security

3. **HTTPS Only**:
   - Ensure API uses HTTPS
   - Validate SSL certificates

4. **Audit Logging**:
   - Log all notification requests
   - Track which tasks were notified
   - Monitor for abuse

## Monitoring

### Key Metrics to Monitor
- **Workflow Execution Time**: Should complete within 30 seconds
- **API Response Time**: Should be under 1 second
- **Notification Success Rate**: Should be > 95%
- **Failed Requests**: Should be < 1%

### Monitoring Setup
1. **n8n Built-in Monitoring**:
   - Enable workflow execution logs
   - Set up error notifications
   - Monitor workflow status

2. **API Monitoring**:
   - Track endpoint response times
   - Monitor error rates
   - Set up alerts for failures

3. **Notification Monitoring**:
   - Track Telegram delivery success
   - Monitor for duplicate notifications
   - Log all sent notifications

## Performance Optimization

### Current Performance
- **Schedule Interval**: 5 minutes
- **Batch Size**: 1 task at a time
- **Parallel Processing**: 3 branches (24h, 1h, 10m)

### Optimization Opportunities
1. **Increase Batch Size**: Process multiple tasks per batch
2. **Dynamic Scheduling**: Adjust interval based on task volume
3. **Caching**: Cache API responses when appropriate
4. **Queue System**: Use message queue for high volume

## Testing the Workflow

### Manual Testing
1. **Create test tasks** with due dates in each notification window
2. **Run workflow manually** to verify it picks up tasks
3. **Check notification flags** are updated correctly
4. **Verify Telegram messages** are received
5. **Test error scenarios** (API down, network issues)

### Automated Testing
1. **Unit Tests**: Test individual nodes
2. **Integration Tests**: Test complete workflow
3. **Load Tests**: Test with many tasks
4. **Failure Tests**: Test error handling

## Maintenance

### Regular Tasks
1. **Monitor workflow execution logs**
2. **Check for failed notifications**
3. **Update credentials as needed**
4. **Review and optimize performance**
5. **Update workflow for API changes**

### Backup and Recovery
1. **Export workflow JSON regularly**
2. **Backup n8n database**
3. **Document any custom changes**
4. **Test recovery procedures**

## Future Enhancements

### Planned Features
1. **Custom Notification Times**: Allow users to set custom notification intervals
2. **Multiple Channels**: Support email, SMS, push notifications
3. **Notification Templates**: Customizable message templates
4. **User Preferences**: Per-user notification settings
5. **Analytics Dashboard**: Track notification effectiveness

### API Enhancements
1. **Webhook Support**: Real-time notifications
2. **Batch Operations**: Process multiple tasks at once
3. **Notification History**: Track all sent notifications
4. **Retry Logic**: Automatic retry for failed notifications