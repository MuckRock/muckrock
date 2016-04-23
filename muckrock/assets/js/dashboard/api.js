import axios from 'axios';
import store from './store';
import { getDataSuccess } from './actions';

/* Get data */

const DASHBOARD_DATA_URL = 'http://localhost:8000/dashboard/data.json';

export function getData() {
    return axios.get(DASHBOARD_DATA_URL)
        .then(response => {
            store.dispatch(getDataSuccess(response.data));
            return response;
        });
}
