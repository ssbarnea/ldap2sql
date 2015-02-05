select vp, count(vp) from custom.activedirectory 
group by vp
order by count(*) desc
