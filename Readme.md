# discount-discount-service
Almost a discount service.

Tasked to implement a service for managing discounts i have constructed something that almost could be said to do that.
I have made some assumptions about supporting systems, such as there being some magical way of notifying customers of their discounts being assigned to users,
and that the system is secured in some fashion. This implementation has no concept of authorization or authentication, it is assumde this has been handled before calls are routed to it (and I sort of ran out of time).

---
Three endpoints exists as follows:
```
/discounts [GET]
Response:
  { "availableDiscounts":
    [
      "id": <int> discount id,
      "name": <str> discount name,
      "brand": <str> discount customer,
      "percentage": <int> discount percentage,
      "available": <int> number of available codes.
     ]
   }

/discount/create [POST]
Request:
  {
      "name": {"type": "string"},
      "percentage": {"type": "integer", "minimum": 0, "maximum": 100},
      "nCodes": {"type": "integer", "minimum": 1}
  }

/dicount/{id}/claim [POST]
Request:
  {
  "username": {"type": "string"},
  }
 Response:
  {
  "registered": {"type" "bool"},
  "code": {"type": "string"}
  ["reason": {"type": "string"}] <-- Only provided on failure to register
  }
  ```
  ## Running
  A docker-compose file is provided, build with:
  ```
  docker-compose build
  ```
  and run with:
  ```
  docker-compose up
  ```
  
  ## Regrets
  I decided early to use an auth framework that did not play nice with asgi falcon and ripped it out about halfway. Given time I'd have liked to have some kind of (pretend) auth.
  I also decided I'd use the new and fancy sqlalchemy with (proper) asyncio support, that turned out to be quite a hurdle.
  I have left the unfinished scaffolding for test, unused and in pristine condition.
