import json
from os import path
import sqlite3

def createNewJsonFile():
    with open('/Users/bic/Desktop/work/python_server/modifiedOcurrences.json', 'w') as outfile:
        outfile.write("[]")
        outfile.close()

def addModifiedRecordsToJsonFile(ocurrencePath, entityName, operation, modifiedType):
    currentOcurrences = []
    with open('/Users/bic/Desktop/work/python_server/modifiedOcurrences.json') as outfile:
        currentOcurrences = json.load(outfile)
        currentOcurrences.append({
            "ocurrencePath" : ocurrencePath,
            "entityName" : entityName,
            "matchType" : operation,
            "modifiedType" : modifiedType
        })
        outfile.close()
    with open('/Users/bic/Desktop/work/python_server/modifiedOcurrences.json', "w") as json_file:
        json.dump(currentOcurrences, json_file, indent=4, separators=(',',': '))
        json_file.close()
    print(ocurrencePath + " sucessfully added to json")

def updateDabases():
    conn = sqlite3.connect("test.db")
    c = conn.cursor()
    c.execute("SELECT FILE_PATH FROM MODIFIED_OCURRENCES")

    databaseField = {"FilePath" : 0, "EntityName" : 1, "Operation" : 2, "Line" : 3}

    file_names = []
    for it in c.fetchall():
        file_names.extend(it)
    file_names = tuple(set(file_names))

    # checking which entries have been deleted and adding them to the json
    # for file_path_it in file_names:
    #     c.execute(
    #         ''' SELECT * FROM AFFECTED_FILES WHERE FILE_PATH='{path}' AND NOT EXISTS (
    #                 SELECT 1 FROM MODIFIED_OCURRENCES WHERE MODIFIED_OCURRENCES.FILE_PATH = AFFECTED_FILES.FILE_PATH 
    #                                                     AND MODIFIED_OCURRENCES.ENTITY_NAME = AFFECTED_FILES.ENTITY_NAME 
    #                                                     AND MODIFIED_OCURRENCES.OPERATION = AFFECTED_FILES.OPERATION); '''.format(path = file_path_it))
    #     # adding entries to jsonFile
    #     for it in c.fetchall():
    #         occurencePath = it[databaseField["FilePath"]] + ":" + it[databaseField["Line"]]
    #         addModifiedRecordsToJsonFile(occurencePath, it[databaseField["EntityName"]], it[databaseField["Operation"]], "Deleted")

    # delete entries from AFFECTED_FILES which have been removed
    for file_path_it in file_names:
        c.execute(
            ''' DELETE FROM AFFECTED_FILES WHERE FILE_PATH='{path}' AND NOT EXISTS (
                    SELECT 1 FROM MODIFIED_OCURRENCES WHERE MODIFIED_OCURRENCES.FILE_PATH = AFFECTED_FILES.FILE_PATH 
                                                        AND MODIFIED_OCURRENCES.ENTITY_NAME = AFFECTED_FILES.ENTITY_NAME 
                                                        AND MODIFIED_OCURRENCES.OPERATION = AFFECTED_FILES.OPERATION); '''.format(path = file_path_it))
        conn.commit()

    # adding new entries to the json and the AFFECTED_FILES database
    for file_path_it in file_names:
        c.execute(
        ''' SELECT * FROM MODIFIED_OCURRENCES WHERE FILE_PATH='{path}' AND NOT EXISTS (
                SELECT 1 FROM AFFECTED_FILES WHERE MODIFIED_OCURRENCES.FILE_PATH = AFFECTED_FILES.FILE_PATH 
                                                    AND MODIFIED_OCURRENCES.ENTITY_NAME = AFFECTED_FILES.ENTITY_NAME 
                                                    AND MODIFIED_OCURRENCES.OPERATION = AFFECTED_FILES.OPERATION); '''.format(path = file_path_it))
        # adding entries to jsonFile
        for it in c.fetchall():
            occurencePath = it[databaseField["FilePath"]] + ":" + it[databaseField["Line"]]
            addModifiedRecordsToJsonFile(occurencePath, it[databaseField["EntityName"]], it[databaseField["Operation"]], "Added")
            c.execute("INSERT INTO AFFECTED_FILES (FILE_PATH, ENTITY_NAME, OPERATION, LINE) values (?, ?, ?, ?)",(it[databaseField["FilePath"]], it[databaseField["EntityName"]], it[databaseField["Operation"]], it[databaseField["Line"]]))
            conn.commit()

def update():
    createNewJsonFile()
    updateDabases()