/* api.js
**
** Configures and exports an Axios instance for accessing the API.
*/

import axios from 'axios';

/* eslint-disable no-undef */
let rootDomain = 'http://localhost:8000';
if (process.env.NODE_ENV == 'staging') {
    rootDomain = 'http://muckrock-staging.herokuapp.com';
} else if (process.env.NODE_ENV == 'production') {
    rootDomain = 'https://www.muckrock.com';
}
/* eslint-enable no-undef */

const api = axios.create({
    baseURL: rootDomain + '/api_v1/',
    xsrfCookieName: 'csrftoken',
    xsrfHeaderName: 'X-CSRFToken'
});

export { api as default, rootDomain };
