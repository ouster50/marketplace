import uuid
from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from src.database import get_db, ProductDB

from src.generated import ProductStatus, ProductCreate, ProductUpdate, ProductResponse, PaginatedProductResponse

app = FastAPI(title="Marketplace API")


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
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.get("/products", response_model=PaginatedProductResponse)
def get_products(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1),
    status: ProductStatus = Query(None),
    category: str = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(ProductDB)
    if status is not None:
        query = query.filter(ProductDB.status == status.value)
    if category is not None:
        query = query.filter(ProductDB.category == category)
    total_elements = query.count()
    items = query.offset(page * size).limit(size).all()
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
        raise HTTPException(status_code=404, detail="Product not found")
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
        raise HTTPException(status_code=404, detail="Product not found")
    product.status = "ARCHIVED"
    db.commit()
    return None
