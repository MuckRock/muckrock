/* actions.js
**
** Exports actions for use by the exemption browser.
*/

export const updateExemptionQuery = (query) => (
    {
        type: 'UPDATE_EXEMPTION_QUERY',
        data: {
            query: query,
        }
    }
);

export const updateExemptionResults = (results) => (
    {
        type: 'UPDATE_EXEMPTION_RESULTS',
        data: results,
    }
);
