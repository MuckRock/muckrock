import axios from 'axios';
import store from './store';
import { getDataLoading, getDataSuccess, getDataError } from './actions';

/* Get data */

const DASHBOARD_DATA_URL = '/dashboard/data.json';

function encodeData(data) {
    return Object.keys(data).map(function(key) {
        return [key, data[key]].map(encodeURIComponent).join("=");
    }).join("&");
}

export function getData(query) {
    var url = DASHBOARD_DATA_URL + '?' + encodeData(query);
    store.dispatch(getDataLoading());
    return axios.get(url)
        .then(response => {
            store.dispatch(getDataSuccess(response));
            return response;
        })
        .catch(response => {
            store.dispatch(getDataError(response));
            return response;
        });
}
