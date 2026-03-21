from fastapi import FastAPI, Query


app = FastAPI(title="Petstore API", version="1.0.0")

PETS = {
    1: {
        "id": 1,
        "name": "Scooby",
        "type": "dog",
        "status": "Adopted",
    },
    2: {
        "id": 2,
        "name": "Mittens",
        "type": "cat",
        "status": "Available",
    },
}


@app.get("/pets/search")
def search_pets(type: str = Query(...)):
    return [pet for pet in PETS.values() if pet["type"] == type]


@app.get("/pets/{petId}")
def get_pet(petId: int):
    return PETS[petId]
