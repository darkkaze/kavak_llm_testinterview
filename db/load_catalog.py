import csv
from db.connection import SessionLocal, engine, Base
from db.models import Car

def load_csv():
    print("Creando tablas...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Check if data exists
    if db.query(Car).count() > 0:
        print("La base de datos ya tiene datos. Saltando carga.")
        db.close()
        return

    print("Cargando catálogo desde CSV...")
    with open("specs/sample_caso_ai_engineer.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Clean and convert data
            try:
                car = Car(
                    id=int(row["stock_id"]),
                    km=int(row["km"]) if row["km"] else 0,
                    price=float(row["price"]) if row["price"] else 0.0,
                    make=row["make"],
                    model=row["model"],
                    year=int(row["year"]) if row["year"] else 0,
                    version=row["version"],
                    # Add other fields if needed, mapping from CSV columns
                )
                db.add(car)
            except ValueError as e:
                print(f"Error en fila {row.get('stock_id')}: {e}")
    
    db.commit()
    db.close()
    print("Carga de catálogo completada.")

if __name__ == "__main__":
    load_csv()
