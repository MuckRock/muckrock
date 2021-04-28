# Changelog
All notable changes to the Washington Post fork of Muckrock will be noted here

## [Unreleased]

## [1.0.0] - 2020-04-28
### Changed
	- Revised deployment and docker configuration in /compose to work in ECS
		- Created separate dockerfiles for each service
		- Revised entrypoint commands so celery and django commands get pid 1 and can react to ECS SIGTERM signals
	- Added healthchecks to all docker containers
	- Updated fine uploader library to take advantage of v4 signatures
	- Split off user uploads into private s3 bucket
	- Refactored AWS tokens to instead use IAM roles inside of ECS task
	- Updated to use boto3 library
	- Added washington post specific django settings at `muckrock/settings/wapo/`
	- Add better stacktrace logging to celery for inspectibility
	- Add management commands in `/wapo-management` to handle incoming fixture data from Muckrock
	- Added django-watchman for configurable healthchecks

