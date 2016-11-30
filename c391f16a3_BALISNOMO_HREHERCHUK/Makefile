all: A3.db
	echo Made all
A3.db: dbMake.txt
	sqlite3 A3.db < dbMake.txt

QFiles = q0.txt q1.txt q2.txt q3.txt q4.txt q5.txt q6.txt q7.txt q8.py q9.py sparqlparser.py rdfparser.py
Other = Makefile README A3.db dbMake.txt

clean:
	rm -f A3.db