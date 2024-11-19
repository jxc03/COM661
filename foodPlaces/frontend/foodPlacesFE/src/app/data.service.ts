import jsonData from '../assets/data/foodPlacesDB.foodPlaces.json'

export class DataService {
    getPlaces() {
        return jsonData;
    }
}