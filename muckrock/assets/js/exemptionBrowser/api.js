/* api.js
**
** Configures and exports an Axios instance for accessing the API.
*/

import axios from 'axios';

const api = axios.create({
    baseURL: '/api_v1/',
    xsrfCookieName: 'csrftoken',
    xsrfHeaderName: 'X-CSRFToken'
});

export default api;
