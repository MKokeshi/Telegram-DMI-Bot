# -*- coding: utf-8 -*-

import json
import sqlite3
import re

def esami_output(item):

	output = "*Insegnamento:* " + item["insegnamento"]
	output += "\n*Docenti:* " + item["docenti"]

	for session in ("prima", "seconda", "terza", "straordinaria"):
		if session in item.keys():
			appeals = item[session]
			appeals = str(appeals)			
			appeals = re.sub(r"(?P<ora>([01]?\d|2[0-3]):[0-5][0-9])(?P<parola>\w)", r"\g<ora> - \g<parola>", appeals) #aggiunge un - per separare orario e luogo dell'esame
			appeals = appeals.split("', '") #separa i vari appelli della sessione
			for i, appeal in enumerate(appeals):
				appeals[i] = re.sub(r"[\['\]]", "", appeal) #rimuove eventuali caratteri [ ' ] rimasti in ogni appello
				appeals[i] = re.sub(r"(?P<link>https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*))", r"[link](\g<link>)", appeals[i]) #cattura eventuali link e li rende inoffensivi per il markdown
				appeals[i] = re.sub(r"_(?![^(]*[)])", " ", appeals[i]) #rimuove eventuali caratteri _ rimasti che non siano nei link
			if "".join(appeals) != "":
				output += "\n*" + session.title() + ":*\n" + "\n".join(appeals)

	output += "\n*CDL:* " + item["cdl"]
	output += "\n*Anno:* " + item["anno"] + "\n"

	return output

def check_output(output):
	if len(output):
		output_str = '\n'.join(output)
		output_str += "\nRisultati trovati: " + str(len(output))
	else:
		output_str = "Nessun risultato trovato :(\n"

	return output_str

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def esami_cmd(userDict):
	output_str = []
 	
	select_sessione = ", ".join([key for key in userDict.keys() if "sessione" in key]).replace("sessione", "") #stringa contenente le sessioni per cui il dict contiene la key, separate da ", " 	
	where_sessione = " = '[]' and not ".join([key for key in userDict.keys() if "sessione" in key]).replace("sessione", "") #stringa contenente le sessioni per cui il dict contiene la key, separate da " = '[]' and not " 
	where_anno = "' or anno = '".join([key for key in userDict.keys() if "anno" in key]) #stringa contenente gli anni per cui il dict contiene la key, separate da "' or anno = '"	
	where_insegnamento = userDict.get("insegnamento", "")  #stringa contenente l'insegnamento, se presente

	query = """SELECT anno, cdl, docenti, insegnamento{} 
			   FROM exams
			   WHERE 1 = 1 {} {} {}""".format(
	", " + select_sessione if select_sessione else ", prima, seconda, terza, straordinaria", #es.=> , prima, seconda, terza
	"and not " + where_sessione + " = '[]'" if where_sessione else "", #es.=> and not prima = '[] and not terza = '[]' 
	"and (anno = '" + where_anno + "')" if where_anno else "", #es.=>  and (anno = '1° anno' or anno = '3° anno)'
	"and insegnamento LIKE '%" + where_insegnamento + "%'" if where_insegnamento else "" #es.=> and insegnamento LIKE '%stringa%'
	)

	conn = sqlite3.connect('data/DMI_DB.db')
	conn.row_factory = dict_factory
	cur = conn.cursor()
	try:
		cur.execute(query)
	except:
		print("The following exams query could not be executed (command \\esami)")
		print(query) #per controllare cosa è andato storto

	for item in cur.fetchall():
		output_str.append(esami_output(item))

	return check_output(output_str)