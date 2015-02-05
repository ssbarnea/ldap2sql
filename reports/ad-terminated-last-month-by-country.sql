select country,  count(*)
  from custom.activedirectory where is_deleted = 't' and 
  is_active = 'f' and
changed is not null 
and givenname is not null
and country is not null
and changed > 
CURRENT_DATE - INTERVAL '1 months'
group by country
order by count(*) desc

