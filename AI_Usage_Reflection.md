# AI Usage Reflection: Refining and Scaling the Bike Ride Service

## 1. AI tool used

Cursor

## 2. Prompts and Instructions Given

- **Prompt 1**

Please generate a complete, production-ready project with a full file structure and source code according to the following requirements:

(1) Assignment Overview
Build a simple Bike Ride Service API that supports starting a ride, ending a ride, retrieving ride information, and calculating ride cost. Your solution should be clean, runnable, and easy to review. You should use Python (FastAPI preferred) and SQLite.

(2) Required API endpoints
1> Method: “POST” Endpoint: “/ride/start” Purpose: "Create a new ride session"
2> Method: “POST” Endpoint: “/ride/end” Purpose: "End an existing ride session"
3> Method: “GET” Endpoint: “/ride/{id}” Purpose: "Return ride details"
4> Method: “GET” Endpoint: “/ride/{id}/cost” Purpose: "Return calculated fare for the ride"

(3) Pricing Rules
1> Unlock fee: HKD 5 
2> First 15 minutes: free 
3> After 15 minutes: HKD 1 per 5 minutes 
4> Daily cap: HKD 25

(4) Technical Expectations 
1> Organize the project with clear structure and readable naming.
2> Accurate pricing logic, clear component boundaries, reasonable trade-offs, and edge-case awareness.
3> Use SQLite as database.  
4> Include sensible validation and error handling. 
5> Provide a README with setup and run instructions. 
6> Unit tests 
7> Basic idempotency or duplicate request handling 
8> Caching or other performance-aware choices 
9> Simple concurrency handling where relevant

- **Prompt 2**

Please modify the "/ride/start" endpoint: remove the Idempotency-Key from the request headers. Instead, implement a logic check in the code: if a user_id or bike_id already has an ongoing ride (not yet ended), prevent adding a new record to the rides table. Return an appropriate error message, such as "User is already on a ride" or "Bike is currently in use".

- **Prompt 3**

Please modify the "/ride/end" endpoint: remove the Idempotency-Key from the request headers. Instead, implement a logic check in the code: if a ride has ended, prevent duplicate database operations regarding to duplicate requests.

- **Prompt 4**

Since the Idempotency-Key has been removed from the request headers, the idempotency_keys table is no longer needed. Please remove the code that generates this table and delete the idempotency_keys table from the database.

- **Prompt 5**

Considering the need to scale this backend service to 50,000 bikes and 500,000 users, which approach is better for designing the "/ride/start" and "/ride/end" APIs: the initial "Idempotency-Key in headers" solution, or the current "Business Unique Constraints + State Machine Validation" approach?
Please explain the pros and cons of each, and describe how to implement idempotent operations using an Idempotency Key.

- **Prompt 6**

Refactor the code to ensure data integrity and idempotency:
(1) Add a unique constraint in the database to prevent multiple active rides for the same user or bike.
(2) Re-enable the Idempotency-Key as a required field in the headers for the "/ride/start" and "/ride/end" APIs.

## 3. AI Mistakes, Weaknesses, and Blind Spots

- **Weak Validation**

The initial output failed to make the Idempotency-Key a mandatory field in the POST request headers, reducing its effectiveness.

- **Concurrency Blind Spots**

The initially AI-generated code lacked internal logic to prevent a user from starting multiple concurrent rides or multiple users from unlocking the same bike. It relied on the client-side key rather than server-side logic checks.

- **Schema Redundancy**

After removing the Idempotency-Key requirement in intermediate steps, the AI did not automatically suggest cleaning up the idempotency_keys table no longer needed until explicitly prompted.

## 4. Manual Verification, Fixes, and Improvements

- **Data Integrity**

I directed the AI to implement DB Unique Constraints (such as partial unique indexes) to ensure that a bike or user could only be associated with one ride when they have an ongoing ride (not yet ended).

- **Hybrid Idempotency**

I recognized that for high-scale systems, relying on business logic alone is insufficient. I forced the re-enabling of the Idempotency-Key as a mandatory field in the POST request headers to handle duplicate network retries before they hit the database.

- **System Cleanup**

I manually initiated a schema cleanup by instructing the removal of the idempotency_keys table once the strategy shifted, ensuring a lean and relevant database structure.