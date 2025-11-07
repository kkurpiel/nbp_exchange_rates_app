import requests

from utils.json_to_model import json_to_model

class ApiService:
    ##### Konstruktor inicjalizujący połączenie z bazą danych #####
    def __init__(self, url: str):
        self.url = url

    ### Pobieranie listy kursów z API NBP (url, nazwa tabeli (A,B,C), data początkowa, data końcowa) ###
    def get_tables(self, table_letter: str, startDate: str, endDate: str) -> dict:
        url = f"{self.url}/{table_letter}/{startDate}/{endDate}?format=json"
        response = requests.get(url)
        if response.status_code == 404:
            return []
        if response.status_code != 200:
            raise Exception(f"Błąd {response.status_code}: {response.text}")
        return response.json()

    ### Pobieranie listy kursów z API NBP i konwersja do modelu danych ###
    def get_table_models(self, table_letter: str, startDate: str, endDate: str):
        return [json_to_model(data) for data in self.get_tables(table_letter, startDate, endDate)]