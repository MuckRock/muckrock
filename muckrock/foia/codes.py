"""Status codes for autoimporting documents"""

# pylint: disable=line-too-long
# pylint: disable=bad-continuation

CODES = {
	'ACK': ('Acknowledgement Letter', 'processed', 'An acknowledgement letter, stating the request is being processed.'),
	'NRD': ('No Responsive Documents', 'no_docs', 'A no responsive documents response.'),
	'NRD-T': ('No Responsive Documents', 'no_docs', 'Potentially responsive documents were transferred to another department.'),
	'RES-C': ('Cover Letter', 'done', 'A cover letter granting the request and outlining any exempted materials, if any.'),
	'RES-P': ('Partial Responsive Documents', 'partial', 'A first set of responsive documents from the agency, with more to be sent at a specified date.'),
	'RES': ('Responsive Documents', 'done', 'A copy of documents responsive to the request.'),
	'FEE-R': ('Fee Waiver Rejected', None, 'A letter stating the request for reduced or waived fees has been rejected.'),
	'FEE-A': ('Fee Waiver Accepted', 'processed', 'A letter stating the request for reduced or waived fees has been accepted.'),
	'FEE': ('Payment Required', 'payment', 'A letter stating the requester must agree to or prepay assessed or estimated fees in order for the agency to continue processing the request.'),
	'REJ-V': ('Request Rejected', 'rejected', 'The request has been rejected as being too vague, burdensome or otherwise unprocessable.'),
	'REJ-G': ('Glomar Response', 'rejected', 'The request has been rejected, with the agency stating that it can neither confirm nor deny the existence of the requested documents.'),
	'REJ-E': ('Materials exempt from disclosure', 'rejected', 'The request has been rejected, with the agency stating that the information or document(s) requested are exempt from disclosure.'),
	'REJ-P': ('Rejected, proxy required', 'rejected', 'The request has been rejected with the agency stating that you must be a resident of the state. MuckRock is working with our in-state volunteers to refile this request, and it should appear in your account within a few days.'),
	'REJ': ('Request rejected', 'rejected', 'The request has been rejected by the agency.'),
	'FIX-D': ('Fix Required', 'fix', 'A fix is required to perfect the request. The agency has asked the requester to specify a date range for the requested materials.'),
	'FIX-F': ('Fee Agreement Required', 'fix', 'The user must agree to pay fees in order for the process to be continued being processed.  No payment is due at this time.'),
	'FIX-V': ('Fix Required', 'fix', 'A fix is required to perfect the request. The request has been rejected as being too vague, burdensome or otherwise unprocessable.'),
	'FIX-I': ('Fix Required', 'fix', 'A letter stating that a certificate of identity, proof of death, or other privacy-related fix is required in order to continue processing the request.'),
	'FIX': ('Fix Required', 'fix', 'A fix is required to perfect the request.'),
	'FWD': ('Request Forwarded', None, 'The request has been forwarded from one agency to another agency or department for further review or follow up.'),
	'INT': ('Interim Response', 'processed', 'An interim response, stating the request is being processed.'),
	'INT-D': ('Interim Response', 'processed', 'An interim response, stating the request has been delayed'),
	'APP-ACK': ('Appeal Acknowledgement', 'appealing', 'A letter stating that the request appeal has been received and is being processed.'),
	'APP-R': ('Appeal Rejected', 'rejected', 'A letter stating that the request appeal has been rejected.'),
	'APP-A': ('Appeal Succesful', 'processed', 'A letter stating that the request appeal has been succesful.'),
	'APP-W': ('Appeal Withdrawn', 'abandoned', 'An acknowledgment that the requester has withdrawn an appeal.'),
}
