# Developing Muckrock at the Washington Post

## Seeding a local database
We have a forked version of the [Muckrock](https://github.com/MuckRock/muckrock) codebase and have made some changes to suit our needs. Since we didn't want a full database dump of the organization's data, we have a subset of agencies and jurisdictions that enable us to file FOIA requests. The fixture contains data from these django models:

```python
[
  "business_days.holiday",                                                                                                                                                                                                                                                     
  "jurisdiction.jurisdiction",                                                                                                                                                                                                                                                  
  "jurisdiction.law",                                                                                                                                                                                                                                                           
  "jurisdiction.lawyear",                                                                                                                                                                                                                                                       
  "communication.emailaddress",                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              
  "communication.address",                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         
  "communication.phonenumber",                                                                                                                                                                                                                                                  
  "portal.portal",                                                                                                                                                                                                                                                              
  "agency.agencytype",                                                                                                                                                                                                                                                           
  "agency.agency",                                                                                                                                                                                                                                                              
  "agency.agencyaddress",                                                                                                                                                                                                                                                       
  "agency.agencyphone",                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       
  "agency.agencyemail",
 ]
 ```

Locally, you'll want to load data from these fixtures into a postgres instance running inside of docker on your machine. To do this, follow these steps:

1. Make sure that you have [invoke](https://pypi.org/project/invoke/) installed: `pip install invoke`
2. Download the bzip2 file here: `s3://wp-muckrock-uploads-dev/fixtures/agency_jurisdiction.json.bz2` and move it inside the `wapo-management/` directory.
3. If you haven't already run `python initialize_dotenvs.py` as stated in the root README, then do so. Ensure that your `.envs/.local/.postgres` so that you are using the local postgres container for your app. If you are unsure then make sure that this value is set: `POSTGRES_HOST=muckrock_postgres`
4. `inv manage "loaddata -v3 wapo-management/agency_jurisdiction.json.bz2"`

Grab a :coffee:, this will take ~5 minutes to complete. 

Once complete, you should be able to run `docker-compose up -f local.yml` and visit http://dev.muckrock.com/agency/ and see a list of agencies!

##  Maintenance
In the future we may receive more data from the Muckrock team, there are a few other scripts in this directory which were used to clean the data in the `agency_jurisdiction` fixture, that may be useful in the future. 

There are cases in which fixtures will have foreign key relations to data that doesn't exist in our database. for that case run:
`./wapo-management/null-fixtures.sh`

There are occasions to load multiple fixtures into a remote database, which is far slower than the local process. It is better to chunk the fixtures up in that case, in case the DB connection times out, or the sql COPY statement gets too large. Make sure to swap in the appropriate model name in the file and run:
`./wapo-management/split_models.py` 

Then run:
`./wapo-management/load-fixtures.sh` to import the chunked fixtures into the django ORM.
