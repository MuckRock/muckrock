#!/usr/bin/env python
# This will create your initial .env files
# These are not to be checked in to git, as you may populate them
# with confidential information

# Standard Library
import os
import random
import string


COMPOSE_ENV_PATH = ".envs/.local/.compose"

def random_string(n=5):
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))

def write_env_file(filepath, env_vars):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        for k, v in env_vars.items():
            f.write(f"{k}={v}\n")

def generate_and_save_compose_project_name():
    project_name = os.path.basename(os.getcwd()).lower() + "_" + random_string(5)
    write_env_file(COMPOSE_ENV_PATH, {"COMPOSE_PROJECT_NAME": project_name})
    print(f"Generated and saved COMPOSE_PROJECT_NAME={project_name} in {COMPOSE_ENV_PATH}")
    return project_name


PGUSER = random_string(30)
PGPASSWORD = random_string(60)

CONFIG = [
    {
        "name": ".django",
        "sections": [
            {
                "name": "General",
                "envvars": [
                    ("USE_DOCKER", "yes"),
                    ("SECRET_KEY", lambda: random_string(20)),
                    ("IPYTHONDIR", "/app/.ipython"),
                    ("REQUESTS_CA_BUNDLE", "/etc/ssl/certs/ca-certificates.crt"),
                ],
            },
            {
                "name": "Redis",
                "envvars": [("REDIS_URL", "redis://muckrock_redis:6379/0")],
            },
            {
                "name": "Squarelet",
                "url": "https://github.com/muckrock/squarelet/",
                "description": "Squarelet is the user account service for MuckRock - it's "
                "development environment should be installed in parallel to MuckRock",
                "envvars": [("SQUARELET_KEY", ""), ("SQUARELET_SECRET", "")],
            },
            {"name": "JWT", "envvars": [("JWT_VERIFYING_KEY", "")]},
            {
                "name": "DocumentCloud",
                "url": "https://www.documentcloud.org",
                "description": "DocumentCloud is used to host and embed PDF documents",
                "envvars": [
                    ("DOCUMENTCLOUD_USERNAME", ""),
                    ("DOCUMENTCLOUD_PASSWORD", ""),
                ],
            },
            {
                "name": "Stripe",
                "url": "https://stripe.com",
                "description": "Stripe is used for payment processing",
                "envvars": [
                    ("STRIPE_SECRET_KEY", ""),
                    ("STRIPE_PUB_KEY", ""),
                    ("STRIPE_WEBHOOK_SECRET", ""),
                ],
            },
            {
                "name": "Mailgun",
                "url": "https://www.mailgun.com",
                "description": "Mailgun is used for sending and receiving email",
                "envvars": [("MAILGUN_ACCESS_KEY", ""), ("MAILGUN_SERVER_NAME", "")],
            },
            {
                "name": "AWS",
                "url": "https://aws.amazon.com",
                "description": "AWS is used for to store files in the S3 service",
                "envvars": [("AWS_ACCESS_KEY_ID", ""), ("AWS_SECRET_ACCESS_KEY", "")],
            },
            {
                "name": "Phaxio",
                "url": "https://www.phaxio.com",
                "description": "Phaxio is used for sending faxes",
                "envvars": [
                    ("PHAXIO_KEY", ""),
                    ("PHAXIO_SECRET", ""),
                    ("PHAXIO_CALLBACK_TOKEN", ""),
                ],
            },
            {
                "name": "Zoho Desk",
                "url": "https://www.zoho.com",
                "description": "We use Zoho desk for help ticket management",
                "envvars": [("ZOHO_TOKEN", "")],
            },
            {
                "name": "Lob",
                "url": "https://lob.com",
                "description": "Lob is used for sending snail mail",
                "envvars": [
                    ("LOB_SECRET_KEY", ""),
                    ("LOB_WEBHOOK_KEY", ""),
                    ("LOB_BANK_ACCOUNT_ID", ""),
                ],
            },
            {
                "name": "Plaid",
                "url": "https://plaid.com",
                "description": "Plaid is used for checking our bank account",
                "envvars": [
                    ("PLAID_CLIENT_ID", ""),
                    ("PLAID_SECRET", ""),
                    ("PLAID_PUBLIC_KEY", ""),
                    ("PLAID_ENV", ""),
                    ("PLAID_ACCESS_TOKEN", ""),
                ],
            },
            {
                "name": "OPENAI_API_KEY", 
                "url": "https://openai.com/",
                "description": "We use OpenAI to automate some support tasks",
                "envvars": [("OPENAI_API_KEY", "")]
            },
        ],
    },
    {
        "name": ".postgres",
        "sections": [
            {
                "name": "PostgreSQL",
                "description": "POSTGRES values are used by Django, PG values are used for importing DB from Heroku - only uncomment them if needed",
                "envvars": [
                    ("POSTGRES_HOST", "muckrock_postgres"),
                    ("POSTGRES_PORT", "5432"),
                    ("POSTGRES_DB", "muckrock"),
                    ("POSTGRES_USER", PGUSER),
                    ("POSTGRES_PASSWORD", PGPASSWORD),
                    ("#PGHOST", "muckrock_postgres"),
                    ("#PGUSER", PGUSER),
                    ("#PGPASSWORD", PGPASSWORD),
                    ("#PGSSLMODE", "allow"),
                ],
            }
        ],
    },
]


def main():
    print("Initializing the dot env environment for MuckRock development")
    os.makedirs(".envs/.local/", 0o775)
    print("Created the directories")
    for file_config in CONFIG:
        with open(".envs/.local/{}".format(file_config["name"]), "w") as file_:
            for section in file_config["sections"]:
                for key in ["name", "url", "description"]:
                    if key in section:
                        file_.write("# {}\n".format(section[key]))
                file_.write("# {}\n".format("-" * 78))
                for var, value in section["envvars"]:
                    file_.write(
                        "{}={}\n".format(var, value() if callable(value) else value)
                    )
                file_.write("\n")
        print("Created file .envs/.local/{}".format(file_config["name"]))
    generate_and_save_compose_project_name()
    print("Initialization Complete")


if __name__ == "__main__":
    main()
