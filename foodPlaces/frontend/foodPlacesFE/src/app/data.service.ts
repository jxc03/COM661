import jsonData from '../assets/data/foodPlaces.json'

export class DataService {
    getBusinesses() {
        return jsonData;
    }
}