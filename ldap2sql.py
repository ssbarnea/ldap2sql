#!/usr/bin/python
import inspect
import os
import sys
import urllib
import urllib2
import hashlib
import logging
from sqlalchemy import create_engine

reload(sys)
sys.setdefaultencoding('UTF8')

cmd_folder = os.path.abspath(os.path.join(os.path.split(inspect.getfile(inspect.currentframe()))[0], "contrib"))
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

from activedirectory import ActiveDirectory

jira_stats = """select 'issues' as metric, count(*) as value from jiraissue 
            UNION
            select 'projects', count(*) from project
            UNION
            select 'customfields', count(*) from customfield
            UNION

            select 'workflows', count(distinct name) from os_wfentry

            UNION

            select 'users', count(*) from cwd_user

            UNION
            SELECT 'users_active', count(*)
            FROM cwd_user, cwd_user_attributes
            WHERE cwd_user_attributes.user_id = cwd_user.id 
            AND cwd_user_attributes.attribute_name = 'login.previousLoginMillis';"""


class CustomUpdater(object):
    """The methods both update and insert elements in the table as folows:
        UPDATE table SET some_column='something' WHERE another_column='something else';
        INSER INTO table (some_column) 'something' WHERE NOT EXISTS (SELECT 1 FROM table WHERE another_column='something else')
    """

    def __init__(self, stats_uri=None, activedirectory_uri=None):
        if stats_uri is not None:
            self.engine = create_engine(stats_uri, convert_unicode=True)
        if activedirectory_uri is not None:
            self.ad = ActiveDirectory(activedirectory_uri, paged_size=1000, size_limit=50000)
        self.fields = ['mail', 'title', 'manager', 'distinguishedName', 'postalCode', 'telephoneNumber', 'givenName', 'name', 'facsimileTelephoneNumber',
                       'department', 'company', 'streetAddress', 'sAMAccountType', 'mobile', 'c', 'l', 'st', 'extensionAttribute14',
                       'extensionAttribute15', 'extensionAttribute3', 'sAMAccountName', 'userAccountControl']
        self.sql_names = ['mail', 'title', 'managerdn', 'distinguishedname', 'postalcode', 'phone', 'givenname', 'name', 'fax',
                          'department', 'company', 'streetaddress', 'samaccounttype', 'mobile', 'country', 'locale', 'state', 'vp',
                          'region', 'office', 'username', 'useraccountcontrol']
        self.sql_times = ['created', 'changed']
        self.time_fields = ['whenCreated', 'whenChanged']
        self.exists = None
        self.elem_dict = {}
        self.users = []

    """Updates all the fields in custom.stats"""

    def update_stats(self):
        for row in self.engine.execute(jira_stats):
            self.elem_dict[str(row[0])] = row[1]

        update_query = 'UPDATE custom.stats SET workflows=' + str(self.elem_dict['workflows']) + ', customfields=' + \
                str(self.elem_dict['customfields']) + ', issues=' + str(self.elem_dict['issues']) + ', projects=' + str(self.elem_dict['projects']) + \
                ', users=' + str(self.elem_dict['users']) + ', users_active=' + str(self.elem_dict['users_active']) + ' WHERE date=CURRENT_DATE;'
        insert_query = 'INSERT INTO custom.stats (date, workflows, customfields, issues, projects, users, users_active) ' +\
                'SELECT CURRENT_DATE, ' + str(self.elem_dict['workflows']) + ', ' + str(self.elem_dict['customfields']) +\
                ', ' + str(self.elem_dict['issues']) + ', ' + str(self.elem_dict['projects']) + ', ' + str(self.elem_dict['users']) +\
                ', ' + str(self.elem_dict['users_active']) +\
                ' WHERE NOT EXISTS (SELECT 1 FROM custom.stats WHERE date=CURRENT_DATE);'
        self.engine.execute(update_query)
        self.engine.execute(insert_query)

    """Updates most of the fields in custom.activedirectory 
    
    The method gets all the attributes for each user whose account was modified since the day of the last update
    and parses those attributes to meet the fields in the table"""

    def update_activedirectory(self, full=False):
        if full:
            newf = None
        else:
            newf = "(whenChanged>=" + self.get_max_date_ad() + ")"
        self.users = self.ad.get_users(new_filter=newf, attrlist=self.fields)
        logging.info('Found %s users in AD using filter = %s' % (len(self.users), newf))
        if not self.users:
            raise NotImplemented("WTH")
        for count, user in enumerate(self.users):
            if count % 100 == 0:
                logging.info("%s..." % count)
            #print count, user
            try:
                atr = self.users[user]
            except NotImplementedError as e:
                logging.error("Skipped user %s because %s" % (user, e))
                continue

            update_query = 'UPDATE custom.activedirectory SET counter = counter+1 '
            for i in range(len(self.fields)):
                update_query = self.update_fields(update_query, atr, self.fields[i], self.sql_names[i])
            update_query = self.update_times(update_query, atr)
            if int(atr['userAccountControl']) & 0x02:
                update_query += ', is_active=\'false\''
            else:
                update_query += ', is_active=\'true\''
            update_query += ' WHERE username=\'' + user + '\';'

            insert_query = 'INSERT INTO custom.activedirectory ('
            first = True
            for i in range(len(self.sql_names)):
                try:
                    atr[self.fields[i]]
                    if not first:
                        insert_query += ','
                    insert_query += self.sql_names[i]
                    first = False
                except (IndexError, KeyError):
                    pass
            for i in range(len(self.sql_times)):
                try:
                    atr[self.time_fields[i]]
                    insert_query += ', ' + self.sql_times[i]
                except (IndexError, KeyError):
                    pass
            
            # UPSERT implementation based on http://stackoverflow.com/a/6527838/99834
            
            insert_query += ',is_active) SELECT '
            insert_query = self.insert_fields(insert_query, atr)
            insert_query = self.insert_times(insert_query, atr)
            if int(atr['userAccountControl']) & 0x02:
                insert_query += ',\'false\''
            else:
                insert_query += ',\'true\''
            insert_query += ' WHERE NOT EXISTS (SELECT 1 FROM custom.activedirectory WHERE username= \''\
                    + self.escape_quote(user) + '\');'

            self.engine.execute(update_query)
            self.engine.execute(insert_query)

        # updating managers, LDAP returns DN instead of username for managers
        # we look for all mana

    """Checks the deleted users from ldap by comparing the users from ldap with those from the database"""
    def update_deleted(self):
        sql_user = []
        for row in self.engine.execute("SELECT samaccountname FROM custom.activedirectory WHERE is_deleted = 'false' ORDER BY samaccountname"):
            if row[0]:
                sql_user.append(row[0].encode('utf-8'))
        self.users = self.ad.get_users()
        for i in sql_user:
            if not i in self.users:
                logging.info("User %s was deleted from LDAP" % i)
                self.engine.execute("UPDATE custom.activedirectory SET is_deleted = 'true' where username = '%s'" % i)

    """Creates the url that should exist if the user has a gravatar picture conected with his email. 
    Then it checks if the url exists"""
    def check_gravatar(self):
        return  # TODO: re-enable gravator check
        self.users = self.ad.get_users()
        for count, user in enumerate (self.users):
            atr = self.ad.get_attributes(user = user)
            try:
                email = atr['mail']
                default = 'http://www.gravatar.com/avatar/'
                size = 40
                gravatar_url = "http://www.gravatar.com/avatar/" + hashlib.md5(email.lower()).hexdigest() + "?"
                gravatar_url += urllib.urlencode({'d':default, 's':str(size)})
                try:
                    u = self.find_matches(gravatar_url)
                    if len(u) == 0:
                        has_avatar = 'true'
                    else:
                        has_avatar = 'false'
                except (urllib2.HTTPError, urllib2.URLError):
                    has_avatar = 'false'
            except (IndexError, KeyError, TypeError):
                has_avatar = 'false'
            self.engine.execute('UPDATE custom.activedirectory SET has_gravatar=\'%s\' WHERE username=\'%s\';' % (has_avatar, user))

    def find_matches(self, newu):
        urls = []
        urls.append('http://www.gravatar.com/avatar/64908bc7260a8be06b142d34f83b9781?s=40&d=http%3A%2F%2Fwww.gravatar.com%2Favatar%2F')
        urls.append(newu)
        d = {}
        url_contents = {}
        matches = []
        for url in urls:
            c = urllib2.urlopen(url)
            url_contents[url] = []
            while 1:
                r = c.read(4096)
                if not r: break
                md5 = hashlib.md5(r).hexdigest()
                url_contents[url].append(md5)
                if md5 in d:
                    url2 = d[md5]
                    matches.append((md5, url, url2))
                else:
                    d[md5] = []
                d[md5].append(url)
        return matches

    def update_all(self, full=False):
        """Updates all the fields in all the custom tables"""

        logging.info("Updating changes from AD...")

        self.update_activedirectory(full=full)

        for row in self.engine.execute('SELECT CURRENT_DATE'):
            current_date = str(row[0])
            current_date = current_date[:10]
            break
        for row in self.engine.execute('SELECT MAX(gravatar_check_date) FROM custom.activedirectory;'):
            check_date = str(row[0])
            check_date = check_date[:10]
            break
        if check_date == current_date:
            self.check_gravatar()
        self.update_stats()

        logging.info("Updating deleted accounts...")
        self.update_deleted() # must be before managers!


        logging.info("Updating managers...")
        self.update_managers()


    def update_managers(self):
        """
        This will populate the manager field with the username of the manager, based on the managerdn (the field returned by ldap)

        :return:
        """
        for row in self.engine.execute("""select ad.username, ad.manager as oldmanager, ad2.username as newmanager
  from custom.activedirectory ad
left join custom.activedirectory ad2 on ad.managerdn = ad2.distinguishedname and NOT ad2.is_deleted
where ad.managerdn is not NULL AND ad.manager != ad2.username
--and ad.manager != ad2.username
--limit 100;"""):
            (username, oldmanager, newmanager) = row
            self.engine.execute("UPDATE custom.activedirectory SET manager='%s' where username='%s'" % (newmanager, username))

    def update_fields(self, update_query, atr, varname, sql_name):
        """Updates the update_query string with the fields that don't require special parsing"""
        try:
            atr[varname]
            update_query += ', ' + sql_name + "='" + self.escape_quote(atr[varname]).encode('utf-8') + "'"
        except (IndexError, KeyError):
            pass
        return update_query

    def insert_fields(self, insert_query, atr):
        """Updates the insert_query string with the same fields as the ones above"""
        first = True
        for i in range(len(self.sql_names)):
            try:
                atr[self.fields[i]]
                if not first:
                    insert_query += ','
                insert_query += '\'' + self.escape_quote(atr[self.fields[i]]).encode('utf-8') + '\''
                first = False
            except (IndexError, KeyError):
                pass
        return insert_query

    def update_times(self, update_query, atr):
        """Updates the update_query string with the fields that require special parsing (date variables)"""
        for i in range(len(self.time_fields)):
            try:
                update_query += ', ' + self.sql_times[i] + '=\'' + self.convert_date(atr[self.time_fields[i]]).encode('utf-8') + '\''
            except (IndexError, KeyError):
                pass
        return update_query

    def insert_times(self, insert_query, atr):
        """Same as the above just for insert_query"""
        for i in range(len(self.sql_times)):
            try:
                atr[self.time_fields[i]]
                insert_query += ', \'' + self.convert_date(atr[self.time_fields[i]]).encode('utf-8') + '\''
            except (IndexError, KeyError):
                pass
        return insert_query

    def escape_quote(self, string):
        """Escapes the quotes in a string with double quote:
        someone's string => someone''s string"""
        new_str = string
        count = 0
        for i in range(len(string)):
            if string[i] == '\'':
                new_str = new_str[:count] + '\'' + string[i:]
                count += 1
            count += 1
        return new_str

    def get_max_date_ad(self):
        """Determines the last date at which the table was updated.
        Finds the last date at which an account from the table was updated
        and returns that date"""
        for row in self.engine.execute("SELECT MAX(changed) FROM custom.activedirectory"):
            date = row[0]
            break
        date = (str(date)).split('-')
        if len(date) != 3 or len(date[0]) != 4 or len(date[1]) != 2 or len(date[2]) != 2:
            logging.fatal("Couldn't get maximum date from custom.activedirectory")
            sys.exit(1)
        max_date = date[0] + date[1] + date[2] + "000000.0Z"
        return max_date

    def convert_date(self, string):
        """Converts date from the ldap timestamp to the sql timestamp
        20010101121212.0Z => 2001-01-01 """
        string = string[:8]
        if len(string) != 8:
            return None
        try:
            int(string)
            res = string[:4] + '-' + string[4:6] + '-' + string[6:]
            return res
        except ValueError:
            return None


def main():

    logging_format = "%(asctime).19s %(levelname)8s %(message)s"
    logging.basicConfig(
        level=logging.DEBUG,
        format=logging_format,
        #filename='%s.log' % JIRA_PROJECT,
        #mode="w"
        )
    if 'LDAP2DB_DB_URI' not in os.environ or 'LDAP2DB_AD_URI' not in os.environ:
        logging.fatal("""You need to set configuration using environment variables.
    LDAP2DB_DB_URI='postgresql+pg8000://dbuser:dbpass@db.example.com/dbname'
    LDAP2DB_AD_URI='ldaps://pdc.example.com:3269/dc=example,dc=com'
        """)
        sys.exit(1)
    db_uri = os.environ['LDAP2DB_DB_URI']
    ad_uri = os.environ['LDAP2DB_AD_URI']

    custom = CustomUpdater(
        stats_uri=db_uri,
        activedirectory_uri=ad_uri)

    custom.update_all(full=False)

if __name__ == '__main__':
    main()

