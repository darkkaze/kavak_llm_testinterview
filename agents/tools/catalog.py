from sqlalchemy.orm import Session
from sqlalchemy import text
from db.connection import SessionLocal
from db.models import Car
from thefuzz import process, fuzz

class CatalogTool:
    def __init__(self):
        self.db = SessionLocal()
        # Cache unique makes and models for fuzzy matching
        self.makes = [r[0] for r in self.db.query(Car.make).distinct().all()]
        self.models = [r[0] for r in self.db.query(Car.model).distinct().all()]

    def search_cars(self, make: str = None, model: str = None, min_price: float = None, max_price: float = None, limit: int = 5):
        """
        Searches for cars with optional filters.
        Handles fuzzy matching for Make and Model.
        """
        query = self.db.query(Car)

        # Fuzzy Match Make
        if make:
            best_make, score = process.extractOne(make, self.makes, scorer=fuzz.token_sort_ratio)
            if score > 70:
                query = query.filter(Car.make == best_make)
            else:
                print(f"Warning: Make '{make}' not found (best: {best_make}, score: {score})")

        # Fuzzy Match Model
        if model:
            # If make is known, filter models by that make first for better accuracy
            candidate_models = self.models
            if make:
                 # Optimization: In a real app, query models for the specific make
                 pass 
            
            best_model, score = process.extractOne(model, candidate_models, scorer=fuzz.token_sort_ratio)
            if score > 70:
                query = query.filter(Car.model == best_model)
            else:
                print(f"Warning: Model '{model}' not found (best: {best_model}, score: {score})")

        # Price Range
        if min_price:
            query = query.filter(Car.price >= min_price)
        if max_price:
            query = query.filter(Car.price <= max_price)

        return query.limit(limit).all()

    def get_price_range_suggestions(self, target_price: float, tolerance: float = 0.15):
        """Finds cars within +/- tolerance of target price."""
        min_p = target_price * (1 - tolerance)
        max_p = target_price * (1 + tolerance)
        return self.search_cars(min_price=min_p, max_price=max_p)

    def close(self):
        self.db.close()
