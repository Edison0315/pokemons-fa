import requests
import json

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi_utilities import repeat_at

from contextlib import asynccontextmanager

# utilidad
async def call_api(url: str) -> list:
	response = requests.get(url).json()
	return response

# Cron
@repeat_at(cron="*/15 * * * *") 
async def fill_json_file():
	r: list = await call_api('https://pokeapi.co/api/v2/pokemon/')
	r_filled: list = await get_detail_by_pokemon(r["results"])

	print('******************************')
	print('CRON was executed successfully')
	print('******************************')
	
	file: File = File(r_filled)
	file.create_file_and_write_in()

async def get_detail_by_pokemon(r: list):

	pokemon_full_filled: list = []

	for pok in r:

		detail = await call_api(pok["url"])
		
		pok_filled = {
			"name": pok["name"],
			"url": pok["url"],
			"base_experience": detail["base_experience"],
			"height": detail["height"],
			"weight": detail["weight"]
		}

		pokemon_full_filled.append(pok_filled)
	
	return pokemon_full_filled


# Manejador de eventos del contexto
@asynccontextmanager
async def lifespan(app: FastAPI):
	fill_json_file()
	yield


app = FastAPI(lifespan=lifespan)

file              = open("pokemons.json")
pokemons_db: list = json.load(file)


class File:
	def __init__(self, pokemons) -> None:
		self.pokemons = pokemons

	def create_file_and_write_in(self) -> None:
		f = open("pokemons.json", "w")
		f.write(json.dumps(self.pokemons))


class Pokemon(BaseModel):
	name: str
	url: str
	base_experience: int
	height: int
	weight: int

def search_pokemon(name: str):

	for index, pkm in enumerate(pokemons_db):
		if(pkm["name"] == name):
			#return namedtuple('Pokemon', pokemons_db[index].keys())(*pokemons_db[index].values())
			return pokemons_db[index]
		
@app.get('/pokemon')
async def get_all_pokemons() -> None:
	return pokemons_db

@app.get('/pokemon/{id}')
async def get_pokemon(id: int) -> dict:
	return pokemons_db[id]

@app.post('/pokemon')
async def store_pokemon(pokemon: dict):
	name: str = pokemon["name"]
	pokemon_founded = search_pokemon(name)

	if pokemon_founded is not None:
		if pokemon["name"] == pokemon_founded["name"]:
			return {"error": "Pokemon founded, it cant be addded"}

	
	pokemons_db.append(pokemon)
	return {"ok": "Pokemon added succesfully"}


@app.put('/pokemon/{id}')
async def store_pokemon(pokemon: Pokemon, id: int):

	if id in range(len(pokemons_db)):		
		pokemons_db[id] = pokemon
		return {"ok": "Pokemon updated succesfully"}

	return {"error": "Pokemon cant be updated"}


@app.delete('/pokemon/{id}')
async def delete_pokemon(id: int) -> dict:
	pokemons_db.pop(id)
	return {"message": "pokemon deleted successfully"}


