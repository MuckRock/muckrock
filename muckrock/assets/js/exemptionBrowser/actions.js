/* actions.js
**
** Exports actions for use by the exemption browser.
*/

export const updateExemptionQuery = (query) => (
    {
        type: 'UPDATE_EXEMPTION_QUERY',
        query: query,
    }
);

export const updateExemptionResults = (results) => (
    {
        type: 'UPDATE_EXEMPTION_RESULTS',
        results: results,
    }
);

export const displayExemptionDetail = (exemption) => (
    {
        type: 'DISPLAY_EXEMPTION_DETAIL',
        exemption: exemption,
    }
);

export const displayExemptionList = () => (
    {
        type: 'DISPLAY_EXEMPTION_LIST',
    }
);

export const displayExemptionForm = () => (
    {
        type: 'DISPLAY_EXEMPTION_FORM',
    }
);
