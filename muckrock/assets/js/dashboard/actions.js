export function getDataLoading() {
    return {type: 'GET_DATA_LOADING'};
}

export function getDataSuccess(response) {
    return {
        type: 'GET_DATA_SUCCESS',
        response
    };
}

export function getDataError(error) {
    return {
        type: 'GET_DATA_ERROR',
        error
    };
}
