import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import dbmanager

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

class Machine(BaseModel):
    ip: str
    name: str
    shared_folder: str

@app.post("/machine")
async def add_item(machine: Machine):
    dbmanager.add_machine_record(machine.name, machine.ip, machine.shared_folder)
    return machine

@app.get("/machines")
async def get_machines():
    return dbmanager.get_machines()

@app.delete("/machine/{id}")
async def delete_machine(id: int):
    dbmanager.delete_row_from_table(id, "machine")
    return f"machine {id} was deleted successfully"

@app.put("/machine/{id}")
async def update_machine(id: int, machine: Machine):
    dbmanager.update_machine_record(id, machine.name, machine.ip, machine.shared_folder)
    return f"machine {id} was updated successfully"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)