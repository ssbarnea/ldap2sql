select substr(office,0,5), count(*) from custom.activedirectory
where office is not NULL
group by office order by count(*) desc
