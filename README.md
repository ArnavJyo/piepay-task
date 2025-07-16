# Flipkart Offers API Assignment

## 1. Setup Instructions

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Install dependencies
```
pip install flask flask_sqlalchemy
```

### Run the server
```
python main.py
```

The server will start at `http://127.0.0.1:5000/`.

### Database
- The app uses SQLite (`offers.db`) and automatically creates the required tables on first run.

### Testing the API
- Use tools like `curl`, Postman, or Python scripts to test the endpoints.
- See below for example requests.

## 2. Assumptions
- The Flipkart offer API response structure is consistent with the provided sample.
- All relevant offers are found in the `offer_banners` key.
- The `summary` field contains all information needed to calculate discounts (e.g., percentage, flat amount, min order value).
- Only the first matching minimum order/transaction value in the summary is checked.
- Offers are uniquely identified by `adjustment_id`.
- Only basic discount types (percentage, flat, min value) are parsed; more complex conditions are not handled.

## 3. Design Choices
- **Framework:** Flask was chosen for its simplicity and suitability for small REST APIs.
- **Database:** SQLite is used for easy local development and zero setup. SQLAlchemy ORM provides flexibility for future migrations.
- **Schema:** The `Offer` model stores all relevant fields as strings (comma-separated for lists) for simplicity. This makes parsing and querying easy for the assignment scope.
- **Parsing:** Discount logic is based on regular expressions to extract percentage, flat, and minimum value conditions from the offer summary.
- **Extensibility:** The code is modular and can be extended to support more complex offer logic or additional fields.

## 4. Scaling the GET /highest-discount Endpoint
- **Current State:** The endpoint queries the SQLite database and parses summaries in Python. This is sufficient for low traffic.
- **To Scale to 1,000 RPS:**
  - **Database:** Move to a production-grade RDBMS (e.g., PostgreSQL, MySQL) with proper indexing on `banks` and `payment_instruments`.
  - **App Server:** Use a WSGI server like Gunicorn with multiple workers/processes.
  - **Caching:** Cache frequently requested results (e.g., with Redis or Memcached) to avoid repeated DB and parsing work.
  - **Horizontal Scaling:** Deploy behind a load balancer with multiple app instances.
  - **Optimize Parsing:** Precompute and store parsed discount rules in the DB to avoid regex parsing on every request.

## 5. Improvements with More Time
- **Robust Parsing:** Implement a more robust parser for offer conditions (e.g., max cashback per period, exclusions, etc.).
- **Validation:** Add more input validation and error handling.
- **Testing:** Add unit and integration tests.
- **API Documentation:** Provide OpenAPI/Swagger docs for easier integration.


---

## Example API Usage

### POST /offer
```sh
curl -X POST http://127.0.0.1:5000/offer \
     -H "Content-Type: application/json" \
     -d @test-offer.json
```

### GET /highest-discount
```sh
curl "http://127.0.0.1:5000/highest-discount?amountToPay=10000&bankName=IDFC&paymentInstrument=CREDIT"
```

### View All Offers (Debug)
```sh
curl http://127.0.0.1:5000/all-offers
```

## Test Cases:
# GET /highest-discount

1. Request: "http://127.0.0.1:5000/highest-discount?amountToPay=10000&bankName=&paymentInstrument=UPI_COLLECT" 
Response:
{
  "highestDiscountAmount": 10
}

2. Request: "http://127.0.0.1:5000/highest-discount?amountToPay=10000&bankName=IDFC&paymentInstrument=UPI_COLLECT"
Response:
{
  "highestDiscountAmount": 0
}

3. Request :"http://127.0.0.1:5000/highest-discount?amountToPay=10000&bankName=IDFC&paymentInstrument=CREDIT"
Response: 
{
  "highestDiscountAmount": 500
}

4. Request :"http://127.0.0.1:5000/highest-discount?amountToPay=10000&bankName=BAJAJFINSERV&paymentInstrument=EMI_OPTIONS"
Response:
{
  "highestDiscountAmount": 0
}
5. Request : "http://127.0.0.1:5000/highest-discount?amountToPay=10000&bankName=&paymentInstrument=EMI_OPTIONS"
   Response
{
  "highestDiscountAmount": 0
}
6.Request :"http://127.0.0.1:5000/highest-discount?amountToPay=1000&bankName=IDFC&paymentInstrument=CREDIT"
Response:
{
  "highestDiscountAmount": 0
}

7. Request : "http://127.0.0.1:5000/highest-discount?amountToPay=100&bankName=&paymentInstrument=UPI_COLLECT"
   Response:            
{
  "highestDiscountAmount": 0
}




