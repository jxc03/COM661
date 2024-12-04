import jsonData from '../assets/data/foodPlaces.json'

/*
export class DataService {

    getBusinesses(page: number) {

        return jsonData;
    }
}
*/



export class DataService {
    pageSize: number = 2;
    private data: any[] = jsonData as any[];
/*
    getBusinesses(page: number) {
        let pageStart = (page - 1) * this.pageSize;
        let pageEnd = pageStart + this.pageSize;
        return this.data.slice(pageStart, pageEnd);
    }
 
    getLastPageNumber() {
        return Math.ceil(this.data.length / this.pageSize); 
    }
*/

    getBusinesses(page: number) {
        const data: any[] = jsonData as any[];
        let pageStart = (page - 1) * this.pageSize;
        let pageEnd = pageStart + this.pageSize;
        return data.slice(pageStart, pageEnd);
    }
 
    getLastPageNumber() {
        const data: any[] = jsonData as any[];
        return Math.ceil(data.length / this.pageSize);
    }
}
 