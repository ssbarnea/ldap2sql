select region, count(*) from custom.activedirectory 
group by region
order by count(*) desc
