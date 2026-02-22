Диаграмма
```mermaid
flowchart TD
    Buyer("Buyer")
    Seller("Seller")

    subgraph Marketplace_System [Marketplace]
        direction TB

        Frontend("Web Application")
        Api("API")
        Broker("Message Broker")

        UserService("User Service")
        UserDB[("User DB")]

        ProductService("Product Service")
        ProductDB[("Product DB")]

        OrderService("Order Service")
        OrderDB[("Order DB")]

        PaymentService("Payment Service")
        PaymentDB[("Payment DB")]

        RecService("Recomendation Service")
        RecDB[("Recomendation DB")]

        NotifService("Notification Service")
        NotifDB[("Notification DB")]
    end

    Buyer --> Frontend
    Seller --> Frontend
    Frontend --> Api
    Api --> UserService
    Api --> ProductService
    Api --> OrderService
    UserService --> UserDB
    ProductService --> ProductDB
    OrderService --> OrderDB
    PaymentService --> PaymentDB
    RecService --> RecDB
    OrderService --> PaymentService
    OrderService -.-> Broker
    Broker --> NotifService
    Broker --> RecService
    NotifService --> NotifDB
```

Инструкция по запуску сервиса

1. Выполнить в командной строке команду `docker build -t marketplace .`
2. Выполнить после этого команду `docker run -p 8080:8080 marketplace`
3. Проверить, что сервис работает одним из способов
   1. Перейти через браузер на `http://localhost:8080/health`
   2. Выполнить в командной строке `curl http://localhost:8080/health`
