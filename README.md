# ldap2sql
Syncronize Active Directory (LDAP) users to a SQL database

This script will query an Active Directory server and will save all accounts inside a PostgreSQL table.

Also it has some neat features like:
* accounts removed or disabled from LDAP are not removed from the database and are only marked as deleted.
* account status is saved as friendly field
* manager is also saved
* it does mark if an account have a gravatar or not

What you can use this for:
* Find how many people joined or left the company
* Find details of old account even after these accounts are removed
* Get cool stats by grouping the data
* Implement an organigram without having to work with the ugly LDAP API.
