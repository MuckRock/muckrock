
# Sign up for a DocumentCloud account at https://www.documentcloud.org
# DocumentCloud is used to host and embed PDF documents
export DOCUMENTCLOUD_USERNAME=""
export DOCUMENTCLOUD_PASSWORD=""

# Sign up for a Stripe account at https://stripe.com
# Stripe is used for payment processing
export STRIPE_SECRET_KEY=""
export STRIPE_PUB_KEY=""

# Sign up for a mailgun account at https://www.mailgun.org
# Mailgun is used for sending and receiving email
export MAILGUN_ACCESS_KEY=""

# Sign up for an AWS account at https://aws.amazon.com
# AWS is used for the S3 service in order to store uploaded files
export AWS_ACCESS_KEY_ID=""
export AWS_SECRET_ACCESS_KEY=""

# Sign up for a Phaxio account at https://www.phaxio.com
# Phaxio is used for sending faxes
export PHAXIO_KEY=""
export PHAXIO_SECRET=""
export PHAXIO_CALLBACK_TOKEN=""

# Set any random string for the secret key - this is required for Django
source /home/vagrant/muckrock/.secret_key.sh
