# Scalable Backend Service Design (50k bikes and 500k users)
## architecture diagram
```
[Mobile App]
    |
 [API Gateway + Auth]
    |
    +--> [Ride Service] -----> [Redis: active ride + idempotency keys]
    |         |                        |
    |         +--> [Postgres (OLTP): rides, users, bikes, ride_events]
    |         +--> [Kafka/PubSub: RideStarted/RideEnded]
    |
    +--> [Pricing Service] -----> [Redis cache for fare quotes / recent rides]
    |  
    +--> [Lock Command Service] ---> [IoT Broker (MQTT/WebSocket)]
                    |                         |
                    +--> [Command Outbox]     +--> [Smart Locks]
                    +<-- [Ack/Telemetry Ingest]
                               |
                         [Device State Service]
                               |
                        [Timeseries/Telemetry DB]
```
## Component Boundaries

- **Ride Service**
Manages lifecycle, concurrency (unique active ride per user/bike), and state transitions.
- **Pricing Service**
Logic for fare calculation (HKD, 15m grace, 5m blocks, daily cap).
- **Lock Command Service**
Executes IoT commands with retries and tracking (ACK/Timeout).
- **Device State Service**
Tracks locks, battery, location, and connectivity telemetry.
- **Event Backbone**
Kafka/PubSub for asynchronous downstream processing (billing, analytics).

## Data Flow

- **Start**
App sends POST /ride/start + Idempotency Key. Ride Service validates constraints via DB unique indexes, creates record, and triggers Lock Service.
- **End**
App calls POST /ride/end. Ride Service triggers Lock Service. Upon ACK, Pricing Service calculates final fare and emits RidePriced.

## Failure Scenarios

- **Retries**
Idempotency keys + partial unique indexes prevent duplicate rides during network timeouts.
- **Pricing Outage**
Ride closes immediately, pricing task is enqueued for eventual finalization, ensuring user experience isn't blocked.

