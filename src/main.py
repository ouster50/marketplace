import uuid

from fastapi import FastAPI, Depends, Query, status, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from sqlalchemy.orm import Session

from src.database import get_db, ProductDB
from src.generated import ProductStatus, ProductCreate, ProductUpdate, ProductResponse, PaginatedProductResponse

app = FastAPI(title="Marketplace API")


class APIException(Exception):
    def __init__(self, status_code: int, error_code: str, message: str, details: dict = None):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details


@app.exception_handler(APIException)
def api_exception_handler(request: Request, exc: APIException):
    content = {"error_code": exc.error_code, "message": exc.message}
    if exc.details:
        content["details"] = exc.details
    return JSONResponse(status_code=exc.status_code, content=content)


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = {}
    for error in exc.errors():
        field = ".".join(map(str, error["loc"]))
        if field.startswith("body."):
            field = field[5:]
        details[field] = error["msg"]
        
    return JSONResponse(
        status_code=400,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": "Ошибка валидации входных данных",
            "details": details
        }
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product_in: ProductCreate, db: Session = Depends(get_db)):
    new_id = str(uuid.uuid4())
    dump = product_in.model_dump(exclude_unset=True)
    if 'status' in dump and dump['status'] is not None:
        dump['status'] = dump['status'].value
    else:
        dump['status'] = 'ACTIVE'
    db_product = ProductDB(id=new_id, **dump)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@app.get("/products/{id}", response_model=ProductResponse)
def get_product(id: str, db: Session = Depends(get_db)):
    product = db.query(ProductDB).filter(ProductDB.id == id).first()
    if not product:
        raise APIException(
            status_code=404, 
            error_code="PRODUCT_NOT_FOUND", 
            message="Товар не найден по ID"
        )
    return product


@app.get("/products", response_model=PaginatedProductResponse)
def get_products(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1),
    status: ProductStatus = Query(None),
    category: str = Query(None, min_length=1, max_length=100),
    db: Session = Depends(get_db)
):
    query = db.query(ProductDB)
    if status is not None:
        query = query.filter(ProductDB.status == status.value)
    if category is not None:
        query = query.filter(ProductDB.category == category)
    total_elements = query.count()
    items = query.offset(page * size).limit(size).all()
    items = [
        ProductResponse.model_validate(item, from_attributes=True) 
        for item in items
    ]
    return PaginatedProductResponse(
        items=items,
        totalElements=total_elements,
        page=page,
        size=size
    )


@app.put("/products/{id}", response_model=ProductResponse)
def update_product(id: str, product_in: ProductUpdate, db: Session = Depends(get_db)):
    product = db.query(ProductDB).filter(ProductDB.id == id).first()
    if not product:
        raise APIException(
            status_code=404, 
            error_code="PRODUCT_NOT_FOUND", 
            message="Товар не найден по ID"
        )
    dump = product_in.model_dump(exclude_unset=True)
    if 'status' in dump and dump['status'] is not None:
        dump['status'] = dump['status'].value
    for key, value in dump.items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


@app.delete("/products/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(id: str, db: Session = Depends(get_db)):
    product = db.query(ProductDB).filter(ProductDB.id == id).first()
    if not product:
        raise APIException(
            status_code=404, 
            error_code="PRODUCT_NOT_FOUND", 
            message="Товар не найден по ID"
        )
    product.status = "ARCHIVED"
    db.commit()
    return None
